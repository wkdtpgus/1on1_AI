"""
통합 LLM 분석 모듈
STT 결과를 LLM 모델로 분석하는 통합 모듈
- OpenAI GPT 분석기
- Gemini 분석기 (기본)
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, Union
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


class STTLLMAnalysisResult(BaseModel):
    """LLM 분석 결과 모델"""
    summary: str = Field(description="회의 내용 전체 요약 (마크다운 형식)")


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
        
        # 프롬프트 템플릿 설정
        self.comprehensive_prompt_template = PromptTemplate(
            input_variables=["transcript", "questions"],
            template=COMPREHENSIVE_MEETING_ANALYSIS_PROMPT
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
            # 질문 리스트를 그대로 전달 (포맷팅 없이)
            prompt = self.comprehensive_prompt_template.format(
                transcript=transcript,
                questions=questions if questions else []
            )
            response = self.llm.invoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            return f"# 종합 분석 오류\n\n분석 중 오류가 발생했습니다: {str(e)}"
    
    def analyze_stt_result(self, stt_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        간소화된 STT 결과를 받아서 종합 분석
        
        Args:
            stt_result: STTProcessor의 전사 결과 (간단한 형식)
            
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
        
        comprehensive_analysis = self.analyze_comprehensive(transcript_text)
        
        return {
            **stt_result,
            "analysis": {
                "comprehensive_analysis": comprehensive_analysis,
                "analyzed_at": datetime.now().isoformat(),
                "model_used": LLM_MODEL
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
        
        # 프롬프트 템플릿 설정
        self.comprehensive_prompt_template = PromptTemplate(
            input_variables=["transcript", "questions"],
            template=COMPREHENSIVE_MEETING_ANALYSIS_PROMPT
        )
    
    def prepare_analysis_input(self, stt_result: Dict[str, Any]) -> Dict[str, Any]:
        """STT 결과를 LLM 분석용 간소화된 구조로 변환"""
        
        # 참석자 정보 정리
        participants = stt_result.get("participants", [])
        speaker_map = {p['speaker_label']: p['name'] for p in participants}
        
        # 전사 텍스트 생성
        transcript_lines = []
        for segment in stt_result.get("transcript", []):
            speaker_name = speaker_map.get(segment['speaker_label'], '참석자')
            transcript_lines.append(f"{speaker_name}: {segment['text']}")
        
        # LLM 분석용 구조
        analysis_input = {
            "metadata": {
                "meeting_title": stt_result.get("metadata", {}).get("meeting_title", "1on1 미팅"),
                "meeting_date": stt_result.get("metadata", {}).get("meeting_date", "날짜 미상"),
                "duration_minutes": stt_result.get("metadata", {}).get("duration_seconds", 0) // 60,
                "participants": [
                    {"name": p['name'], "role": p['role']} 
                    for p in participants
                ]
            },
            "transcript": "\n".join(transcript_lines)
        }
        
        return analysis_input
    
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
            # 질문 리스트를 그대로 전달 (포맷팅 없이)
            prompt = self.comprehensive_prompt_template.format(
                transcript=transcript,
                questions=questions if questions else []
            )
            response = self.llm.invoke(prompt)
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
    
    def analyze_structured_meeting(self, stt_result: Dict[str, Any]) -> Dict[str, Any]:
        """구조화된 회의 데이터 분석 - JSON 메타데이터와 텍스트 전사를 결합"""
        
        # 1. 분석용 입력 데이터 준비
        analysis_input = self.prepare_analysis_input(stt_result)
        
        # 2. 프롬프트 구성
        prompt = f"""다음 1on1 회의 데이터를 분석해주세요:

회의 정보:
{json.dumps(analysis_input['metadata'], ensure_ascii=False, indent=2)}

회의 전사:
{analysis_input['transcript']}

위 내용을 바탕으로 다음 지침에 따라 종합 분석을 제공해주세요:
"""
        
        # 3. LLM 호출
        try:
            analysis_guidelines = COMPREHENSIVE_MEETING_ANALYSIS_PROMPT.split('{transcript}')[1] if '{transcript}' in COMPREHENSIVE_MEETING_ANALYSIS_PROMPT else COMPREHENSIVE_MEETING_ANALYSIS_PROMPT
            full_prompt = prompt + analysis_guidelines
            
            response = self.llm.invoke(full_prompt)
            
            return {
                "status": "success",
                "original_stt": stt_result,
                "analysis": {
                    "comprehensive_analysis": response.content.strip(),
                    "analyzed_at": datetime.now().isoformat(),
                    "model_used": VERTEX_AI_MODEL,
                    "input_format": "structured_json_text"
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"분석 중 오류가 발생했습니다: {str(e)}",
                "original_stt": stt_result
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
            transcript_lines = []
            for utterance in utterances:
                speaker = utterance.get("speaker", "화자")
                text = utterance.get("text", "")
                transcript_lines.append(f"참석자 {speaker}: {text}")
            
            full_transcript = "\n".join(transcript_lines)
        else:
            full_transcript = stt_result.get("full_text", "")
        
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
                "analyzed_with_speakers": bool(utterances),
                "model_used": VERTEX_AI_MODEL
            }
        }


# 기본 분석기는 Gemini 사용
MeetingAnalyzer = GeminiMeetingAnalyzer