from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.config.config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    GEMINI_MODEL,
    MAX_TOKENS,
    GEMINI_TEMPERATURE,
    GEMINI_THINKING_BUDGET,
)
from src.prompts.template_generation.prompts import SYSTEM_PROMPT, HUMAN_PROMPT
from src.utils.template_schemas import TemplateGeneratorInput, TemplateGeneratorOutput
from src.utils.utils import get_user_data_by_id


def get_template_generator_chain():
    """
    1on1 템플릿 생성을 위한 LangChain 체인을 생성합니다.
    """
    model = ChatVertexAI(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        model_name=GEMINI_MODEL,
        max_output_tokens=MAX_TOKENS,
        temperature=GEMINI_TEMPERATURE,
        model_kwargs={"thinking_budget": GEMINI_THINKING_BUDGET},
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
    chain = get_template_generator_chain()

    # user_id로 사용자 정보 가져오기
    user_data = get_user_data_by_id(input_data.user_id)
    if not user_data:
        raise ValueError(f"User with ID '{input_data.user_id}' not found.")

    # target_info가 비어있으면 DB에서 조회한 정보로 채워주기
    target_info = input_data.target_info #or f"{user_data.get('name', '')}, {user_data.get('team', '')}, {user_data.get('role', '')}"

    # '지난 기록 활용하기'가 선택되었을 경우, 이전 미팅 내용을 프롬프트에 추가
    previous_summary_section = ""
    if input_data.use_previous_data:
        history = user_data.get("one_on_one_history")
        if history:  # 기록이 있는 경우
            # 가장 최근 미팅 기록을 가져옴 (리스트의 마지막 항목)
            last_meeting = history[-1]
            summary = last_meeting.get("summary", {})
            action_items = last_meeting.get("action_items", {})

            is_korean = input_data.language.lower() == 'korean'

            # 언어 설정에 따라 동적으로 제목 설정
            title = "과거 대화 요약" if is_korean else "Previous Conversation Summary"
            done_label = "완료" if is_korean else "Done"
            todo_label = "할 일" if is_korean else "ToDo"
            pending_label = "진행 중인 액션 아이템" if is_korean else "Pending Action Items"
            completed_label = "완료된 액션 아이템" if is_korean else "Completed Action Items"

            formatted_summary = f"- **{title}**:\n"
            for topic, details in summary.items():
                formatted_summary += f"  - {topic}:\n"
                if details.get("Done"): 
                    formatted_summary += f"    - {done_label}: {', '.join(details['Done'])}\n"
                if details.get("ToDo"): 
                    formatted_summary += f"    - {todo_label}: {', '.join(details['ToDo'])}\n"

            if action_items.get("pending"): 
                formatted_summary += f"- **{pending_label}**: {', '.join(action_items['pending'])}\n"
            if action_items.get("completed"): 
                formatted_summary += f"- **{completed_label}**: {', '.join(action_items['completed'])}\n"

            previous_summary_section = formatted_summary.strip()
        else:  # 기록이 없는 경우
            is_korean = input_data.language.lower() == 'korean'
            title = "과거 대화 요약" if is_korean else "Previous Conversation Summary"
            none_text = "없음 (첫 미팅이거나 기록이 없습니다)" if is_korean else "None (This is the first meeting or no history exists)"
            previous_summary_section = f"- **{title}**: {none_text}"

    # 모든 기본값은 영어로 통일
    default_value = "Not specified"

    # 질문 구성 요소가 선택되었을 경우, 문자열로 변환
    question_composition_str = ", ".join(input_data.question_composition) if input_data.question_composition else default_value

    # 프롬프트에 전달할 변수 준비
    def safe_value(value, default=default_value):
        return value if value is not None else default
    
    # purpose 리스트를 문자열로 변환
    purpose_str = ", ".join(input_data.purpose) if input_data.purpose else default_value

    prompt_variables = {
        "target_info": target_info,
        "purpose": purpose_str,
        "detailed_context": safe_value(input_data.detailed_context),
        "dialogue_type": safe_value(input_data.dialogue_type),
        "previous_summary_section": previous_summary_section,
        "num_questions": safe_value(input_data.num_questions),
        "question_composition": question_composition_str,
        "tone_and_manner": safe_value(input_data.tone_and_manner),
        "language": safe_value(input_data.language)
    }

    # 체인 실행
    response = await chain.ainvoke(prompt_variables)
    return response
