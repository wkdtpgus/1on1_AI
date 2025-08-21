import assemblyai as aai
import logging
from typing import Optional
from langchain_google_vertexai import ChatVertexAI

from src.config.config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE,
    GEMINI_THINKING_BUDGET,
    TITLE_GEMINI_MODEL,
    TITLE_GEMINI_MAX_TOKENS,
    TITLE_GEMINI_TEMPERATURE,
    TITLE_GEMINI_THINKING_BUDGET,
    VERTEX_AI_MODEL,
    VERTEX_AI_TEMPERATURE,
    VERTEX_AI_MAX_TOKENS,
    ASSEMBLYAI_API_KEY,
    ASSEMBLYAI_LANGUAGE,
    ASSEMBLYAI_PUNCTUATE,
    ASSEMBLYAI_FORMAT_TEXT,
    ASSEMBLYAI_DISFLUENCIES,
    ASSEMBLYAI_SPEAKER_LABELS,
    ASSEMBLYAI_LANGUAGE_DETECTION,
    ASSEMBLYAI_SPEAKERS_EXPECTED
)

logger = logging.getLogger("model")

# Gemini LLM 인스턴스 (템플릿 생성용)
llm = ChatVertexAI(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    model_name=GEMINI_MODEL,
    max_output_tokens=GEMINI_MAX_TOKENS,
    temperature=GEMINI_TEMPERATURE,
    thinking_budget=GEMINI_THINKING_BUDGET,
)

# 제목 생성용 LLM (config에서 설정 가져오기)
title_llm = ChatVertexAI(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    model_name=TITLE_GEMINI_MODEL,
    max_output_tokens=TITLE_GEMINI_MAX_TOKENS,
    temperature=TITLE_GEMINI_TEMPERATURE,
    thinking_budget=TITLE_GEMINI_THINKING_BUDGET,
)

# Vertex AI Gemini 분석 모델 (STT 분석용)
meeting_llm = ChatVertexAI(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    model_name=VERTEX_AI_MODEL,
    temperature=VERTEX_AI_TEMPERATURE,
    max_output_tokens=VERTEX_AI_MAX_TOKENS,
)

class SpeechTranscriber:
    """AssemblyAI 기반 음성 전사기"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """API 키 검증과 함께 SpeechTranscriber 초기화"""
        self.api_key = api_key or ASSEMBLYAI_API_KEY 
        
        if not self.api_key:
            raise ValueError("AssemblyAI API 키가 필요합니다")
            
        aai.settings.api_key = self.api_key
        
        # 1on1 미팅용 전사 설정 생성 (timeout 연장)
        self.config = aai.TranscriptionConfig(
            language_code=ASSEMBLYAI_LANGUAGE,
            punctuate=ASSEMBLYAI_PUNCTUATE,
            format_text=ASSEMBLYAI_FORMAT_TEXT,
            disfluencies=ASSEMBLYAI_DISFLUENCIES,
            speaker_labels=ASSEMBLYAI_SPEAKER_LABELS,
            language_detection=ASSEMBLYAI_LANGUAGE_DETECTION,
            speakers_expected=ASSEMBLYAI_SPEAKERS_EXPECTED,
            # Timeout 설정 추가 (기본 5분 → 15분)
            webhook_url=None,  # 폴링 방식 사용
            webhook_auth_header_name=None
        )
        
        logger.debug(f"STT 모델 초기화 완료")

