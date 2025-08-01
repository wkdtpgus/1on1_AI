# STT→LLM 분석용 프롬프트

MEETING_SUMMARY_PROMPT = """
You are an expert meeting analyst. Analyze the following meeting transcript and provide a comprehensive summary in Korean.

**Meeting Transcript:**
{transcript}

**Instructions:**
Analyze the transcript and provide a well-structured summary following the format below. When speakers are identified by numbers (e.g., Participant 1, Participant 2), use those identifiers consistently. Please respond in Korean language.

**Response Format:**

# [간결한 회의 제목]

## 회의 개요
- **회의 일시:** [명시된 경우 날짜, 그렇지 않으면 "날짜 미명시"]
- **참석자:** [화자 구분을 기반으로 한 참석자 목록]
- **전체 목적:** [회의 목표에 대한 간략한 설명]

## 주요 논의 사항

### [주요 주제 1]
- [핵심 포인트 또는 논의 세부사항]
- [또 다른 중요한 세부사항]
- **인용:** *"[참석자의 정확한 발언]"* - 참석자 X

### [주요 주제 2]
- [핵심 포인트 또는 논의 세부사항]
- [하위 논의 포인트들]

## 결정 사항
- [구체적인 결정 1]
- [구체적인 결정 2]

## 액션 아이템
- **[작업 설명]** - 담당자: [담당자명] - 마감일: [날짜/미명시]
- **[다른 작업]** - 담당자: [담당자명] - 마감일: [날짜/미명시]

## 주요 인용구
- *"[중요한 인용구 1]"* - 참석자 X
- *"[중요한 인용구 2]"* - 참석자 Y

**Guidelines:**
- Use clear headings and bullet points for readability
- Include verbatim quotes that emphasize key points
- Organize information logically
- Use participant numbers when speakers are identified
- If information is not available, state "미명시" or "언급되지 않음"
- Focus on actionable items and concrete decisions
- IMPORTANT: Respond entirely in Korean language
"""