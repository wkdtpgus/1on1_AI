from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.config.config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    GEMINI_MODEL,
    MAX_TOKENS,
    GEMINI_TEMPERATURE,
    GEMINI_THINKING_BUDGET,
)
from src.prompts.summary_generation.prompts import SYSTEM_PROMPT, HUMAN_PROMPT
from src.utils.summary_schemas import SummaryGeneratorOutput
from src.utils.template_schemas import TemplateGeneratorInput
from src.utils.utils import get_user_data_by_id

def get_summary_generator_chain():
    """
    1on1 템플릿 요약 생성을 위한 LangChain 체인을 생성합니다.
    """
    model = ChatVertexAI(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        model_name=GEMINI_MODEL,
        max_output_tokens=MAX_TOKENS,
        temperature=GEMINI_TEMPERATURE,
        model_kwargs={"thinking_budget": GEMINI_THINKING_BUDGET},
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])
    
    parser = JsonOutputParser(pydantic_object=SummaryGeneratorOutput)
    chain = prompt | model | parser
    return chain

async def generate_summary(input_data: TemplateGeneratorInput) -> dict:
    """
    입력 데이터를 기반으로 1on1 템플릿 요약을 비동기적으로 생성합니다.
    """
    chain = get_summary_generator_chain()

    user_data = get_user_data_by_id(input_data.user_id)
    if not user_data:
        raise ValueError(f"User with ID '{input_data.user_id}' not found.")

    target_info = input_data.target_info or f"{user_data.get('name', '')}, {user_data.get('team', '')}, {user_data.get('role', '')}"

    previous_summary_section = ""
    if input_data.use_previous_data and user_data.get("one_on_one_history"):
        last_meeting = user_data["one_on_one_history"][-1]
        summary = last_meeting.get("summary", {})
        action_items = last_meeting.get("action_items", {})
        formatted_summary = "- **이전 대화 요약**:\n"
        for topic, details in summary.items():
            formatted_summary += f"  - {topic}:\n"
            if details.get("Done"): formatted_summary += f"    - Done: {', '.join(details['Done'])}\n"
            if details.get("ToDo"): formatted_summary += f"    - ToDo: {', '.join(details['ToDo'])}\n"
        if action_items.get("pending"): formatted_summary += f"- **미완료된 Action Items**: {', '.join(action_items['pending'])}\n"
        if action_items.get("completed"): formatted_summary += f"- **완료된 Action Items**: {', '.join(action_items['completed'])}\n"
        previous_summary_section = formatted_summary.strip()
    elif input_data.use_previous_data:
        previous_summary_section = "- **이전 대화 요약**: 없음"

    def safe_value(value, default="지정되지 않음"):
        return value if value is not None else default

    purpose_str = ", ".join(input_data.purpose) if input_data.purpose else "지정되지 않음"

    prompt_variables = {
        "target_info": target_info,
        "purpose": purpose_str,
        "detailed_context": safe_value(input_data.detailed_context),
        "dialogue_type": safe_value(input_data.dialogue_type),
        "previous_summary_section": previous_summary_section,
    }

    response = await chain.ainvoke(prompt_variables)
    return response
