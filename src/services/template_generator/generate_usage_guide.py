import logging
import json
from typing import AsyncGenerator

from langchain_core.prompts import ChatPromptTemplate

from src.prompts.template_generation.guide_prompts import HUMAN_PROMPT, SYSTEM_PROMPT
from src.utils.model import llm
from src.utils.schemas import UsageGuideInput


def get_usage_guide_chain():
    """
    1on1 템플릿 활용 가이드 생성을 위한 LangChain 체인을 생성합니다.
    스트리밍을 위해 JsonOutputParser를 제거합니다.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT),
        ]
    )
    return prompt | llm


async def generate_usage_guide(guide_input: UsageGuideInput) -> AsyncGenerator[str, None]:
    """
    입력 데이터를 기반으로 활용 가이드를 스트리밍으로 생성합니다.
    """
    chain = get_usage_guide_chain()
    
    prompt_variables = {
        "target_info": guide_input.target_info,
        "purpose": guide_input.purpose,
        "detailed_context": guide_input.detailed_context,
        "questions": "\n".join(
            [f"{num}. {text}" for num, text in guide_input.generated_questions.items()]
        ),
        "language": guide_input.language
    }
    
    try:
        async for chunk in chain.astream(prompt_variables):
            if chunk.content:
                # 각 청크의 내용을 SSE 형식으로 포장하여 스트리밍
                # ensure_ascii=False로 한글이 제대로 표시되도록 설정
                yield f"data: {json.dumps(chunk.content, ensure_ascii=False)}\n\n"
    except Exception as e:
        error_message = f"Error during stream generation: {e}"
        logging.error(error_message)
        # 클라이언트에 오류 메시지 전달
        yield f"data: {json.dumps({'error': error_message}, ensure_ascii=False)}\n\n"