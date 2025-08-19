import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import assemblyai as aai
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from supabase import create_client, Client

from src.config.config import (
    ASSEMBLYAI_API_KEY,
    GOOGLE_CLOUD_PROJECT, 
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_APPLICATION_CREDENTIALS_JSON,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_BUCKET_NAME
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stt_main")

meeting_analyzer = None
meeting_pipeline = None
supabase: Client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global meeting_analyzer, meeting_pipeline, supabase
    
    if GOOGLE_APPLICATION_CREDENTIALS_JSON:
        creds_path = "/tmp/gcp_creds.json"
        with open(creds_path, "w", encoding="utf-8") as f:
            f.write(GOOGLE_APPLICATION_CREDENTIALS_JSON)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    aai.settings.api_key = ASSEMBLYAI_API_KEY
    
    from src.utils.model import MeetingAnalyzer
    from src.services.meeting_analyze.meeting_pipeline import MeetingPipeline
    
    meeting_analyzer = MeetingAnalyzer(GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION)
    meeting_pipeline = MeetingPipeline(supabase, meeting_analyzer)
    
    logger.info("서비스 초기화 완료")
    yield

app = FastAPI(title="1on1 Meeting AI Analysis", version="1.0.0", lifespan=lifespan)

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
    return FileResponse("frontend/index.html")

@app.get("/api.js")
async def api_js():
    return FileResponse("frontend/api.js", media_type="application/javascript")

@app.get("/app.js")
async def app_js():
    return FileResponse("frontend/app.js", media_type="application/javascript")

@app.get("/api/config")
async def get_config():
    return {"supabase_url": SUPABASE_URL, "supabase_key": SUPABASE_KEY, "bucket_name": SUPABASE_BUCKET_NAME}

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