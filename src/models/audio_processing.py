"""오디오 녹음 및 전사 통합 모듈

이 모듈은 오디오 녹음과 음성-텍스트 변환 처리를 위한 포괄적인 솔루션을 제공합니다.

클래스들:
    AudioRecorder: 적절한 리소스 관리와 함께 실시간 오디오 녹음 처리
    TranscriptionFormatter: 화자 분석과 함께 전사 결과 포맷팅
    STTProcessor: 에러 처리가 포함된 AssemblyAI 기반 음성-텍스트 처리
    AudioProcessor: 녹음과 전사를 통합한 고수준 인터페이스
    
상수들:
    녹음 설정, 타이밍, 그리고 포맷팅 상수들
"""

import assemblyai as aai
import os
import threading
import queue
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
import numpy as np
import sounddevice as sd
import soundfile as sf
from dataclasses import dataclass
from enum import Enum

# 설정 값들 가져오기
from src.config.config import (
    # 오디오 관련 설정
    AUDIO_SAMPLE_RATE,
    AUDIO_CHANNELS,
    AUDIO_CHUNK_SIZE,
    AUDIO_FORMAT,
    TEMP_AUDIO_DIR,
    OUTPUT_DIR,
    # AssemblyAI 설정
    ASSEMBLYAI_API_KEY,
    ASSEMBLYAI_SPEECH_MODEL,
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 상수들
class ProcessingStatus(Enum):
    """처리 상태 값들을 위한 열거형"""
    SUCCESS = "success"
    ERROR = "error"
    SUCCESS_NO_UTTERANCES = "success_but_no_utterances"
    PROCESSING = "processing"


# 설정과 상수들
RECORDING_TIMEOUT = 2.0  # 녹음 스레드 종료 대기 시간(초)
QUEUE_TIMEOUT = 0.1  # 오디오 큐 대기 시간(초)
TRANSCRIPT_POLL_INTERVAL = 5  # 전사 상태 확인 간격(초)
FILE_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
ISO_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"
TIME_DISPLAY_FORMAT = "{minutes}분 {seconds}초"
SPEAKER_ALPHABET_START = 65  # ASCII 'A'


@dataclass
class SpeakerInfo:
    """화자 정보를 위한 불변 데이터 클래스"""
    id: str
    name: str
    role: str
    total_seconds: float
    formatted_time: str
    percentage: float


@dataclass 
class UtteranceInfo:
    """발화 정보를 위한 불변 데이터 클래스"""
    speaker: str
    start_time: float
    end_time: float
    duration: float
    text: str
    formatted_start: str


@dataclass
class TranscriptionResult:
    """전사 결과를 위한 불변 데이터 클래스"""
    transcript: str
    status: str
    timestamp: str
    speaker_times: Dict[str, Dict[str, Union[float, str]]]
    total_duration_seconds: float
    utterances: List[Dict[str, Any]]
    participants: List[Dict[str, str]]


class AudioRecorder:
    """적절한 리소스 관리와 에러 처리를 포함한 오디오 녹음 처리"""
    
    def __init__(self) -> None:
        """설정값으로 AudioRecorder 초기화"""
        self.sample_rate: int = AUDIO_SAMPLE_RATE
        self.channels: int = AUDIO_CHANNELS
        self.chunk_size: int = AUDIO_CHUNK_SIZE
        self.is_recording: bool = False
        self.audio_queue: queue.Queue = queue.Queue()
        self.recorded_frames: List[np.ndarray] = []
        self.stream: Optional[sd.InputStream] = None
        self.recording_thread: Optional[threading.Thread] = None
        
        # 필요한 디렉토리 생성
        self._ensure_directories_exist()
        
        logger.info(f"AudioRecorder 초기화 완료: {self.sample_rate}Hz, {self.channels} 채널")
    
    def _ensure_directories_exist(self) -> None:
        """필요한 디렉토리들이 존재하는지 확인"""
        try:
            Path(TEMP_AUDIO_DIR).mkdir(parents=True, exist_ok=True)
            Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
            logger.debug(f"디렉토리 확인 완료: {TEMP_AUDIO_DIR}, {OUTPUT_DIR}")
        except Exception as e:
            logger.error(f"디렉토리 생성 실패: {e}")
            raise
    
    def _audio_callback(self, indata: np.ndarray, frames: int, time_info: Any, status: sd.CallbackFlags) -> None:
        """에러 처리를 포함한 오디오 스트림 콜백 함수"""
        if status:
            logger.warning(f"오디오 콜백 상태: {status}")
        
        if self.is_recording:
            try:
                self.audio_queue.put(indata.copy())
            except Exception as e:
                logger.error(f"오디오 콜백 오류: {e}")
                self.is_recording = False
    
    def start_recording(self) -> bool:
        """적절한 에러 처리를 포함하여 오디오 녹음 시작"""
        if self.is_recording:
            logger.warning("이미 녹음이 진행 중입니다")
            return False
            
        try:
            self._reset_recording_state()
            
            # 오디오 스트림 초기화
            self.stream = sd.InputStream(
                callback=self._audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                dtype=AUDIO_FORMAT
            )
            self.stream.start()
            
            # 녹음 워커 스레드 시작
            self.recording_thread = threading.Thread(
                target=self._recording_worker, 
                name="AudioRecordingWorker"
            )
            self.recording_thread.start()
            
            self.is_recording = True
            logger.info("오디오 녹음이 성공적으로 시작되었습니다")
            return True
            
        except Exception as e:
            logger.error(f"녹음 시작 실패: {e}")
            self._cleanup_recording_resources()
            return False
    
    def _reset_recording_state(self) -> None:
        """새 녹음을 위해 녹음 상태 리셋"""
        self.recorded_frames = []
        self.audio_queue = queue.Queue()
        self.is_recording = False
    
    def _recording_worker(self) -> None:
        """적절한 에러 처리를 포함한 녹음 워커 스레드"""
        logger.debug("녹음 워커 스레드가 시작되었습니다")
        
        while self.is_recording:
            try:
                # 타임아웃과 함께 오디오 청크 가져오기
                audio_chunk = self.audio_queue.get(timeout=QUEUE_TIMEOUT)
                self.recorded_frames.append(audio_chunk)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"녹음 워커에서 오류 발생: {e}")
                break
                
        logger.debug("녹음 워커 스레드가 종료되었습니다")
    
    def stop_recording(self) -> Optional[str]:
        """적절한 정리와 함께 녹음 중지 및 오디오 파일 저장"""
        if not self.is_recording:
            logger.warning("진행 중인 녹음이 없습니다")
            return None
            
        logger.info("오디오 녹음을 중지합니다...")
        self.is_recording = False
        
        # 오디오 스트림 중지 및 정리
        self._cleanup_recording_resources()
        
        # 녹음된 데이터가 있는지 확인
        if not self.recorded_frames:
            logger.warning("녹음된 오디오 데이터가 없습니다")
            return None
        
        # 오디오 데이터 결합
        try:
            audio_data = np.concatenate(self.recorded_frames, axis=0)
            logger.info(f"{len(self.recorded_frames)}개의 오디오 프레임 결합 완료")
        except Exception as e:
            logger.error(f"오디오 데이터 결합 실패: {e}")
            return None
        
        # 오디오 파일 저장
        return self._save_audio_file(audio_data)
    
    def _cleanup_recording_resources(self) -> None:
        """녹음 리소스를 안전하게 정리"""
        # 오디오 스트림 중지
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
                logger.debug("오디오 스트림이 중지되고 닫혔습니다")
            except Exception as e:
                logger.error(f"오디오 스트림 중지 오류: {e}")
            finally:
                self.stream = None
        
        # 녹음 스레드가 종료될 때까지 대기
        if self.recording_thread is not None:
            try:
                self.recording_thread.join(timeout=RECORDING_TIMEOUT)
                if self.recording_thread.is_alive():
                    logger.warning("녹음 스레드가 타임아웃 내에 종료되지 않았습니다")
                logger.debug("녹음 스레드 종료 대기 완료")
            except Exception as e:
                logger.error(f"녹음 스레드 종료 대기 오류: {e}")
            finally:
                self.recording_thread = None
    
    def _save_audio_file(self, audio_data: np.ndarray) -> Optional[str]:
        """에러 처리와 함께 오디오 데이터를 파일로 저장"""
        timestamp = datetime.now().strftime(FILE_TIMESTAMP_FORMAT)
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join(TEMP_AUDIO_DIR, filename)
        
        try:
            sf.write(filepath, audio_data, self.sample_rate)
            logger.info(f"오디오 파일 저장 완료: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"오디오 파일 저장 실패: {e}")
            return None


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
        """초를 MM분 SS초 표시 형식으로 포매팅"""
        minutes = int(seconds // 60)
        seconds_remainder = int(seconds % 60)
        return TIME_DISPLAY_FORMAT.format(minutes=minutes, seconds=seconds_remainder)
    
    @staticmethod
    def format_timestamp_display(seconds: float) -> str:
        """초를 MM:SS 타임스탬프 형식으로 포매팅"""
        minutes = int(seconds // 60)
        seconds_remainder = int(seconds % 60)
        return f"{minutes:02d}:{seconds_remainder:02d}"
    
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
    def create_participants_info(
        speaker_mapping: Dict[str, str], 
        participants_info: Optional[Dict[str, Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """참석자 정보 리스트 생성"""
        participants = []
        
        for label, speaker_name in speaker_mapping.items():
            role = "참석자"
            if participants_info and label in participants_info:
                role = participants_info[label].get("role", "참석자")
            
            participants.append({
                "id": label,
                "name": speaker_name,
                "role": role
            })
            
        return participants
    
    @staticmethod
    def log_speaker_analysis(speaker_time_info: Dict[str, Dict[str, Union[float, str]]], total_time_seconds: float) -> None:
        """화자 시간 분석을 콘솔에 로그 출력"""
        logger.info("\n📊 화자별 발언 시간 분석:")
        logger.info("-" * 40)
        
        for speaker_name, info in speaker_time_info.items():
            logger.info(
                f"{speaker_name}: {info['formatted_time']} ({info['percentage']}%)"
            )
        
        total_display = TranscriptionFormatter.format_time_display(total_time_seconds)
        logger.info(f"전체 발언 시간: {total_display}")
        logger.info("-" * 40)


class STTProcessor:
    """포괄적인 에러 처리를 포함한 AssemblyAI 기반 음성-텍스트 처리"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """API 키 검증과 함께 STTProcessor 초기화"""
        self.api_key = self._resolve_api_key(api_key)
        self._configure_assemblyai()
        
        logger.info("STTProcessor가 성공적으로 초기화되었습니다")
    
    def _resolve_api_key(self, api_key: Optional[str]) -> str:
        """검증과 함께 여러 소스에서 API 키 해결"""
        resolved_key = api_key or ASSEMBLYAI_API_KEY or os.getenv("ASSEMBLYAI_API_KEY")
        
        if not resolved_key:
            raise ValueError(
                "AssemblyAI API key is required. Provide via parameter, "
                "config.py, or ASSEMBLYAI_API_KEY environment variable."
            )
            
        return resolved_key
    
    def _configure_assemblyai(self) -> None:
        """AssemblyAI 설정 구성"""
        try:
            aai.settings.api_key = self.api_key
            logger.debug("AssemblyAI가 성공적으로 구성되었습니다")
        except Exception as e:
            logger.error(f"AssemblyAI 구성 실패: {e}")
            raise

    def transcribe_audio(
        self, 
        audio_file: str, 
        participants_info: Optional[Dict[str, Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using AssemblyAI and format results
        
        Args:
            audio_file: Path to audio file to process
            participants_info: Speaker information dict (e.g. {"A": {"name": "김준희", "role": "팀원"}})
            
        Returns:
            Structured transcription result dictionary
        """
        logger.info(f"전사 시작: {audio_file}")
        
        # 입력 파일 검증
        if not os.path.exists(audio_file):
            error_msg = f"Audio file not found: {audio_file}"
            logger.error(error_msg)
            return TranscriptionFormatter.create_error_result(error_msg, audio_file)

        try:
            # 전사 구성 생성
            config = self._create_transcription_config()
            
            # 전사 수행
            transcript = self._perform_transcription(audio_file, config)
            
            if transcript is None:
                error_msg = "Transcription failed"
                logger.error(error_msg)
                return TranscriptionFormatter.create_error_result(error_msg, audio_file)
            
            # 전사 오류 확인
            if transcript.status == aai.TranscriptStatus.error:
                error_msg = f"Transcription failed: {transcript.error}"
                logger.error(error_msg)
                return TranscriptionFormatter.create_error_result(error_msg, audio_file)

            # 결과 포매팅
            formatted_result = self._format_transcription_result(transcript, audio_file, participants_info)

            # 결과 저장
            self._save_transcription_result(formatted_result)
            
            logger.info("전사가 성공적으로 완료되었습니다")
            return formatted_result

        except Exception as e:
            error_msg = f"Transcription processing error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return TranscriptionFormatter.create_error_result(error_msg, audio_file)
    
    def _create_gemini_formatted_transcript(
        self, 
        utterances: List[Any],
        speaker_mapping: Dict[str, str], 
        speaker_time_info: Dict[str, Dict[str, Union[float, str]]],
        total_time_seconds: float,
        participants_info: Optional[Dict[str, Dict[str, str]]] = None
    ) -> str:
        """Gemini 모델에 최적화된 전사 텍스트 형식 생성"""
        lines = []
        
        # 명확한 구분자로 시작
        lines.append("## 1:1 회의 전사 내용")
        lines.append("")
        
        # 참석자 정보만 포함 (역할만 표시)
        if participants_info:
            lines.append("### 참석자 정보")
            for speaker_name in speaker_time_info.keys():
                role_info = ""
                for label, info in participants_info.items():
                    if info.get("name") == speaker_name:
                        role_info = f": {info.get('role', '참석자')}"
                        break
                lines.append(f"- **{speaker_name}{role_info}**")
            lines.append("")
        
        # 대화 내용
        lines.append("### 대화 내용")
        for utterance in utterances:
            speaker_name = speaker_mapping.get(utterance.speaker, '참석자')
            start_time = TranscriptionFormatter.format_timestamp_display(utterance.start / 1000)
            # 간소화된 형식: [타임스탬프] 화자명: 내용
            lines.append(f"[{start_time}] {speaker_name}: {utterance.text}")
        
        return "\n".join(lines)
    
    def _create_transcription_config(self) -> aai.TranscriptionConfig:
        """AssemblyAI 전사 구성 생성"""
        try:
            config = aai.TranscriptionConfig(
                language_code=ASSEMBLYAI_LANGUAGE,
                punctuate=ASSEMBLYAI_PUNCTUATE,
                format_text=ASSEMBLYAI_FORMAT_TEXT,
                disfluencies=ASSEMBLYAI_DISFLUENCIES,
                speaker_labels=ASSEMBLYAI_SPEAKER_LABELS,
                language_detection=ASSEMBLYAI_LANGUAGE_DETECTION,
                speakers_expected=ASSEMBLYAI_SPEAKERS_EXPECTED
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
    
    def _perform_transcription(self, audio_file: str, config: aai.TranscriptionConfig) -> Optional[aai.Transcript]:
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

    def _format_transcription_result(
        self, 
        transcript: aai.Transcript, 
        audio_file: str, 
        participants_info: Optional[Dict[str, Dict[str, str]]]
    ) -> Dict[str, Any]:
        """AssemblyAI 전사 결과를 구조화된 JSON으로 포매팅"""
        
        # 발화가 없는 경우 처리
        if not hasattr(transcript, 'utterances') or not transcript.utterances:
            logger.warning("전사에서 발화를 찾을 수 없습니다")
            return {
                "transcript": "전사된 내용이 없습니다.",
                "status": ProcessingStatus.SUCCESS_NO_UTTERANCES.value,
                "timestamp": datetime.now().isoformat(),
                "speaker_times": {},
                "utterances": [],
                "participants": []
            }

        # 고유한 화자들을 추출하고 매핑 생성
        unique_labels = list(set(u.speaker for u in transcript.utterances))
        speaker_mapping = TranscriptionFormatter.create_speaker_mapping(unique_labels, participants_info)
        
        # 화자 시간 계산
        speaker_times = TranscriptionFormatter.calculate_speaker_times(transcript.utterances)
        
        # 클로바 노트 방식: 순수 발언 시간 합계를 기준으로 점유율 계산 (침묵 구간 제외)
        total_speaking_time_seconds = sum(speaker_times.values()) / 1000  # 밀리초에서 초로 변환
        
        # 실제 회의 전체 시간 계산 (통계용)
        if transcript.utterances:
            meeting_start = min(u.start for u in transcript.utterances)
            meeting_end = max(u.end for u in transcript.utterances)
            total_meeting_duration_seconds = (meeting_end - meeting_start) / 1000  # 밀리초에서 초로
        else:
            total_meeting_duration_seconds = 0
        
        # 상세한 화자 시간 정보 생성 (클로바 노트 방식: 순수 발언 시간 기준)
        speaker_time_info = TranscriptionFormatter.create_speaker_time_info(
            speaker_times, speaker_mapping, total_speaking_time_seconds
        )
        
        # 화자 분석 로그 출력
        TranscriptionFormatter.log_speaker_analysis(speaker_time_info, total_speaking_time_seconds)
        
        # Gemini용 구조화된 전사 텍스트 생성
        gemini_formatted_transcript = self._create_gemini_formatted_transcript(
            transcript.utterances, speaker_mapping, speaker_time_info, total_speaking_time_seconds, participants_info
        )
        
        # 상세한 발화 정보 생성
        utterances = TranscriptionFormatter.create_utterances_info(transcript.utterances, speaker_mapping)
        
        # 참석자 정보 생성
        participants = TranscriptionFormatter.create_participants_info(speaker_mapping, participants_info)

        return {
            # Gemini 모델 최적화된 전사 내용
            "transcript": gemini_formatted_transcript,
            "status": ProcessingStatus.SUCCESS.value,
            "timestamp": datetime.now().isoformat(),
            
            # 화자 통계 정보
            "speaker_times": speaker_time_info,
            "total_duration_seconds": round(total_meeting_duration_seconds, 2),
            "total_speaking_time_seconds": round(total_speaking_time_seconds, 2),
            
            # 프론트엔드용 상세 정보 (타임스탬프 포함)
            "utterances": utterances,
            "participants": participants
        }

    def _save_transcription_result(self, result: Dict[str, Any]) -> None:
        """에러 처리와 함께 전사 결과를 JSON 파일로 저장"""
        try:
            timestamp = datetime.now().strftime(FILE_TIMESTAMP_FORMAT)
            json_file_path = os.path.join(OUTPUT_DIR, f"transcript_{timestamp}.json")
            
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            logger.info(f"💾 Transcription result saved: {json_file_path}")
            
        except Exception as e:
            logger.error(f"전사 결과 저장 실패: {e}")


class AudioProcessor:
    """오디오 녹음과 전사 처리를 통합한 고수준 인터페이스"""
    
    def __init__(self, assemblyai_api_key: Optional[str] = None) -> None:
        """
        Initialize AudioProcessor with recording and transcription capabilities
        
        Args:
            assemblyai_api_key: AssemblyAI API key for transcription service
        """
        try:
            self.recorder = AudioRecorder()
            self.stt_processor = STTProcessor(api_key=assemblyai_api_key)
            logger.info("AudioProcessor가 성공적으로 초기화되었습니다")
        except Exception as e:
            logger.error(f"AudioProcessor 초기화 실패: {e}")
            raise
    
    def start_recording(self) -> bool:
        """오디오 녹음 시작"""
        logger.info("오디오 녹음을 시작합니다...")
        return self.recorder.start_recording()
    
    def stop_recording_and_transcribe(
        self, 
        participants_info: Optional[Dict[str, Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Stop recording and perform transcription with cleanup
        
        Args:
            participants_info: Speaker information dictionary
            
        Returns:
            Transcription result dictionary
        """
        logger.info("녹음을 중지하고 전사를 시작합니다...")
        
        # 녹음 중지하고 파일 경로 가져오기
        audio_file = self.recorder.stop_recording()
        
        if not audio_file:
            error_msg = "No recorded audio file available"
            logger.warning(error_msg)
            return TranscriptionFormatter.create_error_result(error_msg)
        
        logger.info(f"녹음 완료: {audio_file}")
        
        # 전사 수행
        logger.info("전사 시작...")
        transcription_result = self.stt_processor.transcribe_audio(audio_file, participants_info)
        
        # 임시 파일 정리
        self._cleanup_temp_file(audio_file)
        
        return transcription_result
    
    def _cleanup_temp_file(self, audio_file: str) -> None:
        """에러 처리와 함께 임시 오디오 파일 정리"""
        try:
            os.remove(audio_file)
            logger.info(f"임시 파일 정리 완료: {audio_file}")
        except Exception as e:
            logger.warning(f"임시 파일 {audio_file} 정리 실패: {e}")

    def transcribe_existing_file(
        self, 
        audio_file: str, 
        participants_info: Optional[Dict[str, Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe existing audio file
        
        Args:
            audio_file: Path to audio file
            participants_info: Speaker information dictionary
            
        Returns:
            Transcription result dictionary
        """
        logger.info(f"기존 파일 전사: {audio_file}")
        return self.stt_processor.transcribe_audio(audio_file, participants_info)