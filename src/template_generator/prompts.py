# System prompt for 1on1 template generation
SYSTEM_PROMPT = """
You are an expert HR consultant specializing in helping organizational leaders conduct effective 1on1 meetings.

## Output Requirements:
- Generate open-ended questions that encourage detailed responses
- Avoid yes/no or one-word answer questions
- Focus on questions that prompt reflection, experiences, and opinions
- Respond in Korean with natural, conversational tone
- Follow the JSON format with generated_questions and template_summary
- For template_summary, use natural Korean expressions that sound like a real HR consultant speaking
"""

# Human prompt template for user input
HUMAN_PROMPT = """
## [1on1 Basic Information]
- **1on1 Target**: {target_info}
- **1on1 Type**: {dialogue_type}

## [1on1 Purpose and Situation]
- **Purpose/Background**: {purpose}
- **Problem Situation**: {problem}

## [Previous Meeting Context (Optional)]
{previous_summary_section}

## [Request Details]
- **Number of Questions to Generate**: {num_questions} level
  - Simple: Simple (5 questions) - Suitable for quick check-ins or when time is limited
  - Standard: 10 questions - Balanced approach for regular 1on1 meetings
  - Advanced: 15-20 questions - Comprehensive coverage for in-depth discussions or performance reviews

- **Question Composition**: {question_composition}
    - Experience/Story-based: Questions based on specific experiences or cases (e.g., "What's your most memorable project experience recently?")
    - Reflection/Thought-provoking: Questions that encourage deep thinking and self-reflection (e.g., "What part of your current role do you find most meaningful?")
    - Action/Implementation-focused: Questions focused on concrete actions and execution plans (e.g., "What specific actions will you take over the next 3 months?")
    - Relationship/Collaboration: Questions about teamwork and collaboration (e.g., "What aspect of collaboration with colleagues is most helpful?")
    - Growth/Goal-oriented: Questions about personal growth and goal setting (e.g., "What do you want to become like in a year?")
    - Multiple choice: Structured questions with predefined options (e.g., "Rate your current job satisfaction from 1-5")

- **Conversation Tone and Manner**: {tone_and_manner}
  - Formal: Very formal and professional, suitable for senior management or performance reviews
  - Casual: Casual and friendly, appropriate for close team relationships or mentoring sessions

- **Question Generation Creativity (Temperature)**: {creativity_level} (0.0 ~ 1.0)
  - 0.0-0.4: Conservative and safe questions, focused on standard topics
  - 0.5-0.7: Balanced creativity, mixing conventional and innovative approaches
  - 0.8-1.0: Highly creative and unique questions, exploring unconventional topics

    ## OUTPUT FORMAT
  {{
      "generated_questions": [
          "First question",
          "Second question", 
          "Third question"
      ],
      "template_summary": "입력해주신 정보를 바탕으로 [대상자]와의 [대화 유형] 미팅을 위한 템플릿을 준비해드렸어요. 주요 대화 주제는 [목적/배경]과 [문제 상황]을 중심으로, [질문 구성] 스타일의 질문들을 [톤앤매너]한 분위기로 구성했어요. 특히 [특정 상황이나 맥락]을 고려해서 [구체적인 대화 방향]에 초점을 맞춘 어젠다를 만들어봤습니다!"
  }}
  """



