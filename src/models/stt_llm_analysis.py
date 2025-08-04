"""
STT 결과를 LLM으로 분석하는 모듈
"""

import json
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

# 설정 가져오기
from src.config.config import (
    OPENAI_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS
)
from src.prompts.stt_llm_prompts import COMPREHENSIVE_MEETING_ANALYSIS_PROMPT


class STTLLMAnalysisResult(BaseModel):
    """LLM 분석 결과 모델"""
    summary: str = Field(description="회의 내용 전체 요약 (마크다운 형식)")


class MeetingAnalyzer:
    """STT 전사 결과를 분석하는 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        MeetingAnalyzer 초기화
        
        Args:
            api_key: OpenAI API 키 (없으면 환경변수에서 가져옴)
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS
        )
        
        # 통합 프롬프트 템플릿 설정
        self.comprehensive_prompt_template = PromptTemplate(
            input_variables=["transcript"],
            template=COMPREHENSIVE_MEETING_ANALYSIS_PROMPT
        )
    
    def analyze_comprehensive(self, transcript: str) -> str:
        """
        전사 텍스트를 종합 분석 (요약 + 피드백 + Q&A)
        
        Args:
            transcript: STT로 전사된 회의 내용
            
        Returns:
            str: 종합 분석 결과 (마크다운 형식)
        """
        try:
            # 프롬프트 생성
            prompt = self.comprehensive_prompt_template.format(transcript=transcript)
            
            # LLM 호출
            response = self.llm.invoke(prompt)
            
            # 응답 내용을 그대로 사용 (마크다운 형식)
            analysis_text = response.content.strip()
            
            return analysis_text
            
        except Exception as e:
            # 오류 처리
            return f"# 종합 분석 오류\n\n분석 중 오류가 발생했습니다: {str(e)}"
    
    def analyze_stt_result(self, stt_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        STT 결과 전체를 받아서 종합 분석
        
        Args:
            stt_result: STTProcessor의 전사 결과
            
        Returns:
            종합 분석 결과가 추가된 전체 결과
        """
        # STT 결과에서 전사 텍스트 추출
        full_text = stt_result.get("full_text", "")
        
        if not full_text:
            return {
                **stt_result,
                "analysis": {
                    "comprehensive_analysis": "# 전사 내용 없음\n\n분석할 내용이 없습니다."
                }
            }
        
        # 종합 분석
        comprehensive_analysis = self.analyze_comprehensive(full_text)
        
        # 결과 병합
        return {
            **stt_result,
            "analysis": {
                "comprehensive_analysis": comprehensive_analysis
            }
        }
    
    def analyze_with_speakers(self, stt_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        화자 정보가 포함된 STT 결과를 종합 분석
        
        Args:
            stt_result: 화자 분리가 된 STT 결과
            
        Returns:
            화자별 발언을 고려한 종합 분석 결과
        """
        utterances = stt_result.get("utterances", [])
        
        if utterances:
            # 화자별 발언을 대화 형식으로 재구성
            transcript_lines = []
            for utterance in utterances:
                speaker = utterance.get("speaker", "화자")
                text = utterance.get("text", "")
                transcript_lines.append(f"참석자 {speaker}: {text}")
            
            full_transcript = "\n".join(transcript_lines)
        else:
            # 화자 분리가 없으면 전체 텍스트 사용
            full_transcript = stt_result.get("full_text", "")
        
        # 종합 분석 수행
        if not full_transcript:
            return {
                **stt_result,
                "analysis": {
                    "comprehensive_analysis": "# 전사 내용 없음\n\n분석할 내용이 없습니다.",
                    "analyzed_with_speakers": bool(utterances)
                }
            }
        
        comprehensive_analysis = self.analyze_comprehensive(full_transcript)
        
        return {
            **stt_result,
            "analysis": {
                "comprehensive_analysis": comprehensive_analysis,
                "analyzed_with_speakers": bool(utterances)
            }
        }
    
