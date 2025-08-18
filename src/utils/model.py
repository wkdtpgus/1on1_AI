# =============================================================================
# Imports
# =============================================================================
import assemblyai as aai
import os
import time
import logging
from typing import Optional, Dict, List
from langchain_google_vertexai import ChatVertexAI
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate

from src.config.config import (
    # Google Cloud / Vertex AI 설정
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    # Gemini 템플릿 생성용 설정
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE,
    GEMINI_THINKING_BUDGET,
    # Vertex AI STT 분석용 설정
    VERTEX_AI_MODEL,
    VERTEX_AI_TEMPERATURE,
    VERTEX_AI_MAX_TOKENS,
    # AssemblyAI 설정
    ASSEMBLYAI_API_KEY,
    ASSEMBLYAI_LANGUAGE,
    ASSEMBLYAI_PUNCTUATE,
    ASSEMBLYAI_FORMAT_TEXT,
    ASSEMBLYAI_DISFLUENCIES,
    ASSEMBLYAI_SPEAKER_LABELS,
    ASSEMBLYAI_LANGUAGE_DETECTION,
    ASSEMBLYAI_WORD_BOOST,
    ASSEMBLYAI_BOOST_PARAM,
    ASSEMBLYAI_SPEAKERS_EXPECTED,
    # LangSmith 설정
    LANGSMITH_TRACING,
    LANGSMITH_PROJECT
)

# =============================================================================
# 로깅 설정
# =============================================================================
logger = logging.getLogger("model")
TRANSCRIPT_POLL_INTERVAL = 5  # 전사 상태 확인 간격(초)

# LangSmith 추적 상태 로깅
if LANGSMITH_TRACING:
    logger.info(f"LangSmith 추적 활성화됨 - 프로젝트: {LANGSMITH_PROJECT}")
else:
    logger.info("LangSmith 추적이 비활성화되어 있습니다")

# =============================================================================
# Gemini LLM 인스턴스 (템플릿 생성용)
# =============================================================================

# 기본 LLM (스트리밍 비활성화)
llm = ChatVertexAI(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    model_name=GEMINI_MODEL,
    max_output_tokens=GEMINI_MAX_TOKENS,
    temperature=GEMINI_TEMPERATURE,
    # model_kwargs={"thinking_budget": GEMINI_THINKING_BUDGET}, # Deprecated
    thinking_budget=GEMINI_THINKING_BUDGET, # Pass directly
    streaming=False,
)

# 스트리밍 LLM
llm_streaming = ChatVertexAI(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    model_name=GEMINI_MODEL,
    max_output_tokens=GEMINI_MAX_TOKENS,
    temperature=GEMINI_TEMPERATURE,
    # model_kwargs={"thinking_budget": GEMINI_THINKING_BUDGET}, # Deprecated
    thinking_budget=GEMINI_THINKING_BUDGET, # Pass directly
    streaming=True,
)

# =============================================================================
# AssemblyAI 모델 (음성-텍스트 변환)
# =============================================================================

class AssemblyAIProcessor:
    """AssemblyAI 기반 음성-텍스트 처리 모델"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """API 키 검증과 함께 AssemblyAIProcessor 초기화"""
        self.api_key = api_key or ASSEMBLYAI_API_KEY or os.getenv("ASSEMBLYAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("AssemblyAI API 키가 필요합니다")
            
        aai.settings.api_key = self.api_key
        logger.debug("AssemblyAIProcessor가 성공적으로 초기화되었습니다")

    def execute_transcription(self, audio_file: str, expected_speakers: Optional[int]) -> Optional[aai.Transcript]:
        """전사 실행을 위한 메서드"""
        try:
            # 화자 수 설정 (최소 2명, 최대 10명으로 제한)
            speakers_count = expected_speakers if expected_speakers is not None else ASSEMBLYAI_SPEAKERS_EXPECTED
            speakers_count = max(2, min(speakers_count, 10))
            logger.debug(f"화자 수 설정: {speakers_count}명")
            
            # 전사 구성 생성
            config = aai.TranscriptionConfig(
                language_code=ASSEMBLYAI_LANGUAGE,
                punctuate=ASSEMBLYAI_PUNCTUATE,
                format_text=ASSEMBLYAI_FORMAT_TEXT,
                disfluencies=ASSEMBLYAI_DISFLUENCIES,
                speaker_labels=ASSEMBLYAI_SPEAKER_LABELS,
                language_detection=ASSEMBLYAI_LANGUAGE_DETECTION,
                speakers_expected=speakers_count
            )

            # 구성된 경우 단어 부스트 추가
            if ASSEMBLYAI_WORD_BOOST:
                config.word_boost = ASSEMBLYAI_WORD_BOOST
                config.boost_param = ASSEMBLYAI_BOOST_PARAM
            
            # 전사 수행
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(audio_file)
            
            logger.info("전사 완료를 기다리고 있습니다...")
            
            # 완료 여부 폴링
            while transcript.status not in [aai.TranscriptStatus.completed, aai.TranscriptStatus.error]:
                logger.debug(f"전사 상태: {transcript.status}")
                time.sleep(TRANSCRIPT_POLL_INTERVAL)
                transcript = transcript.get()
                
            logger.info(f"전사 완료, 상태: {transcript.status}")
            
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"전사 실패: {transcript.error}")
                return None
                
            return transcript
            
        except Exception as e:
            logger.error(f"전사 실패: {e}")
            return None

# =============================================================================
# Vertex AI Gemini 분석 모델 (STT 분석용)
# =============================================================================

# analyzer 기능을 import
from src.services.meeting_analyze.analyzer import BaseMeetingAnalyzer

class GeminiMeetingAnalyzer(BaseMeetingAnalyzer):    
    """Google Vertex AI Gemini 모델을 사용한 회의 분석기"""
    
    def __init__(self, google_project: Optional[str] = None, google_location: Optional[str] = None):
        super().__init__()  # BaseMeetingAnalyzer 초기화
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
