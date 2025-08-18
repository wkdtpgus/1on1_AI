# Orblit 1-on-1 AI

AI 기반 1:1 미팅 분석 및 피드백 시스템

## 프로젝트 개요

리더의 1:1 미팅 스킬 향상을 위한 AI 분석 시스템입니다. 음성 대화를 텍스트로 변환하고 LLM을 활용해 리더에게 맞춤형 피드백을 제공하며, 다음 미팅을 위한 질문 템플릿을 생성합니다.

## 기능 플로우

```
1. STT: 1on1 미팅 음성 → 텍스트 변환 + 화자 분리
2. LLM Analysis: 텍스트 → 리더 피드백 분석
   - 미팅 제목 요약
   - 미팅 내용 요약
   - 리더 피드백 (발화 비율, 질문 품질, 개선점)
   - 질문별 답변 요약
3. Template Generation: 사용자 프롬프트 → 맞춤형 질문 템플릿
```

### 주요 기능

1. **음성 전사 (STT Processing)**: 
   - 1:1 미팅 음성을 텍스트로 변환
   - 화자 분리 (리더/팀원 구분)
   - AssemblyAI 기반 고정밀 전사

2. **미팅 분석 (Meeting Analysis)**: 
   - 미팅 제목 및 내용 요약
   - 리더의 발화 비율, 질문 품질 분석
   - 구체적인 개선점과 액션 아이템 제공
   - 질문별 답변 정리

3. **질문 템플릿 생성 (Template Generation)**: 
   - 사용자 맞춤형 1:1 미팅 질문 생성
   - 미팅 목적에 따른 질문 커스터마이징

## 프로젝트 구조
프로젝트는 기능적 역할에 따라 명확하게 분리된 디렉토리 구조를 따릅니다.

```
Orblit_1on1_AI/
│
├── data/                                  # 데이터 저장 디렉토리
│   ├── raw_audio/                         # 원본 음성 파일
│   ├── stt_transcripts/                   # STT 변환 결과
│   ├── generated_templates/               # 생성된 템플릿
│   └── generated_1on1_feedback/           # 생성된 피드백

├── docs/                                  # 프로젝트 관련 문서
│   ├── CODE_CONVENTION.md
│   ├── CONTRIBUTING.md

├── src/                                   # 주요 소스 코드
│   ├── config/                            # 전역 설정 관리
│   │   └── config.py
│   │
│   ├── services/                          # 핵심 비즈니스 로직
│   │   ├── stt_processor/                 # STT 처리 서비스
│   │   │   ├── processor.py               # STT 처리 메인 로직
│   │   │   ├── speaker_diarization.py     # 화자 구분 로직
│   │   │   └── audio_handler.py           # 오디오 파일 처리
│   │   │
│   │   ├── template_generator/            # 템플릿 생성 서비스
│   │   │   ├── generator.py               # 템플릿 생성 메인 로직
│   │   │   └── template_types.py          # 템플릿 타입 정의
│   │   │
│   │   └── 1on1_feedback/                 # 1:1 피드백 생성 서비스
│   │       ├── analyzer.py                # 대화 분석 로직
│   │       ├── feedback_generator.py      # 피드백 생성 로직
│   │       └── metrics_calculator.py      # 대화 메트릭 계산
│   │
│   ├── prompts/                           # LLM 프롬프트 템플릿
│   │   ├── template_generation/           # 템플릿 생성용 프롬프트
│   │   │   ├── onboarding.py
│   │   │   ├── performance_review.py
│   │   │   └── general_checkin.py
│   │   │
│   │   └── 1on1_feedback/                 # 피드백 생성용 프롬프트
│   │       ├── listening_skills.py
│   │       ├── question_quality.py
│   │       └── conversation_balance.py
│   │
│   ├── utils/                             # 공통 유틸리티
│   │   ├── file_utils.py
│   │   ├── openai_client.py
│   │   └── validators.py
│   │
│   └── web/                               # FastAPI 웹 애플리케이션
│       ├── app.py                         # 메인 애플리케이션
│       └── routers/                       # API 라우터
│           ├── stt_router.py
│           ├── template_router.py
│           └── feedback_router.py

├── tests/                                 # 테스트 코드
│   ├── archive/                           # 사용하지 않는 과거 테스트
│   ├── data/                              # 테스트용 데이터
│   └── test_*.py                          # 테스트 파일들

├── poetry.lock                            # 의존성 버전 고정
├── pyproject.toml                         # 프로젝트 메타데이터 및 의존성 관리
└── README.md
```

## 설치 방법

### 사전 요구사항

- Python 3.9 이상
- Poetry (Python 패키지 관리자)

### 설치 단계

1. 저장소 클론
```bash
git clone [repository-url]
cd Orblit_1on1_AI
```

2. Poetry를 사용하여 의존성 설치
```bash
poetry install
```

3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 OpenAI API 키 설정
```

4. 개발 서버 실행
```bash
poetry run python src/web/main.py
```

## API 엔드포인트

- `GET /`: 루트 엔드포인트
- `GET /health`: 헬스 체크
- `POST /api/v1/transcription/process`: 음성 파일을 텍스트로 변환
- `POST /api/v1/analysis/meeting`: 미팅 텍스트 분석 및 피드백 생성
- `POST /api/v1/template/generate`: 질문 템플릿 생성


