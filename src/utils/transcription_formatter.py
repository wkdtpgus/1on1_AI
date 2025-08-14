import logging
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum

# 로깅 설정
logger = logging.getLogger("transcription_formatter")

# 상수들
class ProcessingStatus(Enum):
    """처리 상태 값들을 위한 열거형"""
    SUCCESS = "success"
    ERROR = "error"
    SUCCESS_NO_UTTERANCES = "success_but_no_utterances"
    PROCESSING = "processing"

# 설정과 상수들
TIME_DISPLAY_FORMAT = "{minutes}분 {seconds}초"


class TranscriptionFormatter:
    """전사 결과의 포매팅과 분석을 처리"""
    
    @staticmethod
    def create_error_result(message: str, audio_file: str = "") -> Dict[str, Any]:
        """표준화된 에러 결과 생성"""
        return {
            "status": ProcessingStatus.ERROR.value,
            "message": message,
            "audio_file": audio_file,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def format_time_display(seconds: float) -> str:
        """초를 MM분 SS초 표시 형식으로 포맷팅"""
        minutes = int(seconds // 60)
        seconds_remainder = int(seconds % 60)
        return TIME_DISPLAY_FORMAT.format(minutes=minutes, seconds=seconds_remainder)
    
    @staticmethod
    def format_timestamp_display(seconds: float) -> str:
        """초를 MM:SS 타임스탬프 형식으로 포맷팅"""
        minutes = int(seconds // 60)
        seconds_remainder = int(seconds % 60)
        return f"{minutes:02d}:{seconds_remainder:02d}"
    
    @staticmethod
    def create_utterances_info(
        utterances: List[Any], 
        speaker_mapping: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """프론트엔드를 위한 상세한 발화 정보 생성"""
        utterances_info = []
        
        for utterance in utterances:
            speaker_name = speaker_mapping.get(utterance.speaker, "참석자")
            start_seconds = utterance.start / 1000  # 밀리초에서 초로
            end_seconds = utterance.end / 1000
            duration = end_seconds - start_seconds
            
            utterances_info.append({
                "speaker": speaker_name,
                "start_time": round(start_seconds, 1),
                "end_time": round(end_seconds, 1),
                "duration": round(duration, 1),
                "text": utterance.text,
                "formatted_start": TranscriptionFormatter.format_timestamp_display(start_seconds)
            })
            
        return utterances_info
    
    @staticmethod
    def create_gemini_formatted_transcript(
        utterances: List[Any],
        speaker_mapping: Dict[str, str]
    ) -> str:
        """Gemini 모델에 최적화된 전사 텍스트 형식 생성"""
        lines = []
        
        # 명확한 구분자로 시작
        lines.append("## 회의 전사 내용")
        lines.append("")
        
        # 대화 내용
        lines.append("### 대화 내용")
        for utterance in utterances:
            speaker_name = speaker_mapping.get(utterance.speaker, '참석자')
            start_time = TranscriptionFormatter.format_timestamp_display(utterance.start / 1000)
            # 간소화된 형식: [타임스탬프] 화자명: 내용
            lines.append(f"[{start_time}] {speaker_name}: {utterance.text}")
        
        return "\n".join(lines)