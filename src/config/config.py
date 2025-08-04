"""
STT (Speech-to-Text) 설정 관련 내용
- STT 모델 및 오디오 처리 관련 설정을 중앙에서 관리
- 설정 변경 시 이 파일만 수정하면 전체 시스템에 반영됨
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# AssemblyAI 모델 설정
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")  # .env 파일에서 자동 로드
ASSEMBLYAI_SPEECH_MODEL = "best"  # 음성 모델 (best: 최고 정확도, nano: 비용 효율적)
ASSEMBLYAI_LANGUAGE = "ko"  # 기본 언어 설정 (한국어)

# 1on1 미팅 최적화 파라미터
ASSEMBLYAI_PUNCTUATE = True  # 구두점 자동 추가
ASSEMBLYAI_FORMAT_TEXT = True  # 텍스트 포맷팅 (대문자, 숫자 등)
ASSEMBLYAI_DISFLUENCIES = False  # 말더듬, 음성간투사 필터링 (회의에서는 제거)
ASSEMBLYAI_SPEAKER_LABELS = True  # 화자 분리 (2명 회의에 필수)
ASSEMBLYAI_LANGUAGE_DETECTION = False  # 언어 자동 감지 (한국어로 고정)
ASSEMBLYAI_WORD_BOOST = []  # 특정 단어 인식 강화 (회사명, 전문용어 등)
ASSEMBLYAI_BOOST_PARAM = "default"  # 부스트 강도 (low, default, high)

# 화자 분리 강화 설정
ASSEMBLYAI_SPEAKERS_EXPECTED = 2  # 예상 화자 수 (1on1이므로 2명)

# 화자 분리 최적화를 위한 오디오 설정
AUDIO_QUALITY_MODE = "high"  # 오디오 품질 모드 (high, standard)
SPEAKER_SEPARATION_SENSITIVITY = "high"  # 화자 분리 민감도


# 오디오 녹음 설정
AUDIO_SAMPLE_RATE = 16000  # 샘플링 레이트 (Hz)
AUDIO_CHANNELS = 1  # 모노 채널
AUDIO_CHUNK_SIZE = 1024  # 오디오 청크 크기
AUDIO_FORMAT = "float32"  # 오디오 포맷

# 파일 저장 경로
TEMP_AUDIO_DIR = "data/raw_audio"  # 임시 오디오 파일 저장 디렉토리
OUTPUT_DIR = "data/stt_transcripts"  # 출력 파일 저장 디렉토리

# LLM 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # OpenAI API 키
LLM_MODEL = "gpt-4.1"  # 사용할 LLM 모델
LLM_TEMPERATURE = 0.0  # 창의성 설정 (0-1, 낮을수록 일관성 있음)
LLM_MAX_TOKENS = 5000  # 최대 토큰 수

# Google Cloud / Vertex AI 설정
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "False").lower() == "true"

# Vertex AI 모델 설정
VERTEX_AI_MODEL = "gemini-2.5-pro"  # Vertex AI 모델명
VERTEX_AI_TEMPERATURE = 0.0
VERTEX_AI_MAX_TOKENS = 8000