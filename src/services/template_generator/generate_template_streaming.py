import os
import json
import tempfile
from typing import AsyncIterator

import streamlit as st
from langsmith import traceable

from src.config.config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    GEMINI_MODEL,
    MAX_TOKENS,
    GEMINI_TEMPERATURE,
)
from src.prompts.template_generation.prompts import HUMAN_PROMPT
from src.utils.template_schemas import TemplateGeneratorInput
from src.utils.utils import get_user_data_by_id


@traceable(run_type="llm", name="generate_template_streaming")
async def generate_template_streaming(input_data: TemplateGeneratorInput) -> AsyncIterator[str]:
    """
    입력 데이터를 기반으로 1on1 템플릿을 비동기적으로 생성합니다.
    google-auth 라이브러리를 사용해 수동으로 인증 정보를 로드하여 문제를 해결합니다.
    """
    temp_creds_path = None
    credentials = None
    try:
        # 1. Streamlit secrets에서 인증 정보를 가져와 임시 파일로 저장
        if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
            gcp_creds_dict = dict(st.secrets["gcp_service_account"])
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_creds_file:
                json.dump(gcp_creds_dict, temp_creds_file)
                temp_creds_path = temp_creds_file.name

        # 2. 라이브러리 지연 임포트 및 수동 인증
        import vertexai
        import google.auth
        from vertexai.generative_models import GenerativeModel, Part

        if temp_creds_path:
            credentials, _ = google.auth.load_credentials_from_file(temp_creds_path)
        
        # 3. Vertex AI 초기화 전, 인증 정보 존재 여부 강제 확인
        if not credentials:
            raise ValueError(
                "GCP credentials could not be loaded. "
                "Please check Streamlit secrets configuration."
            )

        # --- DIAGNOSTIC CODE START ---
        print("Attempting to authenticate with Google Cloud Storage to verify credentials...")
        try:
            from google.cloud import storage
            storage_client = storage.Client(
                project=GOOGLE_CLOUD_PROJECT,
                credentials=credentials
            )
            buckets = list(storage_client.list_buckets(max_results=1))
            print(f"SUCCESS: Successfully authenticated and listed buckets. Found: {buckets}")
        except Exception as e:
            print(f"ERROR: Failed to authenticate with Google Cloud Storage. Error: {e}")
        # --- DIAGNOSTIC CODE END ---

        vertexai.init(
            project=GOOGLE_CLOUD_PROJECT, 
            location=GOOGLE_CLOUD_LOCATION, 
            credentials=credentials
        )

        # 4. 모델 초기화
        streaming_model = GenerativeModel(GEMINI_MODEL)

        # 5. 프롬프트 변수 준비
        target_info = input_data.target_info
        previous_summary_section = ""

        print(f"[DIAGNOSTIC] generate_template_streaming: Checking user_id: '{input_data.user_id}' (type: {type(input_data.user_id)})")
        user_data = None
        if input_data.user_id and input_data.user_id.strip().lower() != "default_user":
            # 실제 사용자인 경우, 데이터베이스에서 정보를 가져옴
            user_data = get_user_data_by_id(input_data.user_id)
            if not user_data:
                raise ValueError(f"User with ID '{input_data.user_id}' not found.")

            # target_info가 비어있으면 사용자 정보로 채움
            if not target_info:
                target_info = f"{user_data.get('name', '')}, {user_data.get('team', '')}, {user_data.get('role', '')}"

            # 이전 대화 기록 처리
            if input_data.use_previous_data and user_data.get("one_on_one_history"):
                history = user_data.get("one_on_one_history")
                latest_history = history[-1]
                done_items = latest_history.get("action_items", {}).get("Done", [])
                todo_items = latest_history.get("action_items", {}).get("ToDo", [])
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
            else:
                previous_summary_section = "None (This is the first meeting or no history exists)"
        else:
            # 'default_user' 또는 ID가 없는 경우
            previous_summary_section = "None (This is the first meeting or no history exists)"

        default_value = "Not specified"
        question_composition_str = ", ".join(input_data.question_composition) if input_data.question_composition else default_value
        purpose_str = ", ".join(input_data.purpose) if input_data.purpose else default_value

        def safe_value(value, default=default_value):
            return value if value is not None else default

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

        # 6. 스트리밍 호출
        formatted_human_prompt = HUMAN_PROMPT.format(**prompt_variables)
        contents = [Part.from_text(formatted_human_prompt)]
        generation_config = {
            "max_output_tokens": MAX_TOKENS,
            "temperature": GEMINI_TEMPERATURE,
        }

        responses = streaming_model.generate_content(
            contents,
            generation_config=generation_config,
            stream=True,
        )

        for response in responses:
            try:
                yield response.text
            except Exception:
                pass

    finally:
        # 7. 임시 파일 정리
        if temp_creds_path and os.path.exists(temp_creds_path):
            os.remove(temp_creds_path)
