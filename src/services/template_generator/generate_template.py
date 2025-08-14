import logging
import json
# import re
from typing import AsyncIterable
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from src.utils.model import llm_streaming
from src.prompts.template_generation.prompts import SYSTEM_PROMPT, HUMAN_PROMPT
from src.utils.template_schemas import TemplateGeneratorInput
from src.utils.utils import get_user_data_by_id

logging.basicConfig(level=logging.INFO)

def get_streaming_chain():
    """1on1 템플릿 생성을 위한 스트리밍 LangChain 체인을 생성합니다."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])
    return prompt | llm_streaming

chain = get_streaming_chain()

@traceable(run_type="llm", name="generate_template")
async def generate_template(input_data: TemplateGeneratorInput) -> AsyncIterable[str]:
    """
    입력 데이터를 기반으로 1on1 템플릿을 스트리밍 방식으로 비동기적으로 생성합니다.
    """

    user_data = get_user_data_by_id(input_data.user_id)
    if not user_data:
        raise ValueError(f"User with ID '{input_data.user_id}' not found.")

    # '지난 기록 활용하기'가 선택되었을 경우, 이전 미팅 내용을 프롬프트에 추가
    # use_previous_data가 True이고 previous_summary가 있을 때만 사용
    previous_summary_section = ""
    if input_data.use_previous_data and input_data.previous_summary:
        previous_summary_section = input_data.previous_summary

    prompt_variables = {
        # 스키마에서 필수값과 기본값이 이미 설정되어 있어서 직접 사용
        "target_info": input_data.target_info,
        "purpose": input_data.purpose,
        "detailed_context": input_data.detailed_context,

        "previous_summary_section": previous_summary_section,
        "num_questions": input_data.num_questions,
        "question_composition": input_data.question_composition,
        "tone_and_manner": input_data.tone_and_manner,
        "language": input_data.language
    }

    #응답 스트리밍처리(Stream the response from the chain)
    # LLM에서 생성되는 콘텐츠 청크를 받아 즉시 클라이언트로 전달
    # 이 방식은 클라이언트에서 한 글자씩 또는 단어씩 렌더링
    try:
        # 스트리밍 응답을 모아서 하나의 완전한 JSON으로 만들기
        full_response = ""
        async for chunk in chain.astream(prompt_variables):
            if chunk.content:
                # 각 청크의 내용을 SSE 형식으로 포장하여 스트리밍
                # ensure_ascii=False로 한글이 제대로 표시되도록 설정
                yield f"data: {json.dumps(chunk.content, ensure_ascii=False)}\n\n"
    except Exception as e:
        error_message = f"Error during stream generation: {e}"
        # 클라이언트에 오류 메시지 전달
        yield f"data: {json.dumps({'error': error_message}, ensure_ascii=False)}\n\n"
