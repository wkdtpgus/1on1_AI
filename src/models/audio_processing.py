"""
오디오 녹음 및 전사 통합 모듈
AudioRecorder: 실시간 오디오 녹음
STTProcessor: AssemblyAI를 사용한 Speech-to-Text 처리
"""

import assemblyai as aai
import os
import threading
import queue
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import sounddevice as sd
import soundfile as sf

# Import config settings
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


class AudioRecorder:
    """오디오 녹음을 담당하는 클래스"""
    
    def __init__(self):
        self.sample_rate = AUDIO_SAMPLE_RATE
        self.channels = AUDIO_CHANNELS
        self.chunk_size = AUDIO_CHUNK_SIZE
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recorded_frames = []
        
        # 디렉토리 생성
        Path(TEMP_AUDIO_DIR).mkdir(parents=True, exist_ok=True)
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        
    def _audio_callback(self, indata, frames, time_info, status):
        """오디오 스트림 콜백 함수"""
        if self.is_recording:
            self.audio_queue.put(indata.copy())
    
    def start_recording(self) -> bool:
        """녹음 시작"""
        try:
            self.is_recording = True
            self.recorded_frames = []
            self.audio_queue = queue.Queue()
            
            # 오디오 스트림 시작
            self.stream = sd.InputStream(
                callback=self._audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                dtype=AUDIO_FORMAT
            )
            self.stream.start()
            
            # 녹음 스레드 시작
            self.recording_thread = threading.Thread(target=self._recording_worker)
            self.recording_thread.start()
            
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to start recording: {str(e)}")
            self.is_recording = False
            return False
    
    def _recording_worker(self):
        """녹음 워커 스레드"""
        while self.is_recording:
            try:
                # 타임아웃으로 큐에서 데이터 가져오기
                audio_chunk = self.audio_queue.get(timeout=0.1)
                self.recorded_frames.append(audio_chunk)
            except queue.Empty:
                continue
    
    def stop_recording(self) -> Optional[str]:
        """녹음 중지 및 파일 저장"""
        if not self.is_recording:
            return None
            
        self.is_recording = False
        
        # 스트림 정지
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        # 녹음 스레드 종료 대기
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join(timeout=2.0)
        
        # 오디오 데이터가 있는지 확인
        if not self.recorded_frames:
            return None
        
        # 오디오 데이터 결합
        audio_data = np.concatenate(self.recorded_frames, axis=0)
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join(TEMP_AUDIO_DIR, filename)
        
        try:
            sf.write(filepath, audio_data, self.sample_rate)
            return filepath
        except Exception as e:
            print(f"ERROR: Failed to save recording file: {str(e)}")
            return None


class STTProcessor:
    """AssemblyAI를 사용한 Speech-to-Text 처리 및 JSON 구조화 클래스"""

    def __init__(self, api_key: Optional[str] = None):
        # API 키 설정
        self.api_key = api_key or ASSEMBLYAI_API_KEY or os.getenv("ASSEMBLYAI_API_KEY")
        if not self.api_key:
            raise ValueError("AssemblyAI API key is required")
        
        # AssemblyAI 설정
        aai.settings.api_key = self.api_key

    def transcribe_audio(self, audio_file: str, participants_info: Optional[Dict[str, Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        AssemblyAI를 사용하여 오디오 파일을 텍스트로 변환하고,
        지정된 JSON 구조로 포맷팅합니다.
        
        :param audio_file: 처리할 오디오 파일 경로
        :param participants_info: 화자 정보를 담은 딕셔너리 (예: {"A": {"name": "김준희", "role": "팀원"}})
        :return: 구조화된 전사 결과 딕셔너리
        """
        if not os.path.exists(audio_file):
            return {
                "status": "error",
                "message": f"오디오 파일을 찾을 수 없습니다: {audio_file}",
                "timestamp": datetime.now().isoformat()
            }

        try:
            config = aai.TranscriptionConfig(
                speech_model=getattr(aai.SpeechModel, ASSEMBLYAI_SPEECH_MODEL, aai.SpeechModel.best),
                language_code=ASSEMBLYAI_LANGUAGE,
                punctuate=ASSEMBLYAI_PUNCTUATE,
                format_text=ASSEMBLYAI_FORMAT_TEXT,
                disfluencies=ASSEMBLYAI_DISFLUENCIES,
                speaker_labels=ASSEMBLYAI_SPEAKER_LABELS,
                language_detection=ASSEMBLYAI_LANGUAGE_DETECTION,
                speakers_expected=ASSEMBLYAI_SPEAKERS_EXPECTED
            )

            if ASSEMBLYAI_WORD_BOOST:
                config.word_boost = ASSEMBLYAI_WORD_BOOST
                config.boost_param = ASSEMBLYAI_BOOST_PARAM

            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(audio_file)

            # 전사 상태 확인 (기다리는 로직 추가)
            while transcript.status not in [aai.TranscriptStatus.completed, aai.TranscriptStatus.error]:
                time.sleep(5)
                transcript = transcript.get()

            if transcript.status == aai.TranscriptStatus.error:
                return {
                    "status": "error",
                    "message": f"전사 실패: {transcript.error}",
                    "audio_file": audio_file,
                    "timestamp": datetime.now().isoformat()
                }

            # 결과를 새로운 JSON 구조로 포맷팅
            formatted_result = self._format_transcription_result(transcript, audio_file, participants_info)

            # 결과 저장
            self._save_transcription_result(formatted_result)

            return formatted_result

        except Exception as e:
            print(f"❌ 전사 오류: {e}")
            return {
                "status": "error",
                "message": f"전사 처리 중 오류 발생: {str(e)}",
                "audio_file": audio_file,
                "timestamp": datetime.now().isoformat()
            }

    def _format_transcription_result(self, transcript: aai.Transcript, audio_file: str, participants_info: Optional[Dict[str, Dict[str, str]]]) -> Dict[str, Any]:
        """AssemblyAI 전사 결과를 간단한 화자별 발언 형식으로 포맷팅합니다."""
        
        if not hasattr(transcript, 'utterances') or not transcript.utterances:
            return {
                "transcript": "전사된 내용이 없습니다.",
                "status": "success_but_no_utterances",
                "timestamp": datetime.now().isoformat()
            }

        # 화자 매핑 생성 (A, B, C... 또는 실제 이름 사용)
        unique_labels = sorted(list(set(u.speaker for u in transcript.utterances)))
        speaker_mapping = {}
        
        for i, label in enumerate(unique_labels):
            # participants_info가 있으면 실제 이름 사용, 없으면 A, B, C...
            if participants_info and label in participants_info:
                speaker_name = participants_info[label]["name"]
            else:
                speaker_name = chr(65 + i)  # A, B, C...
            speaker_mapping[label] = speaker_name

        # 화자별 발언을 하나의 문자열로 조합
        transcript_lines = []
        for utterance in transcript.utterances:
            speaker_name = speaker_mapping.get(utterance.speaker, "참석자")
            transcript_lines.append(f"{speaker_name}: {utterance.text}")

        return {
            "transcript": "\n".join(transcript_lines),
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }

    def _save_transcription_result(self, result: Dict[str, Any]):
        """간소화된 전사 결과를 JSON 파일로 저장합니다."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON 파일 저장 (간단한 형식)
            json_file_path = os.path.join(OUTPUT_DIR, f"transcript_{timestamp}.json")
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 전사 결과 저장: {json_file_path}")

        except Exception as e:
            print(f"❌ 결과 저장 오류: {e}")


class AudioProcessor:
    """오디오 녹음과 전사를 통합 처리하는 클래스"""
    
    def __init__(self, assemblyai_api_key: Optional[str] = None):
        """
        AudioProcessor 초기화
        
        Args:
            assemblyai_api_key: AssemblyAI API 키
        """
        self.recorder = AudioRecorder()
        self.stt_processor = STTProcessor(api_key=assemblyai_api_key)
    
    def start_recording(self) -> bool:
        """녹음 시작"""
        return self.recorder.start_recording()
    
    def stop_recording_and_transcribe(self, participants_info: Optional[Dict[str, Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        녹음 중지하고 전사 수행
        
        Args:
            participants_info: 화자 정보
            
        Returns:
            전사 결과
        """
        # 녹음 중지하고 파일 경로 가져오기
        audio_file = self.recorder.stop_recording()
        
        if not audio_file:
            return {
                "status": "error",
                "message": "녹음된 파일이 없습니다.",
                "timestamp": datetime.now().isoformat()
            }
        
        print(f"🎵 녹음 완료: {audio_file}")
        
        # 전사 수행
        print("📝 전사 시작...")
        transcription_result = self.stt_processor.transcribe_audio(audio_file, participants_info)
        
        # 임시 파일 정리 (선택적)
        try:
            os.remove(audio_file)
            print(f"🗑️ 임시 파일 정리: {audio_file}")
        except Exception as e:
            print(f"⚠️ 임시 파일 정리 실패: {e}")
        
        return transcription_result
    
    def transcribe_existing_file(self, audio_file: str, participants_info: Optional[Dict[str, Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        기존 오디오 파일 전사
        
        Args:
            audio_file: 오디오 파일 경로
            participants_info: 화자 정보
            
        Returns:
            전사 결과
        """
        return self.stt_processor.transcribe_audio(audio_file, participants_info)