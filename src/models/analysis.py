from typing import Optional, Dict, List
from langchain_google_vertexai import ChatVertexAI
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
import logging

# 설정 가져오기
from src.config.config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    VERTEX_AI_MODEL,
    VERTEX_AI_TEMPERATURE,
    VERTEX_AI_MAX_TOKENS,
    LANGSMITH_TRACING,
    LANGSMITH_PROJECT
)
from src.prompts.stt_generation.meeting_analysis_prompts import SYSTEM_PROMPT, USER_PROMPT
from src.utils.stt_schemas import MeetingAnalysis
from src.services.meeting_analyze.analyzer import BaseMeetingAnalyzer

# 로깅 설정
logger = logging.getLogger("analysis_model")

# LangSmith 추적 상태 로깅 (config에서 이미 환경변수 설정됨)
if LANGSMITH_TRACING:
    logger.info(f"LangSmith 추적 활성화됨 - 프로젝트: {LANGSMITH_PROJECT}")
else:
    logger.info("LangSmith 추적이 비활성화되어 있습니다")


class GeminiMeetingAnalyzer(BaseMeetingAnalyzer):    
    """Google Vertex AI Gemini 모델을 사용한 회의 분석기"""
    
    def __init__(self, google_project: Optional[str] = None, google_location: Optional[str] = None):
        super().__init__()
        
        self.google_project = google_project or GOOGLE_CLOUD_PROJECT
        self.google_location = google_location or GOOGLE_CLOUD_LOCATION
        
        if not self.google_project:
            raise ValueError("Google Cloud Project ID is required")
        
        # Vertex AI Gemini LLM 초기화
        self.llm = ChatVertexAI(
            project=self.google_project,
            location=self.google_location,
            model_name=VERTEX_AI_MODEL,
            temperature=VERTEX_AI_TEMPERATURE,
            max_output_tokens=VERTEX_AI_MAX_TOKENS,
        )
        logger.info(f"Vertex AI {VERTEX_AI_MODEL} 모델 초기화 완료")
