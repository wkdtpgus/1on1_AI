# 1. 표준 라이브러리
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from enum import Enum

# 2. 서드파티 라이브러리
import assemblyai as aai

# 3. 내부 모듈
from src.config.stt_config import OUTPUT_DIR
from src.models.transcription import AssemblyAIProcessor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("formatter")

# 설정과 상수들
FILE_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
TIME_DISPLAY_FORMAT = "{minutes}분 {seconds}초"
SPEAKER_ALPHABET_START = 65  # ASCII 'A'


# 상수들
class ProcessingStatus(Enum):
    """처리 상태 값들을 위한 열거형"""
    SUCCESS = "success"
    ERROR = "error"
    SUCCESS_NO_UTTERANCES = "success_but_no_utterances"
    PROCESSING = "processing"


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
    def create_llm_formatted_transcript(
        utterances: List[Any],
        speaker_mapping: Dict[str, str]
    ) -> str:
        """LLM 모델에 최적화된 전사 텍스트 형식 생성"""
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


class SpeakerStatsProcessor:
    """화자 통계 처리를 담당하는 클래스"""
    
    @staticmethod
    def create_speaker_mapping(
        unique_labels: List[str], 
        participants_info: Optional[Dict[str, Dict[str, str]]]
    ) -> Dict[str, str]:
        """화자 라벨에서 표시 이름으로의 매핑 생성"""
        speaker_mapping = {}
        
        for i, label in enumerate(sorted(unique_labels)):
            if participants_info and label in participants_info:
                speaker_name = participants_info[label]["name"]
            else:
                speaker_name = chr(SPEAKER_ALPHABET_START + i)  # A, B, C...
            speaker_mapping[label] = speaker_name
            
        return speaker_mapping
    
    @staticmethod
    def calculate_speaker_times(utterances: List[Any]) -> Dict[str, float]:
        """각 화자의 총 발언 시간을 밀리초 단위로 계산"""
        speaker_times = {}
        
        for utterance in utterances:
            speaker = utterance.speaker
            duration = utterance.end - utterance.start  # 밀리초
            
            speaker_times[speaker] = speaker_times.get(speaker, 0) + duration
            
        return speaker_times
    
    @staticmethod
    def create_speaker_time_info(
        speaker_times: Dict[str, float], 
        speaker_mapping: Dict[str, str],
        total_time_seconds: float
    ) -> Dict[str, Dict[str, Union[float, str]]]:
        """상세한 화자 시간 정보 생성"""
        speaker_time_info = {}
        
        for speaker, time_ms in speaker_times.items():
            time_seconds = time_ms / 1000
            percentage = (time_seconds / total_time_seconds * 100) if total_time_seconds > 0 else 0
            speaker_name = speaker_mapping.get(speaker, "참석자")
            
            speaker_time_info[speaker_name] = {
                "total_seconds": round(time_seconds, 2),
                "formatted_time": TranscriptionFormatter.format_time_display(time_seconds),
                "percentage": round(percentage, 1)
            }
            
        return speaker_time_info
    
    @staticmethod
    def calculate_meeting_duration(utterances: List[Any]) -> float:
        """실제 회의 전체 시간 계산"""
        if not utterances:
            return 0
            
        meeting_start = min(u.start for u in utterances)
        meeting_end = max(u.end for u in utterances)
        return (meeting_end - meeting_start) / 1000  # 밀리초에서 초로


class STTProcessor:
    """AssemblyAI 모델을 사용한 음성-텍스트 처리 서비스"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """STTProcessor 초기화"""
        self.assembly_processor = AssemblyAIProcessor(api_key=api_key)
        logger.debug("STTProcessor가 성공적으로 초기화되었습니다")

    def transcribe_audio(
        self, 
        audio_file: str, 
        participants_info: Optional[Dict[str, Dict[str, str]]] = None,
        expected_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """오디오 파일을 전사하고 결과를 포맷팅
        
        Args:
            audio_file: 처리할 오디오 파일 경로
            participants_info: 화자 정보 딕셔너리 (예: {"A": {"name": "김준희", "role": "팀원"}})
            expected_speakers: 더 나은 전사를 위한 예상 화자 수
            
        Returns:
            구조화된 전사 결과 딕셔너리
        """
        logger.info(f"전사 시작: {audio_file}")
        
        # 입력 파일 검증
        if not os.path.exists(audio_file):
            logger.error(f"오디오 파일을 찾을 수 없습니다: {audio_file}")
            return TranscriptionFormatter.create_error_result(
                f"오디오 파일을 찾을 수 없습니다: {audio_file}",
                audio_file
            )

        try:
            # 전사 수행
            transcript = self.assembly_processor.execute_transcription(audio_file, expected_speakers)
            
            if not transcript:
                logger.error("전사 실패")
                return TranscriptionFormatter.create_error_result("전사 실패", audio_file)
            
            # 결과 포맷팅 및 저장
            formatted_result = self._format_transcription_result(transcript, audio_file, participants_info)
            self._save_transcription_result(formatted_result)
            
            logger.info("전사가 성공적으로 완료되었습니다")
            return formatted_result

        except Exception as e:
            logger.error(str(e))
            return TranscriptionFormatter.create_error_result(str(e), audio_file)

    def _format_transcription_result(
        self, 
        transcript: aai.Transcript, 
        audio_file: str, 
        participants_info: Optional[Dict[str, Dict[str, str]]]
    ) -> Dict[str, Any]:
        """AssemblyAI 전사 결과를 구조화된 JSON으로 포매팅"""
        
        logger.debug(f"전사 결과 포매팅 시작: {audio_file}")
        
        # 발화가 없는 경우 처리
        if not hasattr(transcript, 'utterances') or not transcript.utterances:
            logger.warning("전사에서 발화를 찾을 수 없습니다")
            return {
                "transcript": "전사된 내용이 없습니다.",
                "status": ProcessingStatus.SUCCESS_NO_UTTERANCES.value,
                "timestamp": datetime.now().isoformat(),
                "speaker_times": {},
                "utterances": []
            }

        # 고유한 화자들을 추출하고 매핑 생성
        unique_labels = list(set(u.speaker for u in transcript.utterances))
        speaker_mapping = SpeakerStatsProcessor.create_speaker_mapping(unique_labels, participants_info)
        
        # 화자 시간 계산
        speaker_times = SpeakerStatsProcessor.calculate_speaker_times(transcript.utterances)
        
        # 클로바 노트 방식: 순수 발언 시간 합계를 기준으로 점유율 계산 (침묵 구간 제외)
        total_speaking_time_seconds = sum(speaker_times.values()) / 1000  # 밀리초에서 초로 변환
        
        # 실제 회의 전체 시간 계산 (통계용)
        total_meeting_duration_seconds = SpeakerStatsProcessor.calculate_meeting_duration(transcript.utterances)
        
        # 상세한 화자 시간 정보 생성 (클로바 노트 방식: 순수 발언 시간 기준)
        speaker_time_info = SpeakerStatsProcessor.create_speaker_time_info(
            speaker_times, speaker_mapping, total_speaking_time_seconds
        )
        
        # LLM용 구조화된 전사 텍스트 생성
        llm_formatted_transcript = TranscriptionFormatter.create_llm_formatted_transcript(
            transcript.utterances, speaker_mapping
        )
        
        # 상세한 발화 정보 생성
        utterances = TranscriptionFormatter.create_utterances_info(transcript.utterances, speaker_mapping)
        
        return {
            # LLM 모델 최적화된 전사 내용
            "transcript": llm_formatted_transcript,
            "status": ProcessingStatus.SUCCESS.value,
            "timestamp": datetime.now().isoformat(),
            
            # 화자 통계 정보
            "speaker_stats": speaker_time_info,
            "total_duration_seconds": round(total_meeting_duration_seconds, 2),
            "total_speaking_time_seconds": round(total_speaking_time_seconds, 2),
            
            # 프론트엔드용 상세 정보 (타임스탬프 포함)
            "utterances": utterances
        }

    def _save_transcription_result(self, result: Dict[str, Any]) -> None:
        """에러 처리와 함께 전사 결과를 JSON 파일로 저장"""
        try:
            # 디렉토리 생성
            Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime(FILE_TIMESTAMP_FORMAT)
            json_file_path = os.path.join(OUTPUT_DIR, f"transcript_{timestamp}.json")
            
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            logger.info(f"전사 결과 저장 완료: {json_file_path}")
            
        except Exception as e:
            logger.error(f"전사 결과 저장 실패: {e}")


def prepare_speaker_stats(speaker_stats: Optional[Dict]) -> str:
    """화자 통계 텍스트 준비 (기존 함수 유지 - 하위 호환성)"""
    if not speaker_stats:
        return ""
    
    stats_text = "\n화자별 발언 점유율:\n"
    for speaker_name, stats in speaker_stats.items():
        stats_text += f"- {speaker_name}: {stats['percentage']}% ({stats['formatted_time']})\n"
    return stats_text