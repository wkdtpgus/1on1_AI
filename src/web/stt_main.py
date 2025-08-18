from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging

# 프로젝트 모듈 임포트
from src.config.config import (
    ASSEMBLYAI_API_KEY,
    GOOGLE_CLOUD_PROJECT, 
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_APPLICATION_CREDENTIALS_JSON
)
import os
import json
import tempfile
from datetime import datetime
from pathlib import Path
from fastapi.responses import JSONResponse

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stt_main")

# 서비스 인스턴스
audio_processor = None
meeting_analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global audio_processor, meeting_analyzer
    
    # Google 자격증명 설정
    if GOOGLE_APPLICATION_CREDENTIALS_JSON:
        creds_path = "/tmp/gcp_creds.json"
        with open(creds_path, "w", encoding="utf-8") as f:
            f.write(GOOGLE_APPLICATION_CREDENTIALS_JSON)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
    
    # 서비스 초기화 (각 클래스가 자체 검증 수행)
    from src.utils.formatter import STTProcessor
    from src.models.analysis import GeminiMeetingAnalyzer
    
    audio_processor = STTProcessor(api_key=ASSEMBLYAI_API_KEY)
    meeting_analyzer = GeminiMeetingAnalyzer(
        google_project=GOOGLE_CLOUD_PROJECT, 
        google_location=GOOGLE_CLOUD_LOCATION
    )
    logger.info("모든 서비스 초기화 완료")
    
    yield
    # 종료시 정리 (필요시)
    pass

# FastAPI 앱 생성
app = FastAPI(
    title="1on1 Meeting AI Analysis", 
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """메인 페이지"""
    from fastapi.responses import FileResponse
    return FileResponse("frontend/index.html")

@app.get("/api.js")
async def api_js():
    """API JavaScript 파일"""
    from fastapi.responses import FileResponse
    return FileResponse("frontend/api.js", media_type="application/javascript")

@app.get("/app.js")
async def app_js():
    """앱 JavaScript 파일"""
    from fastapi.responses import FileResponse
    return FileResponse("frontend/app.js", media_type="application/javascript")

@app.get("/favicon.ico")
async def favicon():
    """파비콘"""
    from fastapi.responses import FileResponse
    return FileResponse("frontend/favicon.ico", media_type="image/x-icon")

@app.post("/api/analyze")
async def analyze_meeting(
    audio_file: UploadFile = File(...),
    qa_data: Optional[str] = Form(default=None),
    participants_info: Optional[str] = Form(default=None)
):
    """1on1 미팅 분석 API"""
    if not audio_processor or not meeting_analyzer:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다")
    
    try:
        # 파일 검증 및 처리
        content = await audio_file.read()
        
        # 오디오 파일 형식 검증
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
        file_ext = Path(audio_file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다")
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        # 음성 전사 처리
        transcript_result = audio_processor.transcribe_audio(temp_audio_path, expected_speakers=2)
        if not transcript_result or 'transcript' not in transcript_result:
            raise HTTPException(status_code=500, detail="STT 처리에 실패했습니다")
        
        transcript = transcript_result['transcript']
        speaker_stats = transcript_result.get('speaker_stats', {})
        
        # JSON 입력 파싱
        qa_list = json.loads(qa_data) if qa_data else None
        participants = json.loads(participants_info) if participants_info else None
        
        # LLM 분석 수행
        analysis_result = meeting_analyzer.analyze_1on1_meeting(
            transcript=transcript,
            speaker_stats=speaker_stats,
            qa_pairs=qa_list,
            participants=participants
        )
        
        try:
            analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError:
            analysis_data = {"error": "분석 결과 파싱 실패", "raw_result": analysis_result}
        
        # transcript 추가
        if isinstance(analysis_data, dict):
            analysis_data["transcript"] = transcript
        
        # 성공 응답 생성
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            **analysis_data,
            "file_info": {
                "filename": audio_file.filename,
                "size": len(content),
                "format": file_ext
            }
        }
        return JSONResponse(content=response)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 처리 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)