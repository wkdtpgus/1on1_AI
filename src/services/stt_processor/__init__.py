"""
STT (Speech-to-Text) 프로세서 모듈
AssemblyAI를 사용한 음성 인식 기능 제공
"""

from .STT import (
    AudioRecorder,
    STTProcessor
)

__all__ = [
    "AudioRecorder",
    "STTProcessor"
]