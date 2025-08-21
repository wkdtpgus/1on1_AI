# Orblit 1-on-1 AI

AI 기반 1:1 미팅 분석 및 질문 템플릿 생성 시스템

## 프로젝트 개요

음성 대화를 STT로 전사하고 LLM으로 분석해 리더에게 맞춤형 피드백을 제공하며, 다음 미팅을 위한 질문 템플릿·가이드를 생성합니다.

## 주요 기능

- STT 기반 미팅 분석: STT 텍스트 전사, 요약 및 분석, 비용 추적
- 템플릿 생성: 목적·톤·개수에 맞춘 질문 세트 생성 및 활용 가이드, 이메일 초안 생성

## 프로젝트 구조

```text
Orblit_1on1_AI/
├─ src/
│  ├─ config/
│  │  └─ config.py                 # 환경설정 (AssemblyAI, Google/Gemini, Supabase 등)
│  ├─ prompts/
│  │  ├─ stt_generation/
│  │  │  ├─ meeting_analysis_prompts.py
│  │  └─ template_generation/
│  │     ├─ guide_prompts.py
│  │     └─ template_prompts.py
│  ├─ services/
│  │  ├─ meeting_generator/
│  │  │  ├─ generate_meeting.py
│  │  │  └─ workflow.py
│  │  └─ template_generator/
│  │     ├─ generate_email.py
│  │     ├─ generate_template.py
│  │     └─ generate_usage_guide.py
│  ├─ utils/
│  │  ├─ mock_db.py
│  │  ├─ model.py
│  │  ├─ performance_logging.py
│  │  ├─ stt_schemas.py
│  │  ├─ template_schemas.py
│  │  └─ utils.py
│  └─ web/
│     ├─ stt_main.py               # 미팅 분석 API 서버
│     └─ template_main.py          # 템플릿/가이드/이메일 생성 API 서버
├─ tests/
│  ├─ test_client_flow.py          # 템플릿 생성 플로우 통합 테스트
│  └─ test_meeting_api.py          # STT 분석 API 테스트
├─ data/                           # 생성 결과 저장 (JSON)
├─ docs/
├─ pyproject.toml
└─ README.md
```

## 기술 스택

- FastAPI, Uvicorn, Poetry
- AssemblyAI(STT), Google Vertex AI / Gemini(LLM)
- Supabase(Storage), Pydantic
- LangChain / LangGraph (워크플로우/LLM 통합)

## 빠른 시작

1) 의존성 설치
```bash
poetry install
```

2) 환경 변수(.env) 설정 예시
```bash
# STT
ASSEMBLYAI_API_KEY=your_assemblyai_api_key

# Google / Gemini
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
# JSON 문자열 전체를 그대로 넣습니다
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
GOOGLE_GENAI_USE_VERTEXAI=false

# Supabase
SUPABASE_URL=https://xxxxxxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_key
SUPABASE_BUCKET_NAME=audio-recordings

# (선택) LangSmith 추적
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=oblit-1on1_ai_ui
```

3) 실행 방법 (둘 중 하나씩 실행)

- 템플릿 생성 API 서버 (tests/test_client_flow.py는 8000 포트를 사용)
```bash
PYTHONPATH=. uvicorn src.web.template_main:app --host 0.0.0.0 --port 8000 --reload
```

- 미팅 분석(STT) API 서버 (tests/test_meeting_api.py는 8000 포트를 사용)
```bash
PYTHONPATH=. uvicorn src.web.stt_main:app --host 0.0.0.0 --port 8000 --reload
```

동시에 실행하려면 포트를 다르게 지정하세요. 예) 템플릿:8001, STT:8000

```bash
PYTHONPATH=. uvicorn src.web.template_main:app --port 8001 --reload
PYTHONPATH=. uvicorn src.web.stt_main:app --port 8000 --reload
```

## API

### 템플릿 생성 API (`/generate`)

- 요청: POST `/generate?generation_type=template|guide|email`
- 본문(JSON): `src.utils.template_schemas`에 정의된 입력 스키마 참고

예시 요청 (템플릿):
```bash
curl -X POST "http://localhost:8000/generate?generation_type=template" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "target_info": "홍길동",
    "purpose": "Growth, Work",
    "detailed_context": "팀 내 갈등 진단 및 해결책 논의",
    "use_previous_data": false,
    "previous_summary": null,
    "num_questions": "Standard",
    "question_composition": "Growth/Goal-oriented, Reflection/Thought-provoking, Action/Implementation-focused",
    "tone_and_manner": "Casual",
    "language": "Korean",
    "include_guide": true
  }'
```

### 미팅 분석 API (`/api/analyze`)

- 요청: POST `multipart/form-data`
- 필드(form):
  - `file_id`(optional, string): Supabase Storage 파일 ID (`only_title=true`이면 생략 가능)
  - `qa_pairs`(optional, string): 질문-답변 JSON 문자열
  - `participants_info`(optional, string): 참가자 정보 JSON 문자열
  - `meeting_datetime`(optional, string): ISO8601
  - `only_title`(optional, bool): 제목만 생성

예시 요청:
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "file_id=recordings/sample.m4a" \
  -F "qa_pairs=$(jq -c . < tests/sample_qa.json)" \
  -F "participants_info={\"leader\":\"김지현\",\"member\":\"김준희\"}" \
  -F "meeting_datetime=2024-12-08T14:30:00" \
  -F "only_title=false"
```

설정 확인: `GET /api/config`

## 테스트

다음 중 하나를 먼저 실행한 뒤 테스트를 실행하세요.
- 템플릿 서버: `uvicorn src.web.template_main:app --port 8000`
- STT AI 서버: `uvicorn src.web.stt_main:app --port 8000`

테스트 실행:
- 템플릿 테스트 : `poetry run pytest tests/test_client_flow.py -v -s`
- STT AI 테스트 : `poetry run pytest tests/test_meeting_api.py`


생성 결과는 `data/` 하위에 저장됩니다.

## 설정 가이드

### Google Cloud / Gemini
1. Vertex AI API 활성화 (Vertex 사용 시)
2. 서비스 계정 키(JSON) 발급 후 `.env`의 `GOOGLE_APPLICATION_CREDENTIALS_JSON`에 전체 JSON 문자열로 설정

### Supabase
1. 프로젝트 생성, Storage 버킷(`audio-recordings`) 생성
2. 퍼블릭 액세스 정책 적용 및 URL/Key 설정

### AssemblyAI
1. 계정 생성 및 API Key 발급 → `ASSEMBLYAI_API_KEY`

