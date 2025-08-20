import logging
import os
from contextlib import asynccontextmanager
from typing import Optional
import assemblyai as aai
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from supabase import create_client, Client
from src.utils.model import MeetingAnalyzer
from src.services.meeting_analyze.meeting_pipeline import MeetingPipeline
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
    qa_pairs: Optional[str] = Form(default=None),
    participants_info: Optional[str] = Form(default=None),
    meeting_datetime: Optional[str] = Form(default=None)
):
    # LangGraph 파이프라인 실행 
    result = await meeting_pipeline.run(
        file_id=file_id,
        qa_pairs=qa_pairs,
        participants_info=participants_info,
        meeting_datetime=meeting_datetime
    )
    return JSONResponse(content=result.get("analysis_result", {}))
