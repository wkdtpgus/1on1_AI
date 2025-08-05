from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.config.config import GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GEMINI_MODEL, MAX_TOKENS
from src.template_generator.prompts import SYSTEM_PROMPT, HUMAN_PROMPT
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
    
    # System and Human prompt를 결합한 ChatPromptTemplate 생성
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])
    
    parser = JsonOutputParser(pydantic_object=TemplateGeneratorOutput)
    chain = prompt | model | parser
    return chain


async def generate_template(input_data: TemplateGeneratorInput) -> dict:
    """
    입력 데이터를 기반으로 1on1 템플릿을 비동기적으로 생성합니다.
    """
    chain = get_template_generator_chain(creativity=input_data.creativity)

    # '지난 기록 활용하기'가 선택되었고, 요약 데이터가 있을 경우 프롬프트에 추가
    previous_summary_section = ""
    if input_data.use_previous_data and input_data.previous_summary:
        previous_summary_section = f"- **이전 대화 요약**: {input_data.previous_summary}"
    elif input_data.use_previous_data:
        previous_summary_section = "- **이전 대화 요약**: 없음 (첫 번째 미팅이거나 이전 기록이 없음)"
    else:
        previous_summary_section = ""

    # 질문 구성 요소가 선택되었을 경우, 문자열로 변환
    question_composition_str = ", ".join(input_data.question_composition) if input_data.question_composition else "지정되지 않음"

    # 프롬프트에 전달할 변수 준비
    def safe_value(value, default="지정되지 않음"):
        return value if value is not None else default
    
    prompt_variables = {
        "target_info": safe_value(input_data.target_info),
        "purpose": safe_value(input_data.purpose),
        "problem": safe_value(input_data.problem),
        "dialogue_type": safe_value(input_data.dialogue_type),
        "previous_summary_section": previous_summary_section,
        "num_questions": safe_value(input_data.num_questions),
        "question_composition": question_composition_str,
        "tone_and_manner": safe_value(input_data.tone_and_manner),
        "creativity_level": safe_value(input_data.creativity),
    }

    # 체인 실행
    response = await chain.ainvoke(prompt_variables)
    return response
