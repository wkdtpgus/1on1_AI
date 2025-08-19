from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging

# 프로젝트 모듈 임포트
from src.config.config import (
    ASSEMBLYAI_API_KEY,
    GOOGLE_CLOUD_PROJECT, 
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_APPLICATION_CREDENTIALS_JSON,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_BUCKET_NAME
)
import os
import json
from datetime import datetime
from fastapi.responses import JSONResponse
import assemblyai as aai
from supabase import create_client, Client

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stt_main")

# 서비스 인스턴스
meeting_analyzer = None
meeting_pipeline = None
supabase: Client = None

# 더 이상 Pydantic 모델이 필요하지 않음 (Form 데이터 직접 처리)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global meeting_analyzer, meeting_pipeline, supabase
    
    # Google 자격증명 설정
    if GOOGLE_APPLICATION_CREDENTIALS_JSON:
        creds_path = "/tmp/gcp_creds.json"
        with open(creds_path, "w", encoding="utf-8") as f:
            f.write(GOOGLE_APPLICATION_CREDENTIALS_JSON)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
    
    # Supabase 초기화
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # AssemblyAI 초기화
    aai.settings.api_key = ASSEMBLYAI_API_KEY
    
    # 서비스 초기화
    from src.utils.model import MeetingAnalyzer
    from src.services.meeting_analyze.meeting_pipeline import MeetingPipeline
    
    meeting_analyzer = MeetingAnalyzer(
        google_project=GOOGLE_CLOUD_PROJECT, 
        google_location=GOOGLE_CLOUD_LOCATION
    )
    
    # LangGraph 파이프라인 초기화
    meeting_pipeline = MeetingPipeline(
        supabase_client=supabase,
        analyzer=meeting_analyzer
    )
    
    logger.info("모든 서비스 초기화 완료")
    logger.info(f"Supabase 연결: {SUPABASE_URL}")
    logger.info(f"기본 버킷: {SUPABASE_BUCKET_NAME}")
    logger.info("LangGraph 파이프라인 초기화 완료")
    
    yield
    # 종료시 정리 (필요시)

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


@app.get("/api/config")
async def get_config():
    """프론트엔드용 설정 정보 제공"""
    return {
        "supabase_url": SUPABASE_URL,
        "supabase_key": SUPABASE_KEY,
        "bucket_name": SUPABASE_BUCKET_NAME
    }


@app.post("/api/record-and-analyze")
async def record_and_analyze_meeting(
    audio_file: bytes = Form(...),
    filename: str = Form(...),
    qa_data: Optional[str] = Form(default=None),
    participants_info: Optional[str] = Form(default=None),
    meeting_datetime: Optional[str] = Form(default=None),
    bucket_name: Optional[str] = Form(default=SUPABASE_BUCKET_NAME)
):
    """
    음성 파일을 업로드하고 Supabase에 저장한 후 1on1 미팅 분석 수행
    
    Args:
        audio_file: 업로드된 음성 파일 (바이트)
        filename: 파일명
        qa_data: Q&A 데이터 (JSON 문자열)
        participants_info: 참가자 정보 (JSON 문자열)
        bucket_name: 버킷 이름
    """
    if not meeting_pipeline:
        raise HTTPException(status_code=503, detail="파이프라인이 초기화되지 않았습니다")
    
    try:
        logger.info(f"🎤 음성 파일 업로드 및 분석 시작: {filename}")
        
        # 고유한 파일명 생성 (타임스탬프 추가)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = filename.split('.')[-1] if '.' in filename else 'wav'
        unique_filename = f"{timestamp}_{filename}"
        
        # Supabase에 파일 업로드
        upload_result = supabase.storage.from_(bucket_name).upload(
            path=unique_filename,
            file=audio_file,
            file_options={"content-type": f"audio/{file_extension}"}
        )
        
        if hasattr(upload_result, 'error') and upload_result.error:
            raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {upload_result.error}")
        
        logger.info(f"✅ 파일 업로드 완료: {unique_filename}")
        
        # JSON 입력 파싱
        qa_list = json.loads(qa_data) if qa_data else None
        participants = json.loads(participants_info) if participants_info else None
        
        # LangGraph 파이프라인 실행
        result = await meeting_pipeline.run(
            file_id=unique_filename,
            bucket_name=bucket_name,
            qa_data=qa_list,
            participants_info=participants,
            meeting_datetime=meeting_datetime
        )
        
        # 파이프라인 실행 실패 처리
        if result["status"] == "failed":
            error_details = "; ".join(result.get("errors", ["알 수 없는 오류"]))
            raise HTTPException(status_code=500, detail=f"파이프라인 실행 실패: {error_details}")
        
        # 성공 응답 생성
        analysis_data = result.get("analysis_result", {})
        transcript_data = result.get("transcript", {})
        speaker_stats_percent = result.get("speaker_stats_percent", {})
        formatted_transcript = result.get("formatted_transcript", transcript_data.get("utterances", []))
        
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            **analysis_data,
            "transcript": {
                "utterances": formatted_transcript
            },
            "speaker_stats_percent": speaker_stats_percent,
            "file_info": {
                "file_id": unique_filename,
                "bucket_name": bucket_name,
                "file_path": result.get("file_path", ""),
                "uploaded_filename": filename
            },
            "pipeline_info": {
                "pipeline_status": result["status"],
                "errors": result.get("errors", [])
            }
        }
        
        logger.info(f"✅ 음성 파일 업로드 및 분석 완료: {unique_filename}")
        return JSONResponse(content=response)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"음성 파일 업로드 및 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"음성 파일 처리 중 오류가 발생했습니다: {str(e)}")


@app.post("/api/analyze")
async def analyze_meeting_with_storage(
    file_id: str = Form(...),
    qa_data: Optional[str] = Form(default=None),
    participants_info: Optional[str] = Form(default=None),
    meeting_datetime: Optional[str] = Form(default=None),
    bucket_name: Optional[str] = Form(default=SUPABASE_BUCKET_NAME)
):
    """
    LangGraph 파이프라인을 사용한 1on1 미팅 분석 API
    
    Args:
        file_id: Supabase 스토리지 파일 ID
        qa_data: Q&A 데이터 (JSON 문자열)
        participants_info: 참가자 정보 (JSON 문자열)
        bucket_name: 버킷 이름
    """
    if not meeting_pipeline:
        raise HTTPException(status_code=503, detail="파이프라인이 초기화되지 않았습니다")
    
    try:
        logger.info(f"🚀 LangGraph 파이프라인 시작: {file_id}")
        
        # JSON 입력 파싱
        qa_list = json.loads(qa_data) if qa_data else None
        participants = json.loads(participants_info) if participants_info else None
        
        # LangGraph 파이프라인 실행
        result = await meeting_pipeline.run(
            file_id=file_id,
            bucket_name=bucket_name,
            qa_data=qa_list,
            participants_info=participants,
            meeting_datetime=meeting_datetime
        )
        
        # 파이프라인 실행 실패 처리
        if result["status"] == "failed":
            error_details = "; ".join(result.get("errors", ["알 수 없는 오류"]))
            raise HTTPException(status_code=500, detail=f"파이프라인 실행 실패: {error_details}")
        
        # 성공 응답 생성
        analysis_data = result.get("analysis_result", {})
        transcript_data = result.get("transcript", {})
        speaker_stats_percent = result.get("speaker_stats_percent", {})
        formatted_transcript = result.get("formatted_transcript", transcript_data.get("utterances", []))
        
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            **analysis_data,
            "transcript": {
                "utterances": formatted_transcript
            },
            "speaker_stats_percent": speaker_stats_percent,
            "file_info": {
                "file_id": file_id,
                "bucket_name": bucket_name,
                "file_path": result.get("file_path", "")
            },
            "pipeline_info": {
                "pipeline_status": result["status"],
                "errors": result.get("errors", [])
            }
        }
        
        logger.info(f"✅ LangGraph 파이프라인 완료: {file_id}")
        return JSONResponse(content=response)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파이프라인 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파이프라인 처리 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)