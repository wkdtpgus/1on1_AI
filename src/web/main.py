import os
from contextlib import asynccontextmanager
from typing import Union, Literal
import assemblyai as aai
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from supabase import create_client, Client


from src.services.meeting_generator.workflow import MeetingPipeline

from src.services.template_generator.generate_email import generate_email
from src.services.template_generator.generate_template import generate_template
from src.services.template_generator.generate_usage_guide import generate_usage_guide
from src.utils.schemas import (
    AnalyzeMeetingInput,
    EmailGeneratorInput,
    EmailGeneratorOutput,
    TemplateGeneratorInput,
    TemplateGeneratorOutput,
    UsageGuideInput,
)

from src.config.config import (
    ASSEMBLYAI_API_KEY,
    GOOGLE_APPLICATION_CREDENTIALS,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_BUCKET_NAME
)

meeting_pipeline = None
supabase: Client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 라이프사이클 관리"""
    global meeting_pipeline, supabase
    
    # Google Cloud 인증 설정
    if GOOGLE_APPLICATION_CREDENTIALS:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS
    
    # Supabase 클라이언트 초기화
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # AssemblyAI 설정
    aai.settings.api_key = ASSEMBLYAI_API_KEY
        
    # MeetingPipeline 초기화
    meeting_pipeline = MeetingPipeline(supabase)
    
    yield    

# FastAPI 앱 생성
app = FastAPI(
    title="1on1 Meeting AI Analysis & Template Generator API",
    description="1on1 미팅 분석 및 템플릿 생성을 위한 통합 API",
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

# ==================== STT & Analysis Endpoints ====================

@app.get("/api/config")
async def get_config():
    """Supabase 설정 정보 반환"""
    return {
        "supabase_url": SUPABASE_URL, 
        "supabase_key": SUPABASE_KEY, 
        "bucket_name": SUPABASE_BUCKET_NAME
    }

@app.post("/api/analyze",
         summary="1on1 미팅 오디오를 STT로 전사하고 LLM으로 분석 결과를 반환하는 엔드포인트")
async def analyze_meeting_with_storage(input_data: AnalyzeMeetingInput):
    """1on1 미팅 분석 API"""
    # LangGraph 파이프라인 실행 
    result = await meeting_pipeline.run(
        recording_url=input_data.recording_url,
        qa_pairs=input_data.qa_pairs,
        participants_info=input_data.participants_info,
        meeting_datetime=input_data.meeting_datetime,
        only_title=input_data.only_title
    )
    return JSONResponse(content=result.get("analysis_result", {}))

# ==================== Template Generator Endpoints ====================

@app.post(
    "/api/template",
    response_model=Union[TemplateGeneratorOutput, EmailGeneratorOutput],
    summary="1on1 미팅 템플릿, 이메일, 가이드 생성하는 엔드포인트")
async def generate_endpoint(
    input_data: TemplateGeneratorInput,
    generation_type: Literal["template", "email", "guide"] = Query(
        "template", description="생성할 콘텐츠 타입"
    ),
):
    """템플릿/이메일/가이드 생성 API"""
    try:
        if generation_type == "template":
            result = await generate_template(input_data)
        elif generation_type == "email":
            email_input = EmailGeneratorInput(
                user_id=input_data.user_id,
                target_info=input_data.target_info,
                purpose=input_data.purpose,
                detailed_context=input_data.detailed_context,
                use_previous_data=input_data.use_previous_data,
                previous_summary=input_data.previous_summary,
                language=input_data.language
            )
            result = await generate_email(email_input)
        elif generation_type == 'guide':
            if not input_data.generated_questions:
                raise HTTPException(status_code=400, detail="Usage guide generation requires 'generated_questions'.")
            
            guide_input = UsageGuideInput(
                user_id=input_data.user_id,
                target_info=input_data.target_info,
                purpose=input_data.purpose,
                detailed_context=input_data.detailed_context,
                generated_questions=input_data.generated_questions,
                language=input_data.language
            )
            return StreamingResponse(generate_usage_guide(guide_input), media_type="text/event-stream")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
