from langchain_google_vertexai import ChatVertexAI
from src.config.config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE,
    GEMINI_THINKING_BUDGET,
)

# 기본 LLM (스트리밍 비활성화)
llm = ChatVertexAI(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    model_name=GEMINI_MODEL,
    max_output_tokens=GEMINI_MAX_TOKENS,
    temperature=GEMINI_TEMPERATURE,
    # model_kwargs={"thinking_budget": GEMINI_THINKING_BUDGET}, # Deprecated
    thinking_budget=GEMINI_THINKING_BUDGET, # Pass directly
    streaming=False,
)

# 스트리밍 LLM
llm_streaming = ChatVertexAI(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    model_name=GEMINI_MODEL,
    max_output_tokens=GEMINI_MAX_TOKENS,
    temperature=GEMINI_TEMPERATURE,
    # model_kwargs={"thinking_budget": GEMINI_THINKING_BUDGET}, # Deprecated
    thinking_budget=GEMINI_THINKING_BUDGET, # Pass directly
    streaming=True,
)
