import json
import logging
from langchain_core.prompts import ChatPromptTemplate
from src.utils.model import llm
from src.prompts.template_generation.template_prompts import SYSTEM_PROMPT, HUMAN_PROMPT
from src.utils.template_schemas import TemplateGeneratorInput, UsageGuideInput
from src.utils.utils import get_user_data_by_id
from src.services.template_generator.generate_usage_guide import generate_usage_guide
from langchain_core.output_parsers import JsonOutputParser

logging.basicConfig(level=logging.INFO)

def get_chain():
    """1on1 템플릿 생성을 위한 LangChain 체인을 생성합니다."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])
    return prompt | llm | JsonOutputParser()

chain = get_chain()

async def generate(input_data: TemplateGeneratorInput) -> dict:
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

        result = {"generated_questions": generated_questions}

        # 2. 가이드 생성 옵션 확인 및 실행
        if input_data.include_guide:
            guide_input = UsageGuideInput(
                user_id=input_data.user_id,
                target_info=input_data.target_info,
                purpose=input_data.purpose,
                detailed_context=input_data.detailed_context,
                generated_questions=generated_questions,
                language=input_data.language,
            )
            usage_guide_object = await generate_usage_guide(guide_input)
            # 객체 전체를 할당하여 프론트엔드에서 key-value로 받을 수 있도록 합니다.
            result["usage_guide"] = usage_guide_object
        
        return result

    except Exception as e:
        logging.error(f"Error during generation: {e}")
        raise
