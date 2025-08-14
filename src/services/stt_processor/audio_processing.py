# 1. 표준 라이브러리
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# 2. 서드파티 라이브러리
import assemblyai as aai

# 3. 내부 모듈
from src.config.stt_config import OUTPUT_DIR
from src.models.assembly import AssemblyAIProcessor
from src.services.meeting_analyze.speaker_stats import SpeakerStatsProcessor
from src.utils.transcription_formatter import TranscriptionFormatter, ProcessingStatus

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audio_processing")

# 설정과 상수들
FILE_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


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
            return self._handle_transcription_error(
                f"오디오 파일을 찾을 수 없습니다: {audio_file}",
                audio_file
            )

        try:
            # 전사 수행
            transcript = self.assembly_processor.execute_transcription(audio_file, expected_speakers)
            
            if not transcript:
                return self._handle_transcription_error("전사 실패", audio_file)
            
            # 결과 포맷팅 및 저장
            formatted_result = self._format_transcription_result(transcript, audio_file, participants_info)
            self._save_transcription_result(formatted_result)
            
            logger.info("전사가 성공적으로 완료되었습니다")
            return formatted_result

        except Exception as e:
            return self._handle_transcription_error(str(e), audio_file, include_traceback=True)
    
    def _handle_transcription_error(self, message: str, audio_file: str = "", 
                                   include_traceback: bool = False) -> Dict[str, Any]:
        """전사 오류 처리"""
        logger.error(message)
        
        if include_traceback:
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"상세 오류:\n{error_detail}")
            return {
                "error": "전사 오류",
                "message": message,
                "detail": error_detail,
                "audio_file": audio_file
            }
        
        return TranscriptionFormatter.create_error_result(message, audio_file)
    
    def _create_gemini_formatted_transcript(
        self, 
        utterances: List[Any],
        speaker_mapping: Dict[str, str]
    ) -> str:
        """Gemini 모델에 최적화된 전사 텍스트 형식 생성"""
        # TranscriptionFormatter는 speaker_mapping이 필요한 포맷팅만 담당
        return TranscriptionFormatter.create_gemini_formatted_transcript(utterances, speaker_mapping)

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
        
        # Gemini용 구조화된 전사 텍스트 생성
        gemini_formatted_transcript = self._create_gemini_formatted_transcript(
            transcript.utterances, speaker_mapping
        )
        
        # 상세한 발화 정보 생성
        utterances = TranscriptionFormatter.create_utterances_info(transcript.utterances, speaker_mapping)
        
        return {
            # Gemini 모델 최적화된 전사 내용
            "transcript": gemini_formatted_transcript,
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


class AudioProcessor:
    """오디오 파일 전사 처리를 위한 서버용 인터페이스"""
    
    def __init__(self, assemblyai_api_key: Optional[str] = None) -> None:
        """전사 기능으로 AudioProcessor 초기화
        
        Args:
            assemblyai_api_key: 전사 서비스를 위한 AssemblyAI API 키
        """
        try:
            # STT 처리 초기화
            self.stt_processor = STTProcessor(api_key=assemblyai_api_key)
            logger.debug("AudioProcessor가 성공적으로 초기화되었습니다")
        except Exception as e:
            logger.error(f"AudioProcessor 초기화 실패: {e}")
            raise

    def transcribe_existing_file(
        self, 
        audio_file: str, 
        participants_info: Optional[Dict[str, Dict[str, str]]] = None,
        expected_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """기존 오디오 파일 전사
        
        Args:
            audio_file: 오디오 파일 경로
            participants_info: 화자 정보 딕셔너리
            expected_speakers: 더 나은 전사를 위한 예상 화자 수
            
        Returns:
            전사 결과 딕셔너리
        """
        logger.debug(f"기존 파일 전사: {audio_file}")
        return self.stt_processor.transcribe_audio(audio_file, participants_info, expected_speakers)

    def _cleanup_temp_file(self, audio_file: str) -> None:
        """에러 처리와 함께 임시 오디오 파일 정리"""
        try:
            if os.path.exists(audio_file):
                os.remove(audio_file)
                logger.info(f"임시 파일 정리 완료: {audio_file}")
        except Exception as e:
            logger.warning(f"임시 파일 {audio_file} 정리 실패: {e}")