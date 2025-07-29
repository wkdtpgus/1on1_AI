# 아키텍처 설계서

## 1. 시스템 아키텍처 개요

### 1.1 아키텍처 패턴
- **패턴**: Layered Architecture + Microservices
- **프레임워크**: FastAPI (Python)
- **배포**: Docker 컨테이너 기반

### 1.2 주요 컴포넌트
```
┌─────────────────────────────────────────────────┐
│                   Client Layer                   │
│              (Web Browser / API Client)          │
└─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│                    API Layer                     │
│                  (FastAPI Server)                │
├─────────────────────────────────────────────────┤
│  - Authentication & Authorization                │
│  - Request Validation                            │
│  - Response Formatting                           │
└─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│                 Service Layer                    │
├─────────────────┬────────────────┬──────────────┤
│  STT Processor  │Template Generator│1:1 Feedback │
│    Service      │    Service       │  Service    │
└─────────────────┴────────────────┴──────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│               External APIs Layer                │
├─────────────────────┬───────────────────────────┤
│   OpenAI Whisper    │      OpenAI GPT-4         │
│      (STT)          │   (Text Generation)       │
└─────────────────────┴───────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│                 Storage Layer                    │
├─────────────────────┬───────────────────────────┤
│   File Storage      │    JSON Storage           │
│  (Audio Files)      │   (Transcripts)           │
└─────────────────────┴───────────────────────────┘
```

## 2. 컴포넌트 상세 설계

### 2.1 API Layer (FastAPI)
**책임**: HTTP 요청 처리, 인증, 유효성 검사

**주요 엔드포인트**:
- `/api/v1/stt/process` - STT 처리
- `/api/v1/template/generate` - 템플릿 생성
- `/api/v1/feedback/generate` - 피드백 생성

### 2.2 Service Layer

#### STT Processor Service
**책임**: 음성 파일 처리 및 텍스트 변환
- 파일 검증 및 전처리
- OpenAI Whisper API 호출
- 결과 후처리 및 저장

#### Template Generator Service
**책임**: AI 기반 미팅 템플릿 생성
- 프롬프트 엔지니어링
- GPT-4 API 호출
- 템플릿 구조화 및 저장

#### 1-on-1 Feedback Service
**책임**: 대화 분석 및 피드백 생성
- 대화 메트릭 계산
- AI 기반 분석
- 구조화된 피드백 생성

### 2.3 Storage Layer
**파일 시스템 구조**:
```
data/
├── raw_audio/          # 원본 음성 파일
├── stt_transcripts/    # STT 변환 결과
├── generated_templates/# 생성된 템플릿
└── generated_1on1_feedback/ # 생성된 피드백
```

## 3. 데이터 흐름

### 3.1 STT 처리 흐름
1. 클라이언트가 음성 파일 업로드
2. API Layer에서 파일 검증
3. STT Service가 파일을 임시 저장
4. OpenAI Whisper API 호출
5. 결과를 JSON으로 변환 및 저장
6. 클라이언트에 결과 반환

### 3.2 템플릿 생성 흐름
1. 클라이언트가 미팅 목적 입력
2. Template Service가 프롬프트 생성
3. GPT-4 API 호출
4. 결과 구조화 및 저장
5. 클라이언트에 템플릿 반환

### 3.3 피드백 생성 흐름
1. 클라이언트가 transcript ID 제공
2. Feedback Service가 transcript 로드
3. 대화 메트릭 계산
4. GPT-4를 통한 분석
5. 구조화된 피드백 생성 및 저장
6. 클라이언트에 피드백 반환

## 4. 보안 고려사항

### 4.1 API 보안
- API 키 기반 인증
- Rate limiting 적용
- CORS 설정

### 4.2 데이터 보안
- 업로드 파일 크기 제한
- 파일 타입 검증
- 민감 정보 마스킹

## 5. 확장성 고려사항

### 5.1 수평적 확장
- 서비스별 독립적 스케일링
- 로드 밸런서 고려

### 5.2 캐싱 전략
- 자주 사용되는 템플릿 캐싱
- API 응답 캐싱 고려

## 6. 모니터링 및 로깅

### 6.1 로깅
- 구조화된 JSON 로깅
- 로그 레벨별 관리

### 6.2 모니터링 지표
- API 응답 시간
- 에러율
- 서비스별 처리량