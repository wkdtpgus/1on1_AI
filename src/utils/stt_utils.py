"""STT 처리 관련 유틸리티 함수들"""

import logging
import time
from typing import Dict, List, Any
import assemblyai as aai

logger = logging.getLogger("stt_utils")


def wait_for_transcript(
    transcriber: aai.Transcriber,
    transcript: aai.Transcript,
    max_wait_time: int = 900,
    check_interval: int = 10
) -> aai.Transcript:
    """
    AssemblyAI 전사 상태 확인 및 대기
    
    Args:
        transcriber: AssemblyAI transcriber 객체
        transcript: 전사 객체
        max_wait_time: 최대 대기 시간 (초)
        check_interval: 상태 확인 간격 (초)
        
    Returns:
        완료된 transcript 객체
        
    Raises:
        TimeoutError: 처리 시간 초과
        Exception: STT 처리 실패
    """
    elapsed_time = 0
    
    while transcript.status in [aai.TranscriptStatus.processing, aai.TranscriptStatus.queued]:
        if elapsed_time >= max_wait_time:
            raise TimeoutError(f"STT 처리 시간 초과 ({max_wait_time}초)")
        
        logger.info(f"🔄 STT 처리 중... ({elapsed_time}초 경과)")
        time.sleep(check_interval)
        elapsed_time += check_interval
        transcript = transcriber.get_transcript(transcript.id)
    
    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"STT 처리 실패: {transcript.error}")
    
    return transcript


def process_transcript(transcript: aai.Transcript) -> Dict[str, Any]:
    """
    AssemblyAI transcript를 처리하여 필요한 데이터 추출
    
    Args:
        transcript: AssemblyAI transcript 객체
        
    Returns:
        처리된 데이터 딕셔너리 (transcript_dict, speaker_stats_percent)
    """
    # LLM용 포맷된 transcript (speaker, text만 포함)
    formatted_transcript = []
    if transcript.utterances:
        formatted_transcript = [
            {
                "speaker": utterance.speaker,
                "text": utterance.text
            }
            for utterance in transcript.utterances
        ]
    
    # 화자별 발화 시간 비율 계산
    speaker_stats_percent = {}
    if transcript.utterances:
        speaker_stats = {}
        total_duration_ms = 0
        
        # 화자별 발화 시간 계산
        for utterance in transcript.utterances:
            speaker = utterance.speaker or 'Unknown'
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {'duration': 0}
            duration_ms = (utterance.end or 0) - (utterance.start or 0)
            speaker_stats[speaker]['duration'] += duration_ms
            total_duration_ms += duration_ms
        
        # 퍼센트 계산
        for speaker_name, stats in speaker_stats.items():
            duration_ms = stats.get('duration', 0)
            percentage = round((duration_ms / total_duration_ms) * 100, 1) if total_duration_ms > 0 else 0
            speaker_stats_percent[speaker_name] = percentage
    
    # 결과 구조화
    return {
        "transcript_dict": {
            "utterances": formatted_transcript,
            "total_duration": transcript.audio_duration  # 비용 계산용
        },
        "speaker_stats_percent": speaker_stats_percent
    }