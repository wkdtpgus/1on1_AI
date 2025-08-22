import os
from dotenv import load_dotenv

load_dotenv()

# AssemblyAI 모델 설정
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")  # .env 파일에서 자동 로드
ASSEMBLYAI_SPEECH_MODEL = "best"  # 음성 모델 (best: 최고 정확도, nano: 비용 효율적)
ASSEMBLYAI_LANGUAGE = "ko"  # 기본 언어 설정 (한국어)
ASSEMBLYAI_PUNCTUATE = True  # 구두점 자동 추가
ASSEMBLYAI_FORMAT_TEXT = True  # 텍스트 포맷팅 (대문자, 숫자 등)
ASSEMBLYAI_DISFLUENCIES = False  # 말더듬, 음성간투사 필터링 (회의에서는 제거)
ASSEMBLYAI_SPEAKER_LABELS = True  # 화자 분리 (2명 회의에 필수)
ASSEMBLYAI_LANGUAGE_DETECTION = False  # 언어 자동 감지 (한국어로 고정)
ASSEMBLYAI_SPEAKERS_EXPECTED = 2  # 예상 화자 수 (1on1이므로 2명)
AUDIO_QUALITY_MODE = "high"  # 오디오 품질 모드 (high, standard)
SPEAKER_SEPARATION_SENSITIVITY = "high"  # 화자 분리 민감도
AUDIO_SAMPLE_RATE = 16000  # 샘플링 레이트 (Hz)
AUDIO_CHANNELS = 1  # 모노 채널
AUDIO_CHUNK_SIZE = 1024  # 오디오 청크 크기
AUDIO_FORMAT = "float32"  # 오디오 포맷
TEMP_AUDIO_DIR = "data/raw_audio"  # 임시 오디오 파일 저장 디렉토리
OUTPUT_DIR = "data/stt_transcripts"  # 출력 파일 저장 디렉토리
STT_MAX_WAIT_TIME = 900  # STT 최대 대기 시간 (초)
STT_CHECK_INTERVAL = 10  # STT 상태 확인 간격 (초)

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Vertex AI 모델 설정 (STT 분석용)
VERTEX_AI_MODEL = "gemini-2.5-pro"  # Vertex AI 모델명
VERTEX_AI_TEMPERATURE = 0.0
VERTEX_AI_MAX_TOKENS = 13000

# 템플릿 생성용 LLM 설정 (Gemini)
GEMINI_MODEL = "gemini-2.5-flash"  # 기본 모델 설정 (gemini-2.5-flash 사용)
GEMINI_TEMPERATURE = 0.7
GEMINI_THINKING_BUDGET = 0  # 모델의 창의성 제어 (0.0: 일관성, 1.0: 다양성)
GEMINI_MAX_TOKENS = 10000  # 템플릿 생성용 토큰 제한

# 제목 생성용 LLM 설정 (Gemini Flash)
TITLE_GEMINI_MODEL = "gemini-2.5-flash"  # 제목 생성용 모델
TITLE_GEMINI_TEMPERATURE = 0.7  # 제목 생성용 temperature
TITLE_GEMINI_THINKING_BUDGET = 0  # 빠른 응답을 위해 0으로 설정
TITLE_GEMINI_MAX_TOKENS = 1000  # 제목 생성용 토큰 제한 (적은 토큰으로 충분)

# LangSmith 추적 설정
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "oblit-1on1_ai_ui")

# LangSmith 환경변수 자동 설정
if LANGSMITH_TRACING:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    if LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT

# Supabase 설정 
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "audio-recordings")

# Supabase 파일 경로 템플릿
RECORDING_PATH_TEMPLATE = "recordings/{user_id}/{file_id}"

