import assemblyai as aai
import os
import time
import logging
from typing import Optional

# 설정 값들 가져오기
from src.config.stt_config import (
    ASSEMBLYAI_API_KEY,
    ASSEMBLYAI_LANGUAGE,
    ASSEMBLYAI_PUNCTUATE,
    ASSEMBLYAI_FORMAT_TEXT,
    ASSEMBLYAI_DISFLUENCIES,
    ASSEMBLYAI_SPEAKER_LABELS,
    ASSEMBLYAI_LANGUAGE_DETECTION,
    ASSEMBLYAI_WORD_BOOST,
    ASSEMBLYAI_BOOST_PARAM,
    ASSEMBLYAI_SPEAKERS_EXPECTED
)

# 로깅 설정
logger = logging.getLogger("assembly_model")

# 설정과 상수들
TRANSCRIPT_POLL_INTERVAL = 5  # 전사 상태 확인 간격(초)


class AssemblyAIProcessor:
    """AssemblyAI 기반 음성-텍스트 처리 모델"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """API 키 검증과 함께 AssemblyAIProcessor 초기화"""
        self.api_key = self._resolve_api_key(api_key)
        self._configure_assemblyai()
        
        logger.debug("AssemblyAIProcessor가 성공적으로 초기화되었습니다")
    
    def _resolve_api_key(self, api_key: Optional[str]) -> str:
        """검증과 함께 여러 소스에서 API 키 해결"""
        resolved_key = api_key or ASSEMBLYAI_API_KEY or os.getenv("ASSEMBLYAI_API_KEY")
        
        if not resolved_key:
            error_msg = (
                "AssemblyAI API 키가 필요합니다. "
                "파라미터, config.py 또는 ASSEMBLYAI_API_KEY 환경 변수를 통해 제공하세요."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        return resolved_key
    
    def _configure_assemblyai(self) -> None:
        """AssemblyAI 설정 구성"""
        try:
            aai.settings.api_key = self.api_key
            logger.debug("AssemblyAI가 성공적으로 구성되었습니다")
        except Exception as e:
            logger.error(f"AssemblyAI 구성 실패: {e}")
            raise

    def create_transcription_config(self, expected_speakers: Optional[int] = None) -> aai.TranscriptionConfig:
        """AssemblyAI 전사 구성 생성
        
        Args:
            expected_speakers: 예상 화자 수 (None이면 기본값 사용)
        """
        try:
            # 동적으로 화자 수 설정 (최소 2명, 최대 10명으로 제한)
            speakers_count = expected_speakers if expected_speakers is not None else ASSEMBLYAI_SPEAKERS_EXPECTED
            speakers_count = max(2, min(speakers_count, 10))
            
            logger.debug(f"화자 수 설정: {speakers_count}명")
            
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
                
            logger.debug("전사 구성이 생성되었습니다")
            return config
            
        except Exception as e:
            logger.error(f"전사 구성 생성 실패: {e}")
            raise
    
    def perform_transcription(self, audio_file: str, config: aai.TranscriptionConfig) -> Optional[aai.Transcript]:
        """상태 폴링과 함께 전사 수행"""
        try:
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(audio_file)
            
            logger.info("전사 완료를 기다리고 있습니다...")
            
            # 적절한 에러 처리와 함께 완료 여부 폴링
            while transcript.status not in [aai.TranscriptStatus.completed, aai.TranscriptStatus.error]:
                logger.debug(f"전사 상태: {transcript.status}")
                time.sleep(TRANSCRIPT_POLL_INTERVAL)
                transcript = transcript.get()
                
            logger.info(f"전사 완료, 상태: {transcript.status}")
            return transcript
            
        except Exception as e:
            logger.error(f"전사 실패: {e}")
            return None

    def execute_transcription(self, audio_file: str, expected_speakers: Optional[int]) -> Optional[aai.Transcript]:
        """전사 실행을 위한 내부 메서드"""
        # 전사 구성 생성
        config = self.create_transcription_config(expected_speakers)
        
        # 전사 수행
        transcript = self.perform_transcription(audio_file, config)
        
        if transcript and transcript.status == aai.TranscriptStatus.error:
            logger.error(f"전사 실패: {transcript.error}")
            return None
            
        return transcript