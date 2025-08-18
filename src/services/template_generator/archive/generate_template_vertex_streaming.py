from typing import AsyncIterator

import vertexai
from langsmith import traceable
from vertexai.generative_models import GenerativeModel, Part

from src.config.config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE,
)
from src.prompts.template_generation.prompts import HUMAN_PROMPT, SYSTEM_PROMPT
from src.utils.template_schemas import TemplateGeneratorInput
from src.utils.utils import get_user_data_by_id

# Vertex AI 초기화
vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)

# 스트리밍을 위한 모델 직접 초기화
streaming_model = GenerativeModel(GEMINI_MODEL)


@traceable(run_type="llm", name="generate_template_streaming")
async def generate_template_streaming(input_data: TemplateGeneratorInput) -> AsyncIterator[str]:
    """
    입력 데이터를 기반으로 1on1 템플릿을 비동기적으로 생성합니다.
    """

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
            latest_history = history[-1]
            done_items = latest_history.get("action_items", {}).get("Done", [])
            todo_items = latest_history.get("action_items", {}).get("ToDo", [])

            # 프롬프트가 언어를 처리하므로 간단한 형식으로 전달
            done_section = f"  - Done: {', '.join(done_items) if done_items else 'None'}"
            todo_section = f"  - ToDo: {', '.join(todo_items) if todo_items else 'None'}"

            previous_summary_section = (
                f"<Previous Conversation Summary>\n"
                f"- Date: {latest_history['date']}\n"
                f"- Summary: {latest_history['summary']}\n"
                f"- Action Items:\n"
                f"{done_section}\n"
                f"{todo_section}"
            )
        else: # 기록이 없는 경우
            previous_summary_section = "None (This is the first meeting or no history exists)"

    # default_value 설정
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

    # Google SDK에 맞는 형식으로 프롬프트 구성
    formatted_human_prompt = HUMAN_PROMPT.format(**prompt_variables)
    contents = [Part.from_text(formatted_human_prompt)]

    # 생성 설정
    generation_config = {
        "max_output_tokens": GEMINI_MAX_TOKENS,
        "temperature": GEMINI_TEMPERATURE,
    }

    # 모델의 generate_content_async를 직접 호출하여 스트리밍
    responses = streaming_model.generate_content(
        contents,
        generation_config=generation_config,
        stream=True,
    )

    for response in responses:
        try:
            yield response.text
        except Exception:
            # 일부 청크에 텍스트가 없을 수 있으므로 오류 발생 시 무시
            pass
