"""
다중 LLM 모델을 사용한 STT 분석 비교 모듈
OpenAI GPT와 Google Vertex AI Gemini 모델 비교
"""

import json
import time
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

# 설정 가져오기
from src.config.config import (
    OPENAI_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    VERTEX_AI_MODEL,
    VERTEX_AI_TEMPERATURE,
    VERTEX_AI_MAX_TOKENS
)
from src.prompts.stt_llm_prompts import COMPREHENSIVE_MEETING_ANALYSIS_PROMPT


class ModelComparisonResult(BaseModel):
    """모델 비교 결과"""
    openai_result: str = Field(description="OpenAI GPT 결과")
    vertexai_result: str = Field(description="Vertex AI Gemini 결과")
    openai_response_time: float = Field(description="OpenAI 응답 시간(초)")
    vertexai_response_time: float = Field(description="Vertex AI 응답 시간(초)")
    comparison_notes: str = Field(description="비교 메모")


class MultiLLMAnalyzer:
    """다중 LLM 모델을 사용한 STT 분석 비교 클래스"""
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 google_project: Optional[str] = None,
                 google_location: Optional[str] = None):
        """
        MultiLLMAnalyzer 초기화
        
        Args:
            openai_api_key: OpenAI API 키
            google_project: Google Cloud 프로젝트 ID
            google_location: Google Cloud 리전
        """
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        self.google_project = google_project or GOOGLE_CLOUD_PROJECT
        self.google_location = google_location or GOOGLE_CLOUD_LOCATION
        
        # OpenAI LLM 초기화
        self.openai_llm = None
        if self.openai_api_key:
            try:
                self.openai_llm = ChatOpenAI(
                    openai_api_key=self.openai_api_key,
                    model=LLM_MODEL,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS
                )
                print(f"✅ OpenAI {LLM_MODEL} 모델 초기화 완료")
            except Exception as e:
                print(f"❌ OpenAI 모델 초기화 실패: {e}")
        
        # Vertex AI LLM 초기화
        self.vertexai_llm = None
        if self.google_project:
            try:
                self.vertexai_llm = ChatVertexAI(
                    project=self.google_project,
                    location=self.google_location,
                    model_name=VERTEX_AI_MODEL,
                    temperature=VERTEX_AI_TEMPERATURE,
                    max_output_tokens=VERTEX_AI_MAX_TOKENS
                )
                print(f"✅ Vertex AI {VERTEX_AI_MODEL} 모델 초기화 완료")
            except Exception as e:
                print(f"❌ Vertex AI 모델 초기화 실패: {e}")
        
        # 프롬프트 템플릿 설정
        self.prompt_template = PromptTemplate(
            input_variables=["transcript"],
            template=COMPREHENSIVE_MEETING_ANALYSIS_PROMPT
        )
    
    def analyze_with_openai(self, transcript: str) -> tuple[str, float]:
        """OpenAI GPT 모델로 분석"""
        if not self.openai_llm:
            return "OpenAI 모델이 초기화되지 않았습니다.", 0.0
        
        try:
            start_time = time.time()
            prompt = self.prompt_template.format(transcript=transcript)
            response = self.openai_llm.invoke(prompt)
            response_time = time.time() - start_time
            
            return response.content.strip(), response_time
            
        except Exception as e:
            return f"OpenAI 분석 오류: {str(e)}", 0.0
    
    def analyze_with_vertexai(self, transcript: str) -> tuple[str, float]:
        """Vertex AI Gemini 모델로 분석"""
        if not self.vertexai_llm:
            return "Vertex AI 모델이 초기화되지 않았습니다.", 0.0
        
        try:
            start_time = time.time()
            prompt = self.prompt_template.format(transcript=transcript)
            response = self.vertexai_llm.invoke(prompt)
            response_time = time.time() - start_time
            
            return response.content.strip(), response_time
            
        except Exception as e:
            return f"Vertex AI 분석 오류: {str(e)}", 0.0
    
    def compare_models(self, transcript: str) -> ModelComparisonResult:
        """두 모델의 결과를 비교"""
        print("🔄 OpenAI GPT 모델로 분석 중...")
        openai_result, openai_time = self.analyze_with_openai(transcript)
        
        print("🔄 Vertex AI Gemini 모델로 분석 중...")
        vertexai_result, vertexai_time = self.analyze_with_vertexai(transcript)
        
        # 비교 메모 생성
        comparison_notes = f"""
모델 비교 결과:
- OpenAI 응답 시간: {openai_time:.2f}초
- Vertex AI 응답 시간: {vertexai_time:.2f}초
- 빠른 모델: {'OpenAI' if openai_time < vertexai_time else 'Vertex AI'}
        """.strip()
        
        return ModelComparisonResult(
            openai_result=openai_result,
            vertexai_result=vertexai_result,
            openai_response_time=openai_time,
            vertexai_response_time=vertexai_time,
            comparison_notes=comparison_notes
        )
    
    def analyze_stt_with_comparison(self, stt_result: Dict[str, Any]) -> Dict[str, Any]:
        """STT 결과를 두 모델로 분석하고 비교"""
        # 전체 텍스트 사용
        full_transcript = stt_result.get("full_text", "")
        
        if not full_transcript:
            return {
                **stt_result,
                "model_comparison": {
                    "error": "분석할 전사 내용이 없습니다."
                }
            }
        
        # 두 모델로 분석
        comparison_result = self.compare_models(full_transcript)
        
        return {
            **stt_result,
            "model_comparison": {
                "openai_analysis": comparison_result.openai_result,
                "vertexai_analysis": comparison_result.vertexai_result,
                "performance": {
                    "openai_response_time": comparison_result.openai_response_time,
                    "vertexai_response_time": comparison_result.vertexai_response_time
                },
                "comparison_notes": comparison_result.comparison_notes
            }
        }