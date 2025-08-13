import streamlit as st
import json
import tempfile
import os
import google.auth
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
from typing import Dict
from src.utils.template_schemas import TemplateGeneratorInput, TemplateGeneratorOutput
from src.utils.utils import get_user_data_by_id

def get_template_generator_chain(credentials):
    """
    1on1 템플릿 생성을 위한 LangChain 체인을 생성합니다.
    인증 정보를 인자로 받아 모델을 초기화합니다.
    """
    model = ChatVertexAI(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        model_name=GEMINI_MODEL,
        credentials=credentials,
        max_output_tokens=MAX_TOKENS,
        temperature=GEMINI_TEMPERATURE,
        model_kwargs={"thinking_budget": GEMINI_THINKING_BUDGET},
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])
    parser = JsonOutputParser(pydantic_object=TemplateGeneratorOutput)
    chain = prompt | model | parser
    return chain

async def generate_template(input_data: TemplateGeneratorInput) -> Dict:
    """
    입력 데이터를 기반으로 1on1 템플릿을 비동기적으로 생성합니다.
    함수 내에서 인증을 처리하여 import 시점의 오류를 방지합니다.
    """
    credentials = None
    temp_creds_path = None
    try:
        if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
            gcp_creds_dict = dict(st.secrets["gcp_service_account"])
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_creds_file:
                json.dump(gcp_creds_dict, temp_creds_file)
                temp_creds_path = temp_creds_file.name
            credentials, _ = google.auth.load_credentials_from_file(temp_creds_path)

        if not credentials:
            raise ValueError("GCP credentials could not be loaded.")

        chain = get_template_generator_chain(credentials)

        user_data = None
        print(f"[DIAGNOSTIC] generate_template: Checking user_id: '{input_data.user_id}' (type: {type(input_data.user_id)})")
        if not input_data.user_id or input_data.user_id.strip().lower() != "default_user":
            user_data = get_user_data_by_id(input_data.user_id)
            if not user_data:
                raise ValueError(f"User with ID '{input_data.user_id}' not found.")

        target_info = input_data.target_info

        previous_summary_section = ""
        if input_data.use_previous_data and user_data and user_data.get("one_on_one_history"):
            history = user_data.get("one_on_one_history")
            if history:
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

        default_value = "Not specified"
        def safe_value(value, default=default_value):
            return value if value is not None else default

        question_composition_str = ", ".join(input_data.question_composition) if input_data.question_composition else default_value
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

        response = await chain.ainvoke(prompt_variables)
        return response

    finally:
        if temp_creds_path and os.path.exists(temp_creds_path):
            os.remove(temp_creds_path)

