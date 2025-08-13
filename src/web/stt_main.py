from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
import logging

# 프로젝트 모듈 임포트  
from src.models.audio_processing import AudioProcessor
from src.models.llm_analysis import GeminiMeetingAnalyzer
from src.config.stt_config import (
    ASSEMBLYAI_API_KEY,
    GOOGLE_CLOUD_PROJECT, 
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_APPLICATION_CREDENTIALS_JSON
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 변수
audio_processor = None
meeting_analyzer = None

# FastAPI 앱 생성
app = FastAPI(title="1on1 Meeting AI Analysis", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """앱 시작시 초기화"""
    global audio_processor, meeting_analyzer
    
    try:
        # Google 자격증명 설정
        if GOOGLE_APPLICATION_CREDENTIALS_JSON:
            creds_path = "/tmp/gcp_creds.json"
            with open(creds_path, "w", encoding="utf-8") as f:
                f.write(GOOGLE_APPLICATION_CREDENTIALS_JSON)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        
        # 모델 초기화
        audio_processor = AudioProcessor(assemblyai_api_key=ASSEMBLYAI_API_KEY)
        meeting_analyzer = GeminiMeetingAnalyzer(google_project=GOOGLE_CLOUD_PROJECT, google_location=GOOGLE_CLOUD_LOCATION)
        
        logger.info("모든 모듈 초기화 완료")
        
    except Exception as e:
        logger.error(f"초기화 오류: {str(e)}")

@app.post("/api/analyze")
async def analyze_meeting(
    audio_file: UploadFile = File(...),
    qa_data: Optional[str] = Form(default=None),
    participants_info: Optional[str] = Form(default=None)
):
    """1on1 미팅 분석"""
    if not audio_processor or not meeting_analyzer:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다")
    
    temp_audio_path = None
    try:
        # 파일 확장자 검증
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
        file_ext = Path(audio_file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다")
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_audio_path = temp_file.name
            content = await audio_file.read()
            temp_file.write(content)
        
        # STT 처리
        transcript_result = audio_processor.transcribe_existing_file(temp_audio_path, expected_speakers=2)
        if not transcript_result or 'transcript' not in transcript_result:
            raise HTTPException(status_code=500, detail="STT 처리에 실패했습니다")
        
        transcript = transcript_result['transcript']
        speaker_stats = transcript_result.get('speaker_stats', {})
        
        # Q&A 데이터 처리
        qa_list = None
        if qa_data:
            try:
                qa_list = json.loads(qa_data)
            except json.JSONDecodeError:
                qa_list = None
        
        # 참석자 정보 처리
        participants = None
        if participants_info:
            try:
                participants = json.loads(participants_info)
            except json.JSONDecodeError:
                participants = None
        
        # LLM 분석
        analysis_result = meeting_analyzer.analyze_1on1_meeting(
            transcript=transcript,
            speaker_stats=speaker_stats,
            qa_pairs=qa_list,
            participants=participants
        )
        
        # JSON 파싱
        try:
            analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError as e:
            analysis_data = {"error": "분석 결과 파싱 실패", "raw_result": analysis_result}
        
        # transcript 추가
        if isinstance(analysis_data, dict):
            analysis_data["transcript"] = transcript
        
        # 최종 응답
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
    
    finally:
        # 임시 파일 정리
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except Exception as e:
                logger.warning(f"임시 파일 삭제 실패: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)