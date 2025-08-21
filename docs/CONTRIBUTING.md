# 🤝 Contributing Guide

팀 프로젝트에 기여하기 위해 따라야 할 기본 규칙입니다. 이 가이드라인을 따라 일관된 코드 품질과 협업 효율성을 유지합니다.

---

## 📌 브랜치 전략

- 기능 개발: `feat/기능이름`
- 버그 수정: `fix/버그설명`
- 문서 작성: `docs/내용`
- 리팩토링: `refactor/내용`
- 테스트: `test/내용`
- 스타일 수정: `style/내용`
- 예시: `feat/stt-processor-api`, `fix/audio-format-error`

## 💬 커밋 메시지 컨벤션

커밋 메시지는 다음 형식을 따릅니다:
```
<유형>: <설명>

[본문]

[꼬리말]
```

### 커밋 유형
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 스타일 변경 (코드 로직 변경 없음)
- `refactor`: 코드 리팩토링
- `test`: 테스트 코드 추가/수정
- `chore`: 빌드 프로세스, 라이브러리 변경 등

### 예시
```
feat: STT 처리기 화자 구분 기능 추가

- 화자 구분을 위한 diarization 로직 구현
- 화자별 발언 시간 계산 기능 추가
```

---

## ✅ 코드 스타일

- 코드 스타일은 `black`(들여쓰기/줄바꿈 정리), `isort`(import 줄 정리), `flake8`(코드 규칙 검사)으로 관리
- 최대 줄 길이: 88자
- 불필요한 import 제거

## 📁 버전관리 및 디렉토리 구조 가이드

### 🔹 프롬프트 버전 관리

- 기본 경로: `src/prompts/`
- 현재 사용 중인 프롬프트만 이 경로에 위치
- 이전 버전은 `src/prompts/archive/` 폴더로 이동
- 사용 중인 프롬프트에는 버전명을 붙이지 않음
- 예시:
  - 사용 중: `listening_skills.py`
  - 이전 버전: `archive/listening_skills_v1.py`, `archive/listening_skills_testA.py`

### 🔹 서비스 코드 버전 관리

- 기본 경로: `src/services/`
- 현재 사용 중인 서비스는 `processor.py`, `generator.py`, `analyzer.py` 등 명확한 이름 사용
- 더 이상 사용하지 않는 서비스는 `archive/` 폴더에 이동하고 버전명을 붙임
- 예시:
  - 사용 중: `stt_processor/processor.py`
  - 이전 버전: `stt_processor/old/processor_v1.py`

### 🔹 기타 원칙

- **모르는 사람도 쉽게 이해할 수 있도록** 디렉토리 명, 파일명에 의미를 담습니다
- **중복된 파일**은 만들지 않고, 필요 시 명확한 버전명을 붙여 추적 가능하도록 관리합니다


---

이 문서는 `CONTRIBUTING.md`로 프로젝트 루트에 위치해야 하며, GitHub에 자동 인식됩니다.