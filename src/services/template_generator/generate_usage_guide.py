from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.utils.model import llm
from src.prompts.template_generation.guide_prompts import SYSTEM_PROMPT, HUMAN_PROMPT
from src.utils.template_schemas import UsageGuideInput, UsageGuideOutput

def get_usage_guide_chain():
    """
    1on1 템플릿 활용 가이드 생성을 위한 LangChain 체인을 생성합니다.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT),
        ]
    )
    # LLM의 JSON 응답을 딕셔너리로 파싱하도록 JsonOutputParser를 사용합니다.
    return prompt | llm | JsonOutputParser()

async def generate_usage_guide(guide_input: UsageGuideInput) -> UsageGuideOutput:
    """
    입력 데이터를 기반으로 활용 가이드를 생성합니다.
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
        # 체인이 반환하는 것은 이제 텍스트가 아닌 파싱된 딕셔너리입니다.
        guide_data = await chain.ainvoke(prompt_variables)
        
        # 딕셔너리에서 실제 가이드 텍스트를 추출합니다.
        # 만약 'usage_guide' 키가 없거나 파싱에 실패하면 빈 문자열을 사용합니다.
        guide_text = guide_data.get("usage_guide", "") if isinstance(guide_data, dict) else str(guide_data)
        
        return UsageGuideOutput(usage_guide=guide_text)
    except Exception as e:
        # logging 추가
        import logging
        logging.error(f"Error during usage guide generation: {e}")
        raise