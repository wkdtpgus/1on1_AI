"""
녹음 관련 모델 및 기능
"""

import os
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import Optional
import numpy as np
import sounddevice as sd
import soundfile as sf

# Import config settings
from src.config.config import (
    AUDIO_SAMPLE_RATE,
    AUDIO_CHANNELS,
    AUDIO_CHUNK_SIZE,
    AUDIO_FORMAT,
    TEMP_AUDIO_DIR,
    OUTPUT_DIR
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
            return None