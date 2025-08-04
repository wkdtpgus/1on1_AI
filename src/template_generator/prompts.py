from langchain.prompts import PromptTemplate

# 1on1 템플릿 생성을 위한 기본 프롬프트
TEMPLATE_GENERATION_PROMPT = PromptTemplate.from_template(
    """당신은 전문적인 HR 컨설턴트이자 커리어 코치입니다.
    리더가 팀원과 성공적인 1on1 미팅을 할 수 있도록, 아래 정보를 바탕으로 맞춤형 질문과 액션 아이템 가이드를 생성해주세요.

    **1. 1on1 기본 정보:**
    - **대상자:** {target_info}
    - **대화 목적:** {purpose}
    - **주요 이슈:** {problem}
    {previous_summary_section}

    **2. 요청 사항:**
    - **질문 수:** {num_questions}
    - **질문 유형:** {question_composition}
    - **대화 톤앤매너:** {tone_and_manner}

    **3. 결과물:**
    - 위 정보를 모두 고려하여, 대상자와의 1on1 미팅에서 바로 사용할 수 있는 창의적이고 깊이 있는 질문 목록을 생성해주세요.
    - 질문 후 어떤 액션 아이템을 도출하면 좋을지 구체적인 가이드를 제시해주세요.

    **출력 형식:**
    반드시 아래와 같은 JSON 형식으로만 응답해주세요. 다른 설명은 추가하지 마세요.
    {{
        "generated_questions": [
            "첫 번째 질문",
            "두 번째 질문",
            "..."
        ],
        "action_items_guidance": "액션 아이템 도출을 위한 상세 가이드"
    }}
    """
)

# 입력이 부족할 때를 위한 제안 프롬프트
SUGGESTION_PROMPT = PromptTemplate.from_template(
    """당신은 사용자의 의도를 파악하는 AI 어시스턴트입니다.
    사용자가 1on1 템플릿 생성을 요청했지만, 정보가 부족합니다.
    아래 정보를 바탕으로 사용자에게 어떤 주제를 추가하면 좋을지 한 문장으로 제안해주세요.

    - **대상자:** {target_info}
    - **이전 대화 요약:** {previous_summary}

    **제안 예시:**
    - "최근 성과 리뷰 시즌인데, <성과 평가 및 목표 설정> 관련 질문을 추가해볼까요?"
    - "팀의 협업 방식에 변화가 있었나요? <팀워크 및 협업> 관련 주제를 넣어볼까요?"

    **사용자에게 할 제안:**
    """
)
