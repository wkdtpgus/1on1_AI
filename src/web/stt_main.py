from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging

# 프로젝트 모듈 임포트
from src.config.stt_config import (
    ASSEMBLYAI_API_KEY,
    GOOGLE_CLOUD_PROJECT, 
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_APPLICATION_CREDENTIALS_JSON
)
from src.utils.api_utils import (
    initialize_services,
    get_audio_processor,
    get_meeting_analyzer,
    validate_services,
    validate_audio_file,
    create_temp_file,
    process_audio_transcription,
    parse_json_input,
    perform_meeting_analysis,
    create_success_response,
    cleanup_temp_file
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stt_main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작시 초기화
    await initialize_services(
        ASSEMBLYAI_API_KEY,
        GOOGLE_CLOUD_PROJECT,
        GOOGLE_CLOUD_LOCATION, 
        GOOGLE_APPLICATION_CREDENTIALS_JSON
    )
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
    audio_processor = get_audio_processor()
    meeting_analyzer = get_meeting_analyzer()
    validate_services(audio_processor, meeting_analyzer)
    
    temp_audio_path = None
    try:
        # 파일 검증 및 처리
        content = await audio_file.read()
        file_ext = validate_audio_file(audio_file.filename)
        temp_audio_path = create_temp_file(content, file_ext)
        
        # 음성 전사
        transcript_result = process_audio_transcription(audio_processor, temp_audio_path)
        transcript = transcript_result['transcript']
        speaker_stats = transcript_result.get('speaker_stats', {})
        
        # 입력 데이터 파싱
        qa_list = parse_json_input(qa_data)
        participants = parse_json_input(participants_info)
        
        # LLM 분석 수행
        analysis_data = perform_meeting_analysis(
            meeting_analyzer, transcript, speaker_stats, qa_list, participants
        )
        
        # 응답 생성
        return create_success_response(analysis_data, audio_file.filename, content, file_ext)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 처리 중 오류가 발생했습니다: {str(e)}")
    finally:
        cleanup_temp_file(temp_audio_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)