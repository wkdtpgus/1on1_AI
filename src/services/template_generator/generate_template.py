import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.prompts.template_generation.template_prompts import HUMAN_PROMPT, SYSTEM_PROMPT
from src.utils.model import llm
from src.utils.template_schemas import TemplateGeneratorInput, TemplateGeneratorOutput
from src.utils.utils import get_user_data_by_id

logger = logging.getLogger("template_generator")

def get_chain():
    """1on1 템플릿 생성을 위한 LangChain 체인을 생성합니다."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])
    return prompt | llm | JsonOutputParser()

chain = get_chain()

async def generate_template(input_data: TemplateGeneratorInput) -> TemplateGeneratorOutput:
    """
    사용자 입력을 기반으로 1on1 템플릿 질문을 생성합니다.
    옵션에 따라 활용 가이드도 이어서 생성합니다.
    """
    user_data = get_user_data_by_id(input_data.user_id)
    if not user_data:
        raise ValueError(f"User with ID '{input_data.user_id}' not found.")

    previous_summary_section = ""
    if input_data.use_previous_data and input_data.previous_summary:
        previous_summary_section = input_data.previous_summary

    prompt_variables = {
        "target_info": input_data.target_info,
        "purpose": input_data.purpose,
        "detailed_context": input_data.detailed_context,
        "previous_summary_section": previous_summary_section,
        "num_questions": input_data.num_questions,
        "question_composition": input_data.question_composition,
        "tone_and_manner": input_data.tone_and_manner,
        "language": input_data.language
    }

    try:
        # 1. 템플릿 질문 생성
        generated_questions = await chain.ainvoke(prompt_variables)
        if not generated_questions:
            raise ValueError("Failed to generate questions.")

        # API 계약에 따라 순수한 질문 딕셔너리만 반환합니다.
        # 가이드 생성은 'guide' generation_type으로 분리되어 처리됩니다.
        return TemplateGeneratorOutput(generated_questions=generated_questions)

    except Exception as e:
        logger.error(f"Error during template generation: {e}")
        raise
