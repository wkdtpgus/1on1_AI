from typing import AsyncIterable
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from src.config.config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    GEMINI_MODEL,
    MAX_TOKENS,
    GEMINI_TEMPERATURE,
    GEMINI_THINKING_BUDGET,
)
from src.prompts.template_generation.prompts import SYSTEM_PROMPT, HUMAN_PROMPT
from src.utils.template_schemas import TemplateGeneratorInput
from src.utils.utils import get_user_data_by_id

def get_streaming_chain_v2():
    """1on1 템플릿 생성을 위한 스트리밍 LangChain 체인을 생성합니다. (v2)"""
    model = ChatVertexAI(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        model_name=GEMINI_MODEL,
        max_output_tokens=MAX_TOKENS,
        temperature=GEMINI_TEMPERATURE,
        model_kwargs={"thinking_budget": GEMINI_THINKING_BUDGET},
        streaming=True,  # 스트리밍 활성화
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])
    return prompt | model

streaming_chain_v2 = get_streaming_chain_v2()

@traceable(run_type="llm", name="generate_template_streaming_v2")
async def generate_template_streaming_v2(input_data: TemplateGeneratorInput) -> AsyncIterable[str]:
    """
    입력 데이터를 기반으로 1on1 템플릿을 스트리밍 방식으로 비동기적으로 생성합니다. (v2)
    """

    user_data = get_user_data_by_id(input_data.user_id)
    if not user_data:
        raise ValueError(f"User with ID '{input_data.user_id}' not found.")

    target_info = input_data.target_info

    previous_summary_section = ""
    if input_data.use_previous_data:
        history = user_data.get("one_on_one_history")
        if history:
            latest_history = history[-1]
            done_items = latest_history.get("action_items", {}).get("Done", [])
            todo_items = latest_history.get("action_items", {}).get("ToDo", [])
            done_section = f"  - Done: {', '.join(done_items) if done_items else 'None'}"
            todo_section = f"  - ToDo: {', '.join(todo_items) if todo_items else 'None'}"
            previous_summary_section = (
                f"<Previous Conversation Summary>\n"
                f"- Date: {latest_history['date']}\n"
                f"- Summary: {latest_history['summary']}\n"
                f"- Action Items:\n"
                f"{done_section}\n"
                f"{todo_section}"
            )
        else:
            previous_summary_section = "None (This is the first meeting or no history exists)"

    default_value = "Not specified"
    question_composition_str = ", ".join(input_data.question_composition) if input_data.question_composition else default_value

    def safe_value(value, default=default_value):
        return value if value is not None else default
    
    purpose_str = ", ".join(input_data.purpose) if input_data.purpose else default_value

    prompt_variables = {
        "target_info": target_info,
        "purpose": purpose_str,
        "detailed_context": safe_value(input_data.detailed_context),
        "dialogue_type": safe_value(input_data.dialogue_type),
        "previous_summary_section": previous_summary_section,
        "num_questions": safe_value(input_data.num_questions),
        "question_composition": question_composition_str,
        "tone_and_manner": safe_value(input_data.tone_and_manner),
        "language": safe_value(input_data.language)
    }

    async for chunk in streaming_chain_v2.astream(prompt_variables):
        yield chunk.content
