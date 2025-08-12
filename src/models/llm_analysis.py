from datetime import datetime
from typing import Optional
from abc import ABC, abstractmethod
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
import json

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
from src.prompts.meeting_analysis_prompts import SYSTEM_PROMPT, USER_PROMPT
from src.prompts.planning_meeting_prompts import SYSTEM_PROMPT as PLANNING_SYSTEM_PROMPT, USER_PROMPT as PLANNING_USER_PROMPT
from src.utils.schema import MeetingAnalysis, PlanningMeetingAnalysis


class BaseMeetingAnalyzer(ABC):    
    def __init__(self):
        pass
    
    @abstractmethod
    def _get_model_name(self) -> str:
        """모델명 반환 (서브클래스에서 구현)"""
        pass
    
    def analyze_comprehensive(self, transcript: str, questions: list = None, speaker_stats: dict = None) -> str:

        try:
            # 질문 텍스트 처리
            questions_text = ""
            if questions:
                if isinstance(questions, list):
                    questions_text = "\n".join(f"- {q}" for q in questions)
                else:
                    questions_text = str(questions)
            
            # 화자 통계 텍스트 처리
            speaker_stats_text = ""
            if speaker_stats:
                speaker_stats_text = "\n화자별 발언 점유율:\n"
                for speaker_name, stats in speaker_stats.items():
                    speaker_stats_text += f"- {speaker_name}: {stats['percentage']}% ({stats['formatted_time']})\n"
            
            # 전사 텍스트에 화자 통계 추가
            full_transcript = transcript
            if speaker_stats_text:
                full_transcript = f"{transcript}\n\n{speaker_stats_text}"
            
            # 기존 사용자 프롬프트 템플릿을 그대로 사용 (JSON 출력은 무시됨)
            user_prompt_template = PromptTemplate(
                input_variables=["transcript", "questions"],
                template=USER_PROMPT
            )
            
            # 프롬프트 체인 구성
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", user_prompt_template.template)
            ])
            
            # 체인 생성: prompt | structured_llm
            chain = prompt | self.llm.with_structured_output(MeetingAnalysis)
            
            # 실행
            print(f"🔍 Gemini 요청 데이터 크기: {len(full_transcript)}자")
            print(f"🔍 질문 개수: {len(questions) if questions else 0}개")
            
            result = chain.invoke({
                "transcript": full_transcript,
                "questions": questions_text
            })
            
            print(f"🔍 Gemini 응답 타입: {type(result)}")
            print(f"🔍 Gemini 응답 내용: {str(result)[:200]}..." if result else "🔍 Gemini 응답: None")
            
            # None 체크 추가
            if result is None:
                print("⚠️ Gemini가 None을 반환했습니다. 스키마 검증 실패 또는 내용이 너무 길 가능성이 있습니다.")
                raise ValueError("LLM returned None - possibly due to schema validation failure or content too long")
            
            # JSON 형식으로 반환
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"❌ 분석 오류 상세:\n{error_detail}")
            
            # 에러도 JSON 형식으로 반환
            error_result = {
                "error": "분석 오류",
                "message": str(e),
                "detail": error_detail
            }
            return json.dumps(error_result, indent=2, ensure_ascii=False)
    
    def analyze_planning_meeting(self, transcript: str, questions: list = None, speaker_stats: dict = None) -> str:
        """기획회의 분석 메서드"""
        try:
            # 질문 텍스트 처리
            questions_text = ""
            if questions:
                if isinstance(questions, list):
                    questions_text = "\n".join(f"- {q}" for q in questions)
                else:
                    questions_text = str(questions)
            
            # 화자 통계 텍스트 처리 (기획회의에서는 참고용)
            speaker_stats_text = ""
            if speaker_stats:
                speaker_stats_text = "\n참여자별 발언 점유율:\n"
                for speaker_name, stats in speaker_stats.items():
                    speaker_stats_text += f"- {speaker_name}: {stats['percentage']}% ({stats['formatted_time']})\n"
            
            # 전사 텍스트에 화자 통계 추가
            full_transcript = transcript
            if speaker_stats_text:
                full_transcript = f"{transcript}\n\n{speaker_stats_text}"
            
            # 기획회의 프롬프트 템플릿 사용
            user_prompt_template = PromptTemplate(
                input_variables=["transcript", "questions"],
                template=PLANNING_USER_PROMPT
            )
            
            # 프롬프트 체인 구성
            prompt = ChatPromptTemplate.from_messages([
                ("system", PLANNING_SYSTEM_PROMPT),
                ("human", user_prompt_template.template)
            ])
            
            # 체인 생성: prompt | structured_llm
            chain = prompt | self.llm.with_structured_output(PlanningMeetingAnalysis)
            
            # 실행
            print(f"🔍 기획회의 분석 요청 데이터 크기: {len(full_transcript)}자")
            print(f"🔍 질문 개수: {len(questions) if questions else 0}개")
            
            result = chain.invoke({
                "transcript": full_transcript,
                "questions": questions_text
            })
            
            print(f"🔍 기획회의 분석 응답 타입: {type(result)}")
            print(f"🔍 기획회의 분석 응답 내용: {str(result)[:200]}..." if result else "🔍 기획회의 분석 응답: None")
            
            # None 체크 추가
            if result is None:
                print("⚠️ 기획회의 분석에서 None을 반환했습니다.")
                raise ValueError("Planning meeting analysis returned None")
            
            # JSON 형식으로 반환
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"❌ 기획회의 분석 오류 상세:\n{error_detail}")
            
            # 에러도 JSON 형식으로 반환
            error_result = {
                "error": "기획회의 분석 오류",
                "message": str(e),
                "detail": error_detail
            }
            return json.dumps(error_result, indent=2, ensure_ascii=False)
    


class OpenAIMeetingAnalyzer(BaseMeetingAnalyzer):    
    def __init__(self, api_key: Optional[str] = None):

        super().__init__()
        
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
    
    def _get_model_name(self) -> str:
        """OpenAI 모델명 반환"""
        return LLM_MODEL


class GeminiMeetingAnalyzer(BaseMeetingAnalyzer):    
    def __init__(self, google_project: Optional[str] = None, google_location: Optional[str] = None):

        super().__init__()
        
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
    
    def _get_model_name(self) -> str:
        """Gemini 모델명 반환"""
        return VERTEX_AI_MODEL
    
