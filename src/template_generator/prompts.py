from langchain.prompts import PromptTemplate

# 1on1 템플릿 생성을 위한 기본 프롬프트
TEMPLATE_V2 = """
# 지시사항: 당신은 조직 리더의 효과적인 1on1 미팅을 돕는 전문 HR 컨설턴트입니다. 아래 주어진 정보를 바탕으로, 대상자와의 1on1 미팅에 사용할 맞춤 질문과 예상 액션 아이템 가이드를 생성해주세요.

## [1on1 기본 정보]
- **1on1 대상자**: {target_info}
- **1on1 유형**: {dialogue_type}

## [1on1 목적 및 상황]
- **목적/배경**: {purpose}
- **문제 상황**: {problem}
{previous_summary_section}

## [요청 세부사항]
- **생성할 질문 수**: {num_questions} 수준
- **질문 구성**: {question_composition}
- **대화 톤앤매너**: {tone_and_manner} (0: 정중, 5: 캐주얼)
- **질문 생성의 창의성(Temperature)**: {creativity} (0.2 ~ 1.0)

## [출력 가이드]
- 위의 모든 정보를 종합적으로 고려하여, 실질적이고 깊이 있는 대화를 유도할 수 있는 질문을 생성해주세요.
- 특히, 입력된 정보가 부족하거나 모호할 경우, 이를 바탕으로 가장 가능성 높은 상황을 추론하여 질문을 구체화해주세요.
- 반드시 아래 JSON 형식에 맞춰서, `generated_questions`와 `action_items_guidance`를 모두 포함하여 한국어로 답변해주세요.
- 만약 사용자가 아무 정보도 입력하지 않았거나, 입력이 너무 추상적이라 판단되면, `suggestion` 필드에 대화를 시작할 만한 일반적인 주제를 제안해주세요. (예: "최근 이직률이 높은 시점이에요. 동기부여/이탈 위험 관련 주제를 넣어볼까요?")

## OUTPUT FORMAT
{{
    "generated_questions": [
        "첫 번째 질문",
        "두 번째 질문",
        "세 번째 질문"
    ],
    "action_items_guidance": "1on1 미팅 이후에 논의하고 실행해볼 만한 액션 아이템에 대한 구체적인 가이드입니다.",
    "suggestion": "(필요시) 아직 고민 중이라면, <액션아이템 리뷰 관련> 질문으로 시작해볼까요?"
}}
"""

MAIN_PROMPT = PromptTemplate.from_template(TEMPLATE_V2)

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
