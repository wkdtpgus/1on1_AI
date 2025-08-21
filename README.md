# Orblit 1-on-1 AI

AI 기반 1:1 미팅 분석 및 피드백 시스템

## 프로젝트 개요

리더의 1:1 미팅 스킬 향상을 위한 AI 분석 시스템입니다. 음성 대화를 텍스트로 변환하고 LLM을 활용해 리더에게 맞춤형 피드백을 제공하며, 다음 미팅을 위한 질문 템플릿을 생성합니다.

##아키텍처

### LangGraph 파이프라인
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Retrieve  │ -> │ Transcribe   │ -> │   Analyze   │
│ (Supabase)  │    │ (AssemblyAI) │    │ (LLM)       │
└─────────────┘    └──────────────┘    └─────────────┘
```

### 데이터 플로우
```
1. 프론트엔드 → Supabase Storage (직접 파일 업로드)
2. 백엔드 → Supabase (파일 조회)
3. AssemblyAI → STT 변환 + 화자 분리
4. Google Vertex AI/Gemini → 미팅 분석 및 피드백 생성
```

## 🚀 주요 기능

### 1. 미팅 분석 서비스 (STT Main)
- **음성 전사**: AssemblyAI 기반 고정밀 STT 변환
- **화자 분리**: 리더/팀원 구분 및 발화 시간 비율 계산
- **LLM 분석**: Gemini/Vertex AI를 통한 미팅 분석
- **실시간 성능 모니터링**: 실행 시간, 토큰 사용량, 비용 추적

### 2. 템플릿 생성 서비스 (Template Main)  
- **맞춤형 질문 생성**: 미팅 목적별 질문 템플릿
- **스트리밍 응답**: 실시간 질문 생성
- **다양한 템플릿**: 온보딩, 성과 리뷰, 일반 체크인 등

### 3. 웹 인터페이스
- **음성 녹음**: 브라우저 기반 실시간 녹음
- **실시간 분석**: 진행률 표시 및 결과 시각화
- **결과 관리**: 분석 결과 복사, 마크다운 내보내기


## 📁 프로젝트 구조

```
Orblit_1on1_AI/
├── src/
│   ├── config/
│   │   └── config.py                    # 환경설정 (AssemblyAI, Google Cloud, Supabase)
│   │
│   ├── services/
│   │   ├── meeting_analyze/             # 미팅 분석 파이프라인 (LangGraph)
│   │   │   ├── meeting_pipeline.py     # LangGraph 워크플로우 파이프라인
│   │   │   └── meeting_nodes.py        # 파이프라인 노드 구현 
│   │   │
│   │   └── template_generator/          # 질문 템플릿 생성
│   │       ├── generate_template.py    # 템플릿 생성 로직
│   │       └── generate_summary.py     # 요약 생성 로직
│   │
│   ├── prompts/
│   │   ├── stt_generation/
│   │   │   └── meeting_analysis_prompts.py  # 미팅 분석용 프롬프트
│   │   └── template_generation/
│   │       └── prompts.py               # 템플릿 생성용 프롬프트
│   │
│   ├── utils/
│   │   ├── model.py                    # STT + 템플릿 통합 완료
│   │   ├── stt_schemas.py              # Pydantic 스키마 정의 (스키마 통합 아직 안됨)
│   │   ├── performance_logging.py      # 성능 모니터링 데코레이터
│   │   └── template_schemas.py         # 템플릿 스키마 (스키마 통합 아직 안됨)
│   │
│   └── web/
│       ├── stt_main.py                 # 미팅 분석 API 서버 (일단 분리 시킴)
│       └── main.py                     # 통합 필요
│
├── frontend/                           # 웹 UI
│   ├── index.html                      # 메인 페이지
│   ├── api.js                         # API 통신 모듈
│   └── app.js                         # 프론트엔드 로직
│
├── data/                              # 분석 결과 저장
├── docs/                              # 문서
├── tests/                             # 테스트
├── pyproject.toml                     # Poetry 설정
└── template_main.py                   # 템플릿 대시보드 서버
```


## 🛠️ 기술 스택

### 백엔드
- **FastAPI**: 웹 프레임워크
- **LangGraph**: AI 워크플로우 오케스트레이션
- **LangChain**: LLM 통합 프레임워크
- **AssemblyAI**: 음성 전사 (STT)
- **Google Vertex AI / Gemini**: LLM 분석
- **Supabase**: 클라우드 스토리지
- **Pydantic**: 데이터 검증

### 프론트엔드
- **Vanilla JavaScript**: 클라이언트 로직
- **Tailwind CSS**: UI 스타일링
- **Web Audio API**: 브라우저 음성 녹음

### 인프라
- **Poetry**: Python 패키지 관리
- **Uvicorn**: ASGI 서버

## ⚙️ 설치 및 실행

### 사전 요구사항
- Python 3.11+
- Poetry
- Google Cloud Project (Vertex AI 활성화)
- AssemblyAI API Key
- Supabase Project
```

### 의존성 설치
```bash
# Poetry 사용
poetry install

```

### 환경 변수 설정
```bash
# .env 파일 생성 후 다음 변수들 설정
ASSEMBLYAI_API_KEY=your_assemblyai_api_key
GOOGLE_CLOUD_PROJECT=your_project_id  
GOOGLE_CLOUD_LOCATION=your_location
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_BUCKET_NAME=audio-recordings
```

### 서비스 실행


```bash
PYTHONPATH=. uvicorn src.web.stt_main:app --host 0.0.0.0 --port 8000 --reload# http://localhost:8000
```


## API 엔드포인트

### 미팅 분석 API (포트: 8000)
- `GET /`: 웹 인터페이스
- `GET /api/config`: 프론트엔드 설정 정보
- `POST /api/analyze`: 미팅 분석 실행
  ```json
  {
    "file_id": "recording_uuid_timestamp.wav",
    "qa_data": [...],
    "participants_info": {...},
    "meeting_datetime": "2024-01-01T10:00:00"
  }
  ```

## 설정 가이드

### Google Cloud 설정
1. Google Cloud Console에서 프로젝트 생성
2. Vertex AI API 활성화
3. 서비스 계정 키 생성 및 JSON 다운로드
4. `GOOGLE_APPLICATION_CREDENTIALS_JSON`에 JSON 내용 설정

### Supabase 설정
1. Supabase 프로젝트 생성
2. Storage 버킷 생성 (`audio-recordings`)
3. 퍼블릭 액세스 정책 설정
4. URL 및 anon key 복사

### AssemblyAI 설정
1. AssemblyAI 계정 생성
2. API 키 발급
3. `ASSEMBLYAI_API_KEY`에 설정

