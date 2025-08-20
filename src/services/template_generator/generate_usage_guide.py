from langchain_core.prompts import ChatPromptTemplate
import json
from src.utils.model import llm_streaming
from src.prompts.template_generation.guide_prompts import SYSTEM_PROMPT, HUMAN_PROMPT
from src.utils.template_schemas import UsageGuideInput
from typing import AsyncGenerator

def get_usage_guide_chain():
    """
    1on1 템플릿 활용 가이드 생성을 위한 LangChain 체인을 생성합니다.
    (스트리밍, 단일 체인)
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT),
        ]
    )
    # JsonOutputParser를 사용하지 않고 순수한 텍스트 스트림을 받습니다.
    return prompt | llm_streaming

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
                # SSE 형식으로 포장하여 스트리밍
                yield f"data: {json.dumps(chunk.content, ensure_ascii=False)}\n\n"
    except Exception as e:
        error_message = f"Error during usage guide generation: {e}"
        yield f"data: {json.dumps({'error': error_message}, ensure_ascii=False)}\n\n"