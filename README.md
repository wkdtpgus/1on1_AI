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
   - 주요 Q&A 요약
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
   - 주요 질문과 답변 정리

3. **질문 템플릿 생성 (Template Generation)**: 
   - 사용자 맞춤형 1:1 미팅 질문 생성
   - 카테고리별, 난이도별 질문 제공
   - 미팅 목적에 따른 질문 커스터마이징

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

## 프로젝트 구조

```
Orblit_1on1_AI/
├── data/                                  # 데이터 저장소
│   ├── raw_audio/                         # 원본 오디오 파일
│   ├── stt_transcripts/                   # STT 전사 결과
│   └── generated_templates/               # 생성된 질문 템플릿
│
├── src/                                   # 소스 코드
│   ├── config/                            # 설정 관리
│   │   └── config.py                      # STT, LLM 등 전체 설정
│   │
│   ├── models/                            # 데이터 모델 + 처리 로직
│   │   ├── __init__.py
│   │   ├── transcription.py               # STT 전사 기능
│   │   ├── recording.py                   # 녹음 관련 기능
│   │   ├── stt_llm_analysis.py           # STT→LLM 분석 기능
│   │   └── template.py                    # 템플릿 생성 기능
│   │
│   ├── prompts/                           # LLM 프롬프트
│   │   ├── stt_llm_prompts.py            # 미팅 분석용 프롬프트
│   │   └── template_prompts.py            # 템플릿 생성용 프롬프트
│   │
│   ├── utils/                             # 유틸리티 함수
│   │   └── util.py                        # 공통 유틸리티
│   │
│   └── web/                               # 웹 인터페이스
│       └── main.py                        # FastAPI 애플리케이션
│
├── tests/                                 # 테스트 코드
│   └── (테스트 파일들)
│
├── docs/                                  # 프로젝트 문서
│   ├── project_definition.md
│   ├── requirements_specification.md
│   ├── architecture_design.md
│   └── CODE_CONVENTION.md
│
├── poetry.lock                            # Poetry 잠금 파일
├── pyproject.toml                         # Poetry 프로젝트 설정
└── README.md
```

### 주요 특징

- **간소한 구조**: 5개 핵심 디렉토리로 구성 (config, models, prompts, utils, web)
- **모델 중심**: 데이터 구조와 처리 로직을 models에 통합
- **명확한 분리**: STT 전사, LLM 분석, 템플릿 생성 기능별 모듈 분리
- **확장 가능**: 새로운 기능 추가 시 models에 새 파일만 추가

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