from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.prompts.template_generation.email_prompts import HUMAN_PROMPT, SYSTEM_PROMPT
from src.utils.model import llm
from src.utils.template_schemas import EmailGeneratorInput, EmailGeneratorOutput
from src.utils.utils import get_user_data_by_id

def get_email_generator_chain():
    """
    1on1 템플릿 요약 생성을 위한 LangChain 체인을 생성합니다.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])
    
    parser = JsonOutputParser(pydantic_object=EmailGeneratorOutput)
    chain = prompt | llm | parser
    return chain

async def generate_email(input_data: EmailGeneratorInput) -> EmailGeneratorOutput:
    """
    입력 데이터를 기반으로 1on1 템플릿 요약을 비동기적으로 생성합니다.
    """
    chain = get_email_generator_chain()

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
        "language": input_data.language,
    }

    response = await chain.ainvoke(prompt_variables)
    return EmailGeneratorOutput(**response)
