import logging
import json
import re
from typing import AsyncIterable
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
# streaming true공통설정 따로 빼두기
# Configure basic logging to see INFO level messages
logging.basicConfig(level=logging.INFO)

from src.config.template_config import (
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

def get_streaming_chain():
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

chain = get_streaming_chain()

@traceable(run_type="llm", name="generate_template")
async def generate_template(input_data: TemplateGeneratorInput) -> AsyncIterable[str]:
    """
    입력 데이터를 기반으로 1on1 템플릿을 스트리밍 방식으로 비동기적으로 생성합니다.
    """

    user_data = get_user_data_by_id(input_data.user_id)
    if not user_data:
        raise ValueError(f"User with ID '{input_data.user_id}' not found.")

    # target_info가 비어있으면 DB에서 조회한 정보로 채워주기
    # (비활)
    target_info = input_data.target_info

    # '지난 기록 활용하기'가 선택되었을 경우, 이전 미팅 내용을 프롬프트에 추가
    # 여기서 받기만하고 테스트파일에서 만들어야함(더미데이터활용하는것이기 때문) - 프론트에서 묶어서 매핑할 수 없음
    previous_summary_section = ""
    if input_data.use_previous_data:
        history = user_data.get("one_on_one_history")
        if history: #기록이 있는 경우
            latest_history = history[-1]
            done_items = latest_history.get("action_items", {}).get("Done", [])
            todo_items = latest_history.get("action_items", {}).get("ToDo", [])

            #프롬프트 전달을 위한 간단한 형식으로 변환
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
        else: #기록이 없는 경우
            previous_summary_section = "None (This is the first meeting or no history exists)"

    #default_value 설정
    default_value = "Not specified"

    # 프롬프트에 전달할 변수 준비
    def safe_value(value, default=default_value):
        return value if value is not None else default

    # purpose list, 질문 구성요소 list가 선택되었을 경우, 문자열로 변환
    # 여기서 받기만하고 테스트파일에서 만들어야함(문자열처리는 메인파일에서 금지)
    purpose_str = ", ".join(input_data.purpose) if input_data.purpose else default_value
    question_composition_str = ", ".join(input_data.question_composition) if input_data.question_composition else default_value

    prompt_variables = {
        #필수값만 남기기 - 필수는 safe_value로 처리
        #
        "target_info": safe_value(input_data.target_info),
        "purpose": purpose_str,
        "detailed_context": safe_value(input_data.detailed_context),
        "dialogue_type": safe_value(input_data.dialogue_type),
        "previous_summary_section": previous_summary_section,
        "num_questions": safe_value(input_data.num_questions),
        "question_composition": question_composition_str,
        "tone_and_manner": safe_value(input_data.tone_and_manner),
        "language": safe_value(input_data.language)
    }

    #응답 스트리밍처리
    # LLM에서 생성되는 콘텐츠 청크를 받아 즉시 클라이언트로 전달합니다.
    # 이 방식은 클라이언트에서 한 글자씩 또는 단어씩 렌더링되어
    # Stream the response from the chain
    try:
        async for chunk in chain.astream(prompt_variables):
            if chunk.content:
                # 각 청크의 내용을 SSE 형식으로 포장하여 스트리밍합니다.
                yield f"data: {json.dumps(chunk.content)}\n\n"
    except Exception as e:
        error_message = f"Error during stream generation: {e}"
        # Yield a formatted error message to the client
        yield f"data: {json.dumps({'error': error_message})}\n\n"
