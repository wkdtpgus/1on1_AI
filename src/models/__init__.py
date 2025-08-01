"""
1on1 AI 모델 패키지
데이터 모델과 처리 로직을 통합 관리합니다.
"""

from .transcription import TranscriptionResult, Utterance, STTProcessor
from .recording import RecordingSession, RecordingStatus
from .stt_llm_analysis import STTLLMAnalysisResult, MeetingAnalyzer
from .template import GeneratedTemplate, TemplateRequest, QuestionGenerator

__all__ = [
    # STT 관련
    "TranscriptionResult",
    "Utterance", 
    "STTProcessor",
    
    # 녹음 관련
    "RecordingSession",
    "RecordingStatus",
    
    # STT→LLM 분석 관련
    "STTLLMAnalysisResult",
    "MeetingAnalyzer",
    
    # 템플릿 생성 관련
    "GeneratedTemplate",
    "TemplateRequest",
    "QuestionGenerator"
]