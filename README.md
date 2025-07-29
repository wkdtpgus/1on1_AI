# Orblit 1-on-1 AI

AI 기반 1:1 미팅 피드백 시스템

## 프로젝트 개요

OneOnOne_AI_System은 1:1 미팅의 음성 대화를 STT 기술로 자동 기록하고, AI를 통해 분석하는 프로젝트입니다. AI는 미팅 목적에 맞는 질문 템플릿을 생성하고, 대화가 끝난 후 리더에게 맞춤형 피드백을 제공합니다. 이 모든 과정은 리더의 코칭 역량을 강화하고 구성원의 성장을 촉진하는 것을 목표로 합니다.

### 주요 기능

1. **STT 처리기 (STT Processor)**: 
   - 1:1 미팅 음성 파일(mp3, wav 등)을 입력받아 화자를 구분하는 텍스트 스크립트로 변환

2. **템플릿 생성기 (Template Generator)**: 
   - "신규 입사자와의 첫 미팅"과 같은 목적을 입력하면 상황에 맞는 1:1 미팅 질문 템플릿 생성

3. **1:1 피드백 생성기 (1-on-1 Feedback Generator)**: 
   - STT 텍스트를 분석하여 리더의 발언 비율, 질문의 질, 대화 습관 등을 평가하고 개선 피드백 제공

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
poetry run python src/web/app.py
```

## API 엔드포인트

- `GET /`: 루트 엔드포인트
- `GET /health`: 헬스 체크
- `POST /api/v1/stt/process`: 음성 파일을 텍스트로 변환
- `POST /api/v1/template/generate`: 미팅 템플릿 생성
- `POST /api/v1/feedback/generate`: 1:1 피드백 생성

## 프로젝트 구조

```
Orblit_1on1_AI/
│
├── src/                                    # 소스 코드 디렉토리
│   ├── __init__.py
│   ├── config/                            # 설정 관련 모듈
│   │   ├── __init__.py
│   │   └── config.py                    # 환경 설정 및 상수 정의
│   │
│   ├── services/                          # 핵심 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── stt_processor/                 # STT 처리 서비스
│   │   │   ├── __init__.py
│   │   │   ├── processor.py               # STT 처리 메인 로직
│   │   │   ├── speaker_diarization.py     # 화자 구분 로직
│   │   │   └── audio_handler.py           # 오디오 파일 처리
│   │   │
│   │   ├── template_generator/            # 템플릿 생성 서비스
│   │   │   ├── __init__.py
│   │   │   ├── generator.py               # 템플릿 생성 메인 로직
│   │   │   └── template_types.py          # 템플릿 타입 정의
│   │   │
│   │   └── 1on1_feedback/                 # 1:1 피드백 생성 서비스
│   │       ├── __init__.py
│   │       ├── analyzer.py                # 대화 분석 로직
│   │       ├── feedback_generator.py      # 피드백 생성 로직
│   │       └── metrics_calculator.py      # 대화 메트릭 계산
│   │
│   ├── prompts/                           # AI 프롬프트 템플릿
│   │   ├── __init__.py
│   │   ├── template_generation/           # 템플릿 생성용 프롬프트
│   │   │   ├── __init__.py
│   │   │   ├── onboarding.py              # 온보딩 관련 프롬프트
│   │   │   ├── performance_review.py      # 성과 리뷰 프롬프트
│   │   │   └── general_checkin.py         # 일반 체크인 프롬프트
│   │   │
│   │   └── 1on1_feedback/                 # 피드백 생성용 프롬프트
│   │       ├── __init__.py
│   │       ├── listening_skills.py        # 경청 스킬 평가 프롬프트
│   │       ├── question_quality.py        # 질문 품질 평가 프롬프트
│   │       └── conversation_balance.py    # 대화 균형 평가 프롬프트
│   │
│   ├── utils/                             # 유틸리티 함수
│   │   ├── __init__.py
│   │   ├── file_utils.py                  # 파일 처리 유틸리티
│   │   ├── openai_client.py               # OpenAI API 클라이언트
│   │   └── validators.py                  # 입력 검증 함수
│   │
│   └── web/                               # 웹 애플리케이션
│       ├── __init__.py
│       ├── app.py                         # FastAPI 메인 애플리케이션
│       ├── routers/                       # API 라우터
│       │   ├── __init__.py
│       │   ├── stt_router.py              # STT 관련 엔드포인트
│       │   ├── template_router.py         # 템플릿 관련 엔드포인트
│       ├── └── feedback_router.py         # 피드백 관련 엔드포인트
│
├── data/                                  # 데이터 저장 디렉토리
│   ├── raw_audio/                         # 원본 음성 파일
│   │   └── .gitkeep
│   ├── stt_transcripts/                   # STT 변환 결과
│   │   └── .gitkeep
│   ├── generated_templates/               # 생성된 템플릿
│   │   └── .gitkeep
│   └── generated_1on1_feedback/           # 생성된 피드백
│       └── .gitkeep
│
├── docs/                                  # 프로젝트 문서
│   ├── project_definition.md              # 프로젝트 정의서
│   ├── requirements_specification.md      # 요구사항 명세서
│   ├── architecture_design.md             # 아키텍처 설계서
│   └── api_documentation.md               # API 문서 (추가 예정)
│
├── tests/                                 # 테스트 코드
│   ├── __init__.py
│
├── .env.example                           # 환경 변수 예시 파일
├── .gitignore                             # Git 무시 파일
├── poetry.lock                            # Poetry 잠금 파일
├── pyproject.toml                         # Poetry 프로젝트 설정
├── README.md                              # 프로젝트 README

```

## 개발 가이드

### 코드 포맷팅
```bash
```

### 린팅
```bash
```

### 테스트 실행
```bash
```

## 라이선스

[라이선스 정보 추가 예정]