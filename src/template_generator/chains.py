from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import JsonOutputParser

from src.config.config import GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GEMINI_MODEL, MAX_TOKENS
from src.template_generator.prompts import MAIN_PROMPT
from src.template_generator.schemas import TemplateGeneratorInput, TemplateGeneratorOutput


def get_template_generator_chain(creativity: float):
    """
    1on1 템플릿 생성을 위한 LangChain 체인을 생성합니다.
    사용자가 설정한 '창의성' 값을 LLM의 temperature로 사용합니다.
    """
    model = ChatVertexAI(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        model_name=GEMINI_MODEL,
        temperature=creativity,  # 동적으로 설정
        max_output_tokens=MAX_TOKENS,
    )
    parser = JsonOutputParser(pydantic_object=TemplateGeneratorOutput)
    chain = MAIN_PROMPT | model | parser
    return chain


async def generate_template(input_data: TemplateGeneratorInput) -> dict:
    """
    입력 데이터를 기반으로 1on1 템플릿을 비동기적으로 생성합니다.
    """
    chain = get_template_generator_chain(creativity=input_data.creativity)

    # '지난 기록 활용하기'가 선택되었고, 요약 데이터가 있을 경우 프롬프트에 추가
    previous_summary_section = ""
    if input_data.use_previous_data and input_data.previous_summary:
        previous_summary_section = f"\n- **이전 대화 요약**: {input_data.previous_summary}"

    # 질문 구성 요소가 선택되었을 경우, 문자열로 변환
    question_composition_str = ", ".join(input_data.question_composition) if input_data.question_composition else "지정되지 않음"

    # 프롬프트에 전달할 변수 준비
    prompt_variables = {
        "target_info": input_data.target_info or "정보 없음",
        "purpose": input_data.purpose or "지정되지 않음",
        "problem": input_data.problem or "지정되지 않음",
        "dialogue_type": input_data.dialogue_type,
        "previous_summary_section": previous_summary_section,
        "num_questions": input_data.num_questions,
        "question_composition": question_composition_str,
        "tone_and_manner": input_data.tone_and_manner,
    }

    # 체인 실행
    response = await chain.ainvoke(prompt_variables)
    return response
