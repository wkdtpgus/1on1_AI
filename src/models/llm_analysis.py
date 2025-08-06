from datetime import datetime
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI
from langchain.prompts import PromptTemplate

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
from src.prompts.stt_llm_prompts import MEETING_ANALYST_SYSTEM_PROMPT, COMPREHENSIVE_ANALYSIS_USER_PROMPT


class OpenAIMeetingAnalyzer:
    """OpenAI GPT를 사용한 STT 전사 결과 분석 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        OpenAI MeetingAnalyzer 초기화
        
        Args:
            api_key: OpenAI API 키 (없으면 환경변수에서 가져옴)
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # OpenAI LLM 초기화
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS
        )
        print(f"✅ OpenAI {LLM_MODEL} 모델 초기화 완료")
        
        # 시스템 프롬프트 설정
        self.system_prompt = MEETING_ANALYST_SYSTEM_PROMPT
        
        # 사용자 프롬프트 템플릿 설정
        self.user_prompt_template = PromptTemplate(
            input_variables=["transcript", "questions"],
            template=COMPREHENSIVE_ANALYSIS_USER_PROMPT
        )
    
    def analyze_comprehensive(self, transcript: str, questions: list = None) -> str:
        """
        전사 텍스트를 종합 분석 (요약 + 피드백 + Q&A)
        
        Args:
            transcript: STT로 전사된 회의 내용
            questions: 답변이 필요한 질문 리스트 (선택적)
            
        Returns:
            str: 종합 분석 결과 (마크다운 형식)
        """
        try:
            # 사용자 프롬프트 생성 (질문 리스트를 그대로 전달)
            user_prompt = self.user_prompt_template.format(
                transcript=transcript,
                questions=questions if questions else []
            )
            
            # System과 User 메시지로 구성
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            return f"# 종합 분석 오류\n\n분석 중 오류가 발생했습니다: {str(e)}"
    
    def analyze_stt_result(self, stt_result: Dict[str, Any], questions: list = None) -> Dict[str, Any]:
        """
        간소화된 STT 결과를 받아서 종합 분석
        
        Args:
            stt_result: STTProcessor의 전사 결과 (간단한 형식)
            questions: 답변이 필요한 질문 리스트 (선택적)
            
        Returns:
            종합 분석 결과가 추가된 전체 결과
        """
        transcript_text = stt_result.get("transcript", "")
        
        if not transcript_text:
            return {
                **stt_result,
                "analysis": {
                    "comprehensive_analysis": "# 전사 내용 없음\n\n분석할 내용이 없습니다."
                }
            }
        
        comprehensive_analysis = self.analyze_comprehensive(transcript_text, questions)
        
        return {
            **stt_result,
            "analysis": {
                "comprehensive_analysis": comprehensive_analysis,
                "analyzed_at": datetime.now().isoformat(),
                "model_used": LLM_MODEL,
                "questions_answered": questions if questions else []
            }
        }


class GeminiMeetingAnalyzer:
    """Google Gemini를 사용한 STT 전사 결과 분석 클래스 (기본 분석기)"""
    
    def __init__(self, 
                 google_project: Optional[str] = None,
                 google_location: Optional[str] = None):
        """
        Gemini MeetingAnalyzer 초기화
        
        Args:
            google_project: Google Cloud 프로젝트 ID (없으면 환경변수에서 가져옴)
            google_location: Google Cloud 리전 (없으면 환경변수에서 가져옴)
        """
        self.google_project = google_project or GOOGLE_CLOUD_PROJECT
        self.google_location = google_location or GOOGLE_CLOUD_LOCATION
        
        if not self.google_project:
            raise ValueError("Google Cloud Project ID is required")
        
        # Vertex AI Gemini LLM 초기화
        self.llm = ChatVertexAI(
            project=self.google_project,
            location=self.google_location,
            model_name=VERTEX_AI_MODEL,
            temperature=VERTEX_AI_TEMPERATURE,
            max_output_tokens=VERTEX_AI_MAX_TOKENS,
        )
        print(f"✅ Vertex AI {VERTEX_AI_MODEL} 모델 초기화 완료")
        
        # 시스템 프롬프트 설정
        self.system_prompt = MEETING_ANALYST_SYSTEM_PROMPT
        
        # 사용자 프롬프트 템플릿 설정
        self.user_prompt_template = PromptTemplate(
            input_variables=["transcript", "questions"],
            template=COMPREHENSIVE_ANALYSIS_USER_PROMPT
        )
    
    
    def analyze_comprehensive(self, transcript: str, questions: list = None) -> str:
        """
        전사 텍스트를 종합 분석 (요약 + 피드백 + Q&A)
        
        Args:
            transcript: STT로 전사된 회의 내용
            questions: 답변이 필요한 질문 리스트 (선택적)
            
        Returns:
            str: 종합 분석 결과 (마크다운 형식)
        """
        try:
            # 사용자 프롬프트 생성 (질문 리스트를 그대로 전달)
            user_prompt = self.user_prompt_template.format(
                transcript=transcript,
                questions=questions if questions else []
            )
            
            # System과 User 메시지로 구성
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            return f"# 종합 분석 오류\n\n분석 중 오류가 발생했습니다: {str(e)}"
    
    def analyze_stt_result(self, stt_result: Dict[str, Any], questions: list = None) -> Dict[str, Any]:
        """
        간소화된 STT 결과를 받아서 종합 분석
        
        Args:
            stt_result: STTProcessor의 전사 결과 (간단한 형식)
            questions: 답변이 필요한 질문 리스트 (선택적)
            
        Returns:
            종합 분석 결과가 추가된 전체 결과
        """
        transcript_text = stt_result.get("transcript", "")
        
        if not transcript_text:
            return {
                **stt_result,
                "analysis": {
                    "comprehensive_analysis": "# 전사 내용 없음\n\n분석할 내용이 없습니다."
                }
            }
        
        # 질문이 stt_result에 포함되어 있으면 우선 사용
        if not questions and "questions" in stt_result:
            questions = stt_result.get("questions")
        
        comprehensive_analysis = self.analyze_comprehensive(transcript_text, questions)
        
        return {
            **stt_result,
            "analysis": {
                "comprehensive_analysis": comprehensive_analysis,
                "analyzed_at": datetime.now().isoformat(),
                "model_used": VERTEX_AI_MODEL,
                "questions_answered": questions if questions else []
            }
        }
    
