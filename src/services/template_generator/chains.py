from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.config.config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    GEMINI_MODEL,
    MAX_TOKENS,
    GEMINI_TEMPERATURE,
)
from src.prompts.template_generation.prompts import SYSTEM_PROMPT, HUMAN_PROMPT
from src.utils.template_schemas import TemplateGeneratorInput, TemplateGeneratorOutput
from src.utils.utils import get_user_data_by_id


def get_template_generator_chain():
    """
    1on1 템플릿 생성을 위한 LangChain 체인을 생성합니다.
    """
    model = ChatVertexAI(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        model_name=GEMINI_MODEL,
        max_output_tokens=MAX_TOKENS,
        temperature=GEMINI_TEMPERATURE,
    )
    # System and Human prompt를 결합한 ChatPromptTemplate 생성
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])
    
    parser = JsonOutputParser(pydantic_object=TemplateGeneratorOutput)
    chain = prompt | model | parser
    return chain


async def generate_template(input_data: TemplateGeneratorInput) -> dict:
    """
    입력 데이터를 기반으로 1on1 템플릿을 비동기적으로 생성합니다.
    """
    chain = get_template_generator_chain()

    # user_id로 사용자 정보 가져오기
    user_data = get_user_data_by_id(input_data.user_id)
    if not user_data:
        raise ValueError(f"User with ID '{input_data.user_id}' not found.")

    # target_info가 비어있으면 DB에서 조회한 정보로 채워주기
    target_info = input_data.target_info
    if not target_info:
        target_info = f"{user_data.get('name', '')}, {user_data.get('team', '')}, {user_data.get('role', '')}"

    # '지난 기록 활용하기'가 선택되었을 경우, 이전 미팅 내용을 프롬프트에 추가
    previous_summary_section = ""
    if input_data.use_previous_data:
        history = user_data.get("one_on_one_history")
        if history:  # 기록이 있는 경우
            # 가장 최근 미팅 기록을 가져옴 (리스트의 마지막 항목)
            last_meeting = history[-1]
            summary = last_meeting.get("summary", {})
            action_items = last_meeting.get("action_items", {})

            # 요약 및 액션 아이템을 한국어로 포맷팅
            formatted_summary = "- **이전 대화 요약**:\n"
            for topic, details in summary.items():
                formatted_summary += f"  - {topic}:\n"
                if details.get("Done"):
                    formatted_summary += f"    - Done: {', '.join(details['Done'])}\n"
                if details.get("ToDo"):
                    formatted_summary += f"    - ToDo: {', '.join(details['ToDo'])}\n"

            if action_items.get("pending"):
                formatted_summary += "- **미완료된 Action Items**: " + ", ".join(action_items["pending"]) + "\n"
            if action_items.get("completed"):
                formatted_summary += "- **완료된 Action Items**: " + ", ".join(action_items["completed"]) + "\n"

            previous_summary_section = formatted_summary.strip()
        else:  # 기록이 없는 경우
            previous_summary_section = "- **이전 대화 요약**: 없음 (첫 번째 미팅이거나 이전 기록이 없음)"

    # 질문 구성 요소가 선택되었을 경우, 문자열로 변환
    question_composition_str = ", ".join(input_data.question_composition) if input_data.question_composition else "지정되지 않음"

    # 프롬프트에 전달할 변수 준비
    def safe_value(value, default="지정되지 않음"):
        return value if value is not None else default
    
    # purpose 리스트를 문자열로 변환
    purpose_str = ", ".join(input_data.purpose) if input_data.purpose else "지정되지 않음"

    prompt_variables = {
        "target_info": target_info,
        "purpose": purpose_str,
        "detailed_context": safe_value(input_data.detailed_context),
        "dialogue_type": safe_value(input_data.dialogue_type),
        "previous_summary_section": previous_summary_section,
        "num_questions": safe_value(input_data.num_questions),
        "question_composition": question_composition_str,
        "tone_and_manner": safe_value(input_data.tone_and_manner)
    }

    # 체인 실행
    response = await chain.ainvoke(prompt_variables)
    return response
