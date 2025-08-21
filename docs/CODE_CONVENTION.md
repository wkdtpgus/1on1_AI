# Orblit 1-on-1 AI 코드 컨벤션

이 문서는 Orblit 1-on-1 AI 프로젝트의 일관된 코드 스타일과 아키텍처 원칙을 정의하여, 팀원 간의 원활한 협업과 유지보수 효율성 증대를 목표로 합니다.

## 목차

1.  [일반 규칙](#1-일반-규칙)
2.  [네이밍 컨벤션](#3-네이밍-컨벤션)
3.  [코딩 스타일 및 포맷팅](#4-코딩-스타일-및-포맷팅)
4.  [FastAPI 개발 가이드](#5-fastapi-개발-가이드)
5.  [설정(Configuration) 관리](#6-설정-관리)
6.  [프롬프트 관리](#7-프롬프트-관리)
7.  [로깅(Logging)](#8-로깅)
8.  [예외 처리](#9-예외-처리)
9. [테스트](#10-테스트)

---

## 1. 일반 규칙

-   **단일 책임 원칙 (SRP):** 모든 클래스와 함수는 하나의 명확한 책임을 가져야 합니다.
-   **관심사의 분리 (SoC):** 설정, 프롬프트, 비즈니스 로직, 유틸리티, 테스트는 명확히 분리합니다.
-   **가독성 우선:** 코드는 실행되기 전에 사람에게 읽혀야 합니다. 항상 명확하고 이해하기 쉬운 코드를 작성합니다.
-   **타입 힌트 적극 사용:** `typing` 모듈을 사용하여 함수의 입력과 출력 타입을 명시하여 코드의 안정성을 높입니다.
-   **불필요한 코드 제거:** 사용하지 않는 함수, 클래스, 변수, 임포트는 즉시 제거하여 코드베이스를 깨끗하게 유지합니다.
-   **유틸리티 분리:** 여러 모듈에서 공통으로 사용될 수 있는 함수는 `src/utils/` 아래의 적절한 파일로 분리하여 재사용성을 높입니다.

---

#### Archive 디렉토리 정책

`archive` 라는 이름의 디렉토리는 더 이상 사용되지 않는 이전 버전의 코드를 보관하는 용도로 사용됩니다. 

-   **참조용:** 이 디렉토리의 파일들은 과거 구현을 참고하기 위한 용도로만 유지됩니다.
-   **수정 금지:** 새로운 기능 개발이나 리팩토링 시 `archive` 내부의 파일은 **수정하거나 현재 코드로 간주해서는 안 됩니다.**
-   **검색 제외:** 코드 검색이나 분석 시 이 디렉토리들은 기본적으로 제외되어야 합니다.

---

### 2. 네이밍 컨벤션

| 종류 | 규칙 | 예시 |
| :--- | :--- | :--- |
| **디렉토리** | `snake_case` | `stt_processor`, `1on1_feedback` |
| **Python 파일** | `snake_case.py` | `processor.py`, `feedback_generator.py` |
| **클래스** | `PascalCase` | `STTProcessor`, `FeedbackGenerator` |
| **함수/메서드** | `snake_case()` | `process_audio()`, `generate_feedback()` |
| **내부 함수/메서드** | `_`로 시작 | `_extract_speaker()`, `_calculate_metrics()` |
| **상수** | `UPPER_SNAKE_CASE` | `MAX_FILE_SIZE`, `OPENAI_MODEL` |
| **Enum 클래스** | `PascalCase` | `AudioFormat`, `FeedbackType` |
| **Enum 멤버** | `UPPER_SNAKE_CASE` | `MP3`, `WAV`, `LISTENING_SKILLS` |
| **변수** | `snake_case` | `audio_file`, `feedback_result` |

---

### 3. 코딩 스타일 및 포맷팅

-   **기본:** **PEP 8** 스타일 가이드를 준수합니다.
-   **포매터:** **`black`** (코드 포맷팅), **`isort`** (import 정렬)를 사용하여 코드 스타일을 일관되게 유지합니다. 커밋 전에 항상 포매터를 실행하는 것을 권장합니다.
-   **최대 줄 길이:** 100자 내외로 유연하게 관리하되, 가독성을 최우선으로 고려합니다.
-   **임포트:** 라이브러리, 외부 모듈, 내부 모듈 순으로 그룹화하여 정렬합니다 (`isort`가 자동 처리). 절대 경로 임포트를 원칙으로 합니다.
    ```python
    # 1. 표준 라이브러리
    import json
    import logging
    
    # 2. 서드파티 라이브러리
    from fastapi import FastAPI, HTTPException
    
    # 3. 내부 모듈
    from src.config.config import OPENAI_API_KEY
    from src.services.stt_processor.processor import STTProcessor
    ```
-   **주석:** 
    -   코드가 "무엇"을 하는지보다 **"왜"** 그렇게 작성되었는지 설명하는 데 집중합니다. 복잡한 비즈니스 로직이나 특정 결정의 배경에 대해 주석을 답니다.
    -   명백한 코드를 설명하는 주석(e.g. `i = i + 1  # i를 1 증가시킴`)이나, 사용하지 않아 주석 처리된 코드 블록은 남기지 않고 제거합니다.

---

### 4. FastAPI 개발 가이드

`FastAPI`를 사용한 웹 애플리케이션 개발 시 다음 원칙을 따릅니다.

-   **라우터 분리:**
    -   기능별로 라우터를 분리하여 `src/web/routers/` 디렉토리에 위치시킵니다.
    -   각 라우터는 단일 도메인의 엔드포인트만 담당합니다. (예: `stt_router.py`, `template_router.py`)
-   **의존성 주입:**
    -   FastAPI의 `Depends`를 활용하여 서비스 클래스를 주입받아 사용합니다.
    -   의존성은 함수 레벨에서 정의하여 재사용성을 높입니다.
-   **응답 모델:**
    -   모든 API 응답은 Pydantic 모델을 사용하여 타입 안정성을 보장합니다.
    -   응답 모델은 `src/utils/schemas.py`에 정의합니다.
-   **예외 처리:**
    -   FastAPI의 `HTTPException`을 사용하여 적절한 HTTP 상태 코드와 메시지를 반환합니다.
    -   비즈니스 로직에서 발생하는 예외는 라우터 레벨에서 HTTP 예외로 변환합니다.

---

### 5. 설정(Configuration) 관리

-   모든 전역 설정 (모델 이름, API 키, 파일 경로 등)은 `src/config/config.py`에서 관리합니다.
-   설정 변수는 `UPPER_SNAKE_CASE`를 따릅니다.
-   관련 설정들은 접두사를 사용하여 그룹화합니다. (예: `STT_MAX_FILE_SIZE`, `FEEDBACK_MODEL_NAME`)
-   API 키와 같은 민감 정보는 `.env` 파일에 저장하고, 코드에서는 `os.getenv()`를 통해 접근합니다. `.env` 파일은 Git 추적에서 제외합니다.

---

### 6. 프롬프트 관리

-   모든 LLM 프롬프트는 `src/prompts/` 디렉토리 내의 별도 Python 파일에서 관리합니다.
-   프롬프트는 기능별로 파일을 분리합니다 (예: `listening_skills.py`, `question_quality.py`).
-   프롬프트 내용은 `UPPER_SNAKE_CASE`를 따르는 상수로 정의합니다.
-   F-string이나 템플릿을 사용하여 동적 값을 주입합니다.
-   **불필요한 마크업 지양:** 프롬프트 내용에 특정 포맷(e.g., `json`)을 명시하거나 백틱(\`)으로 감싸는 것은 모델의 성능에 영향을 주거나 예측을 제한할 수 있으므로, 꼭 필요한 경우가 아니라면 지양합니다.

---

### 7. 로깅(Logging)

-   Python의 내장 `logging` 모듈을 사용합니다.
-   파일 상단에서 모듈 레벨 로거를 설정합니다. 로거 이름은 모듈의 역할을 나타내는 문자열을 사용합니다.
    ```python
    # 좋은 예
    logger = logging.getLogger("stt_processor")
    
    # 지양
    # logger = logging.getLogger(__name__) 
    ```
-   로그 레벨(INFO, DEBUG, WARNING, ERROR)을 상황에 맞게 사용하여 로그의 중요도를 구분합니다.
-   사용자 입력이나 LLM 결과와 같이 중요한 데이터는 INFO 레벨로 기록하여 흐름 추적을 용이하게 합니다.

---

### 8. 예외 처리

-   LLM API 호출, 파일 I/O 등 외부 시스템과의 연동 지점에는 반드시 `try...except` 블록을 사용하여 예외를 처리합니다.
-   발생한 예외는 로그로 기록하고, 함수의 반환 타입을 `Optional[T]`로 설정하거나 명확한 에러 메시지를 담은 객체를 반환하여 상위 호출자에게 실패를 알립니다.

---

### 9. 테스트

-   주요 비즈니스 로직과 기능은 반드시 `tests/` 디렉토리 아래에 테스트 코드를 작성합니다.
-   테스트 파일명은 `test_` 접두사로 시작합니다. (예: `test_stt_processor.py`)
-   `pytest`를 테스트 프레임워크로 사용합니다.
-   외부 API 의존성이 있는 테스트의 경우, `unittest.mock`을 사용하여 의존성을 격리하고 테스트의 안정성을 높입니다.