"""
STT 결과를 LLM으로 분석하는 모듈
"""

import json
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# 설정 가져오기
from src.config.config import (
    OPENAI_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS
)
from src.prompts.analysis_prompt import MEETING_ANALYSIS_PROMPT


class STTLLMAnalysisResult(BaseModel):
    """LLM 분석 결과 모델"""
    title: str = Field(description="전체 맥락을 고려한 한줄 제목 요약")
    summary: List[str] = Field(description="핵심 포인트 요약 리스트")


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
        
        # 프롬프트 템플릿 설정
        self.prompt_template = PromptTemplate(
            input_variables=["transcript"],
            template=MEETING_ANALYSIS_PROMPT
        )
    
    def analyze_transcript(self, transcript: str) -> STTLLMAnalysisResult:
        """
        전사 텍스트를 분석하여 제목과 요약 생성
        
        Args:
            transcript: STT로 전사된 회의 내용
            
        Returns:
            STTLLMAnalysisResult: 분석 결과 (제목, 요약)
        """
        try:
            # 프롬프트 생성
            prompt = self.prompt_template.format(transcript=transcript)
            
            # LLM 호출
            response = self.llm.invoke(prompt)
            
            # JSON 파싱
            result_json = json.loads(response.content)
            
            # Pydantic 모델로 변환
            analysis_result = STTLLMAnalysisResult(
                title=result_json.get("title", "제목 없음"),
                summary=result_json.get("summary", [])
            )
            
            return analysis_result
            
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 기본값 반환
            return STTLLMAnalysisResult(
                title="분석 실패",
                summary=[f"JSON 파싱 오류: {str(e)}"]
            )
        except Exception as e:
            # 기타 오류 처리
            return STTLLMAnalysisResult(
                title="분석 오류",
                summary=[f"분석 중 오류 발생: {str(e)}"]
            )
    
    def analyze_stt_result(self, stt_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        STT 결과 전체를 받아서 분석
        
        Args:
            stt_result: STTProcessor의 전사 결과
            
        Returns:
            분석 결과가 추가된 전체 결과
        """
        # STT 결과에서 전사 텍스트 추출
        full_text = stt_result.get("full_text", "")
        
        if not full_text:
            return {
                **stt_result,
                "analysis": {
                    "title": "전사 내용 없음",
                    "summary": ["분석할 내용이 없습니다."]
                }
            }
        
        # 텍스트 분석
        analysis_result = self.analyze_transcript(full_text)
        
        # 결과 병합
        return {
            **stt_result,
            "analysis": {
                "title": analysis_result.title,
                "summary": analysis_result.summary
            }
        }
    
    def analyze_with_speakers(self, stt_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        화자 정보가 포함된 STT 결과를 분석
        
        Args:
            stt_result: 화자 분리가 된 STT 결과
            
        Returns:
            화자별 발언을 고려한 분석 결과
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
        
        # 분석 수행
        if not full_transcript:
            return {
                **stt_result,
                "analysis": {
                    "title": "전사 내용 없음",
                    "summary": ["분석할 내용이 없습니다."]
                }
            }
        
        analysis_result = self.analyze_transcript(full_transcript)
        
        return {
            **stt_result,
            "analysis": {
                "title": analysis_result.title,
                "summary": analysis_result.summary,
                "analyzed_with_speakers": bool(utterances)
            }
        }