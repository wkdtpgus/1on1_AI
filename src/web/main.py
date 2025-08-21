import os
from contextlib import asynccontextmanager
from typing import Optional, Union, Literal
import assemblyai as aai
from fastapi import FastAPI, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import create_client, Client


from src.services.meeting_generator.workflow import MeetingPipeline

from src.services.template_generator.generate_email import generate_email
from src.services.template_generator.generate_template import generate_template
from src.services.template_generator.generate_usage_guide import generate_usage_guide
from src.utils.template_schemas import (
    EmailGeneratorInput,
    EmailGeneratorOutput,
    TemplateGeneratorInput,
    TemplateGeneratorOutput,
    UsageGuideInput,
    UsageGuideOutput,
)

from src.config.config import (
    ASSEMBLYAI_API_KEY,
    GOOGLE_APPLICATION_CREDENTIALS_JSON,
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
    if GOOGLE_APPLICATION_CREDENTIALS_JSON:
        creds_path = "/tmp/gcp_creds.json"
        with open(creds_path, "w", encoding="utf-8") as f:
            f.write(GOOGLE_APPLICATION_CREDENTIALS_JSON)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
    
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
async def analyze_meeting_with_storage(
    file_id: Optional[str] = Form(default=None, description="Supabase 스토리지에 업로드된 오디오 파일 ID - only_title=true일 때는 불필요"),
    qa_pairs: Optional[str] = Form(default=None, description="미리 준비된 질문-답변 쌍 (JSON 문자열)"),
    participants_info: Optional[str] = Form(default=None, description="참가자 정보 (JSON 문자열, 예: {\"leader\": \"김지현\", \"member\": \"김준희\"})"),
    meeting_datetime: Optional[str] = Form(default=None, description="회의 일시 (ISO 8601 형식, 예: 2024-12-08T14:30:00)"),
    only_title: Optional[bool] = Form(default=False, description="제목만 생성할지 여부 (기본값: False)")
):
    """1on1 미팅 분석 API"""
    # LangGraph 파이프라인 실행 
    result = await meeting_pipeline.run(
        file_id=file_id,
        qa_pairs=qa_pairs,
        participants_info=participants_info,
        meeting_datetime=meeting_datetime,
        only_title=only_title
    )
    return JSONResponse(content=result.get("analysis_result", {}))

# ==================== Template Generator Endpoints ====================

@app.post(
    "/generate",
    response_model=Union[TemplateGeneratorOutput, EmailGeneratorOutput, UsageGuideOutput],
    summary="1on1 미팅 템플릿, 이메일, 가이드 생성",
    description="""
    1on1 미팅을 위한 다양한 콘텐츠를 생성합니다:
    - template: 1on1 미팅 질문 템플릿 생성
    - email: 1on1 미팅 초대 이메일 생성  
    - guide: 1on1 미팅 진행 가이드 생성
    """
)
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
            result = await generate_usage_guide(guide_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
