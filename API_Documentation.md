# 1on1 AI API 문서

## 📋 개요
1on1 미팅 템플릿 생성, 이메일 작성, 활용 가이드 생성을 위한 통합 API

## 🔗 기본 정보
- **Base URL**: `http://localhost:8000/api/template`
- **Content-Type**: `application/json`
- **인증**: 없음

---

## 1. 공통 입력 파라미터

모든 엔드포인트에서 사용하는 공통 필드들:

### 필수 파라미터
| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `user_id` | string | 조회할 사용자의 고유 ID | `"user_001"` |
| `target_info` | string | 1on1 대상자 정보 (팀, 직급, 이름 등) | `"김준희 (프론트엔드 개발팀 리드)"` |
| `purpose` | string | 1on1에서 얻고자 하는 정보의 카테고리 | `"Growth, Work"` |
| `detailed_context` | string | 상세한 맥락, 구체적인 상황 | `"프로덕트 디자인 팀 내 불화 발생하여 갈등 상황 진단 및 해결책 논의하고자 함"` |

### 선택 파라미터
| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `language` | string | `"Korean"` | 출력 언어 |
| `include_guide` | boolean | `false` | 생성된 질문에 대한 활용 가이드 포함 여부 |

---

## 2. 템플릿 생성 API

### 엔드포인트
```
POST /api/template?generation_type=template
```

### 입력 예시
```json
{
  "user_id": "user_001",
  "target_info": "김준희 (프론트엔드 개발팀 리드)",
  "purpose": "Growth, Work",
  "detailed_context": "프로덕트 디자인 팀 내 불화 발생하여 갈등 상황 진단 및 해결책 논의하고자 함",
  "num_questions": "Standard",
  "question_composition": "Growth/Goal-oriented, Reflection/Thought-provoking",
  "tone_and_manner": "Casual",
  "language": "Korean"
}
```

### 출력 예시
```json
{
  "generated_questions": {
    "1": "이번 분기 목표 중에서 가장 큰 성과는 무엇이었나요?",
    "2": "팀 내 갈등 상황에서 본인의 역할은 어떻게 되나요?",
    "3": "내년에는 어떤 역량 개발을 계획하고 있나요?"
  }
}
```

### 추가 파라미터 설명
| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `num_questions` | string | 생성할 질문 수 | `"Simple"`, `"Standard"`, `"Advanced"` |
| `question_composition` | string | 질문 유형 조합 | `"Experience/Story-based, Growth/Goal-oriented"` |
| `tone_and_manner` | string | 원하는 어조와 말투 | `"Formal"`, `"Casual"` |

---

## 3. 이메일 생성 API

### 엔드포인트
```
POST /api/template?generation_type=email
```

### 입력 예시
```json
{
  "user_id": "user_001",
  "target_info": "김준희 (프론트엔드 개발팀 리드)",
  "purpose": "Growth, Work",
  "detailed_context": "프로덕트 디자인 팀 내 불화 발생하여 갈등 상황 진단 및 해결책 논의하고자 함",
  "use_previous_data": false,
  "previous_summary": null,
  "language": "Korean"
}
```

### 출력 예시
```json
{
  "generated_email": "안녕하세요, 김준희 리드님\n\n이번 1on1 미팅에서 다음 주제들에 대해 이야기 나눠보고 싶습니다:\n\n1. 이번 분기 팀 내 주요 성과와 도전 과제\n2. 개인별 성장 목표 및 지원 필요 사항\n3. 팀 협업 개선 방안\n\n가능한 일정 조율 부탁드립니다.\n\n감사합니다."
}
```

### 추가 파라미터 설명
| 필드 | 타입 | 설명 |
|------|------|------|
| `use_previous_data` | boolean | 이전 1on1 요약 데이터 활용 여부 |
| `previous_summary` | string | 이전 1on1 요약 및 액션 아이템 정보 |

---

## 4. 활용 가이드 생성 API

### 엔드포인트
```
POST /api/template?generation_type=guide
```

### 입력 예시
```json
{
  "user_id": "user_001",
  "target_info": "김준희 (프론트엔드 개발팀 리드)",
  "purpose": "Growth, Work",
  "detailed_context": "프로덕트 디자인 팀 내 불화 발생하여 갈등 상황 진단 및 해결책 논의하고자 함",
  "generated_questions": {
    "1": "이번 분기 목표 중에서 가장 큰 성과는 무엇이었나요?",
    "2": "팀 내 갈등 상황에서 본인의 역할은 어떻게 되나요?",
    "3": "내년에는 어떤 역량 개발을 계획하고 있나요?"
  },
  "language": "Korean"
}
```

### 출력 예시 (일반 응답)
```json
{
  "usage_guide": "📋 1on1 미팅 준비 가이드\n\n1️⃣ 사전 준비사항\n- 미팅 목적과 목표를 명확히 정리하세요\n- 생성된 질문들을 검토하고 필요시 수정하세요\n\n2️⃣ 미팅 진행 팁\n- 편안한 분위기에서 시작하세요\n- 열린 마음으로 경청하는 태도를 보여주세요\n\n3️⃣ 후속 조치\n- 논의된 내용을 정리하여 공유하세요\n- 합의된 액션 아이템을 추적하세요"
}
```

### 출력 예시 (스트리밍 응답)
```
data: "📋 1on1 미팅 준비 가이드\n\n"

data: "1️⃣ 사전 준비사항\n"

data: "- 미팅 목적과 목표를 명확히 정리하세요\n"

data: "- 생성된 질문들을 검토하고 필요시 수정하세요\n\n"

data: "2️⃣ 미팅 진행 팁\n"

data: "- 편안한 분위기에서 시작하세요\n"

data: "- 열린 마음으로 경청하는 태도를 보여주세요\n\n"

data: "3️⃣ 후속 조치\n"

data: "- 논의된 내용을 정리하여 공유하세요\n"

data: "- 합의된 액션 아이템을 추적하세요"

data: {"type": "complete"}
```

### 필수 파라미터
| 필드 | 타입 | 설명 |
|------|------|------|
| `generated_questions` | object | 템플릿 생성 API에서 받은 질문들 |

---

## 5. 프론트엔드 사용 예시

### JavaScript (일반 요청)
```javascript
// 템플릿 생성
async function generateTemplate() {
    const response = await fetch('/api/template?generation_type=template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: "user_001",
            target_info: "김준희 (프론트엔드 개발팀 리드)",
            purpose: "Growth, Work",
            detailed_context: "프로덕트 디자인 팀 내 불화 발생하여 갈등 상황 진단 및 해결책 논의하고자 함",
            num_questions: "Standard",
            question_composition: "Growth/Goal-oriented, Reflection/Thought-provoking",
            tone_and_manner: "Casual",
            language: "Korean"
        })
    });

    const data = await response.json();
    console.log(data.generated_questions);
}
```

### JavaScript (가이드 스트리밍)
```javascript
function generateGuideStream() {
    const eventSource = new EventSource('/api/template?generation_type=guide');

    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);

        if (data.error) {
            console.error('오류:', data.error);
            eventSource.close();
            return;
        }

        // 실시간으로 UI 업데이트
        document.getElementById('guide-output').textContent += data;
    };

    eventSource.onerror = function(event) {
        console.error('연결 오류:', event);
        eventSource.close();
    };
}
```

---

## 6. 에러 응답

### 공통 에러 형식
```json
{
    "detail": "에러 메시지"
}
```

### 주요 에러 케이스
- `400 Bad Request`: 필수 파라미터 누락, 잘못된 파라미터 값
- `500 Internal Server Error`: 서버 내부 오류 (LLM 생성 실패 등)

---

## 7. 추가 참고사항

### 🚀 실시간 스트리밍
- **가이드 생성** 시에만 스트리밍 지원
- Server-Sent Events (SSE) 사용
- 실시간으로 생성되는 텍스트를 확인할 수 있음

### 🔧 개발 팁
- Swagger UI에서 API 테스트 가능: `http://localhost:8000/docs`
- 모든 응답은 UTF-8 인코딩 (한글 지원)
- CORS 설정으로 크로스 도메인 요청 가능

### 📊 데이터 형식
- 입력: JSON (application/json)
- 출력: JSON 또는 Server-Sent Events
- 날짜 형식: ISO 8601
- 언어: 기본값 한국어 (English도 지원)
