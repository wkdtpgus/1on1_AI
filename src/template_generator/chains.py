from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import JsonOutputParser

from src.config.config import GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GEMINI_MODEL, GEMINI_TEMPERATURE, MAX_TOKENS
from src.template_generator.prompts import TEMPLATE_GENERATION_PROMPT
from src.template_generator.schemas import TemplateGeneratorInput, TemplateGeneratorOutput


def get_template_generator_chain():
    """
    1on1 템플릿 생성을 위한 기본 LangChain 체인을 생성합니다.
    """
    # 1. LLM 모델 초기화
    # Vertex AI 모델을 사용하도록 LLM을 초기화합니다.
    # config.py에 설정된 값들을 사용합니다.
    model = ChatVertexAI(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        model_name=GEMINI_MODEL,
        temperature=GEMINI_TEMPERATURE,
        max_output_tokens=MAX_TOKENS,
    )

    # 2. 출력 파서 설정
    # Pydantic 모델을 사용하여 LLM의 출력을 JSON으로 파싱하고 검증합니다.
    parser = JsonOutputParser(pydantic_object=TemplateGeneratorOutput)

    # 3. 프롬프트, 모델, 파서를 하나의 체인으로 연결
    chain = TEMPLATE_GENERATION_PROMPT | model | parser
    
    return chain


async def generate_template(input_data: TemplateGeneratorInput) -> dict:
    """
    입력 데이터를 기반으로 1on1 템플릿을 비동기적으로 생성합니다.
    """
    chain = get_template_generator_chain()
    
    # 이전 1on1 요약이 있는 경우 프롬프트에 추가
    if input_data.previous_summary:
        previous_summary_section = f"\n    - **이전 대화 요약:** {input_data.previous_summary}"
    else:
        previous_summary_section = ""

    # 체인 실행
    response = await chain.ainvoke({
        "target_info": input_data.target_info,
        "purpose": input_data.purpose or "지정되지 않음",
        "problem": input_data.problem or "지정되지 않음",
        "previous_summary_section": previous_summary_section,
        "num_questions": input_data.num_questions,
        "question_composition": input_data.question_composition,
        "tone_and_manner": input_data.tone_and_manner,
    })
    
    return response
