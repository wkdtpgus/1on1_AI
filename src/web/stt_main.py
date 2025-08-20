import logging
import os
from contextlib import asynccontextmanager
from typing import Optional
import assemblyai as aai
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from supabase import create_client, Client
from src.services.meeting_analyze.workflow import MeetingPipeline
from src.config.config import (
    ASSEMBLYAI_API_KEY,
    GOOGLE_APPLICATION_CREDENTIALS_JSON,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_BUCKET_NAME
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stt_main")

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
        
    meeting_pipeline = MeetingPipeline(supabase)
    
    logger.info("서비스 초기화 완료")
    yield

app = FastAPI(
    title="1on1 Meeting AI Analysis API",
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

@app.post("/api/analyze",
         summary="1on1 미팅 오디오를 STT로 전사하고 LLM으로 분석 결과를 반환하는 엔드포인트",
         description="""
         업로드된 오디오 파일을 분석하여 종합적인 1대1 미팅 리포트를 생성.
         
         입력 데이터 :
          file_id: Supabase에 업로드된 오디오 파일 ID (필수)
          qa_pairs: 질문-답변 JSON 문자열 (선택)
          participants_info: 참가자 정보 JSON (필수)
          meeting_datetime: 회의 일시 ISO 문자열 (필수)
        
         반환 데이터 구조:
         ```json
         {
           "title": "회의 제목 한 줄 요약",
           "speaker_stats_percent": {
             "speaking_ratio_leader": 45.2,
             "speaking_ratio_member": 54.8
           },
           "leader_action_items": ["액션아이템1", "액션아이템2"],
           "member_action_items": ["액션아이템1", "액션아이템2"],
           "ai_core_summary": {
             "core_content": "핵심내용",
             "decisions_made": ["결정사항1", "결정사항2"],
             "support_needs_blockers": ["지원요청/블로커1", "지원요청/블로커2"]
           },
           "ai_summary": "마크다운 형식의 상세 회의 내용",
           "leader_feedback": [
             {
               "title": "피드백 개선내용 제목",
               "content": "피드백 내용"
             }
           ],
           "positive_aspects": [
             {
               "title": "잘한점 제목",
               "content": "긍정적 피드백 내용"
             }
           ],
           "qa_summary": [
             {
               "question_index": 1,
               "answer": "질문에 대한 답변"
             }
           ],
           "transcript": [
             {"speaker": "실제이름", "text": "발화내용"}
           ]
         }
         ```
         """)
  
async def analyze_meeting_with_storage(
    file_id: Optional[str] = Form(default=None, description="(선택)Supabase 스토리지에 업로드된 오디오 파일 ID - only_title=true일 때는 불필요"),
    qa_pairs: Optional[str] = Form(default=None, description="(선택)미리 준비된 질문-답변 쌍 (JSON 문자열)"),
    participants_info: Optional[str] = Form(default=None, description="(필수)참가자 정보 (JSON 문자열, 예: {\"leader\": \"김지현\", \"member\": \"김준희\"})"),
    meeting_datetime: Optional[str] = Form(default=None, description="(필수)회의 일시 (ISO 8601 형식, 예: 2024-12-08T14:30:00)"),
    only_title: Optional[bool] = Form(default=False, description="(선택)제목만 생성할지 여부 (기본값: False)")
):
    # LangGraph 파이프라인 실행 
    result = await meeting_pipeline.run(
        file_id=file_id,
        qa_pairs=qa_pairs,
        participants_info=participants_info,
        meeting_datetime=meeting_datetime,
        only_title=only_title
    )
    return JSONResponse(content=result.get("analysis_result", {}))
