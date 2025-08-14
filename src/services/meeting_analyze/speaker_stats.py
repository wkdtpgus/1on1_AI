import logging
from typing import Optional, Dict, List, Any, Union

# 로깅 설정
logger = logging.getLogger("speaker_stats")

# 상수
TIME_DISPLAY_FORMAT = "{minutes}분 {seconds}초"
SPEAKER_ALPHABET_START = 65  # ASCII 'A'


class SpeakerStatsProcessor:
    """화자 통계 처리를 담당하는 클래스"""
    
    @staticmethod
    def create_speaker_mapping(
        unique_labels: List[str], 
        participants_info: Optional[Dict[str, Dict[str, str]]]
    ) -> Dict[str, str]:
        """화자 라벨에서 표시 이름으로의 매핑 생성
        
        Args:
            unique_labels: 고유한 화자 라벨 리스트
            participants_info: 참가자 정보 딕셔너리
            
        Returns:
            화자 라벨과 표시 이름의 매핑 딕셔너리
        """
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
        """각 화자의 총 발언 시간을 밀리초 단위로 계산
        
        Args:
            utterances: 발화 리스트
            
        Returns:
            화자별 발언 시간(밀리초) 딕셔너리
        """
        speaker_times = {}
        
        for utterance in utterances:
            speaker = utterance.speaker
            duration = utterance.end - utterance.start  # 밀리초
            
            speaker_times[speaker] = speaker_times.get(speaker, 0) + duration
            
        return speaker_times
    
    @staticmethod
    def format_time_display(seconds: float) -> str:
        """초를 MM분 SS초 표시 형식으로 포맷팅
        
        Args:
            seconds: 시간(초)
            
        Returns:
            포맷팅된 시간 문자열
        """
        minutes = int(seconds // 60)
        seconds_remainder = int(seconds % 60)
        return TIME_DISPLAY_FORMAT.format(minutes=minutes, seconds=seconds_remainder)
    
    @staticmethod
    def create_speaker_time_info(
        speaker_times: Dict[str, float], 
        speaker_mapping: Dict[str, str],
        total_time_seconds: float
    ) -> Dict[str, Dict[str, Union[float, str]]]:
        """상세한 화자 시간 정보 생성
        
        Args:
            speaker_times: 화자별 발언 시간(밀리초)
            speaker_mapping: 화자 라벨-이름 매핑
            total_time_seconds: 전체 발언 시간(초)
            
        Returns:
            화자별 상세 시간 정보 딕셔너리
        """
        speaker_time_info = {}
        
        for speaker, time_ms in speaker_times.items():
            time_seconds = time_ms / 1000
            percentage = (time_seconds / total_time_seconds * 100) if total_time_seconds > 0 else 0
            speaker_name = speaker_mapping.get(speaker, "참석자")
            
            speaker_time_info[speaker_name] = {
                "total_seconds": round(time_seconds, 2),
                "formatted_time": SpeakerStatsProcessor.format_time_display(time_seconds),
                "percentage": round(percentage, 1)
            }
            
        return speaker_time_info
    
    @staticmethod
    def calculate_meeting_duration(utterances: List[Any]) -> float:
        """실제 회의 전체 시간 계산
        
        Args:
            utterances: 발화 리스트
            
        Returns:
            회의 전체 시간(초)
        """
        if not utterances:
            return 0
            
        meeting_start = min(u.start for u in utterances)
        meeting_end = max(u.end for u in utterances)
        return (meeting_end - meeting_start) / 1000  # 밀리초에서 초로


def prepare_speaker_stats(speaker_stats: Optional[Dict]) -> str:
    """화자 통계 텍스트 준비 (기존 함수 유지 - 하위 호환성)
    
    Args:
        speaker_stats: 화자별 통계 정보 딕셔너리
        
    Returns:
        포맷팅된 화자 통계 텍스트
    """
    if not speaker_stats:
        return ""
    
    stats_text = "\n화자별 발언 점유율:\n"
    for speaker_name, stats in speaker_stats.items():
        stats_text += f"- {speaker_name}: {stats['percentage']}% ({stats['formatted_time']})\n"
    return stats_text