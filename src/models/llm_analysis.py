from typing import Optional, Dict, Any, List
from abc import ABC
from langchain_google_vertexai import ChatVertexAI
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
import json
import os
import logging

# 설정 가져오기
from src.config.stt_config import (
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION,
    VERTEX_AI_MODEL,
    VERTEX_AI_TEMPERATURE,
    VERTEX_AI_MAX_TOKENS,
    LANGSMITH_TRACING,
    LANGSMITH_PROJECT
)
from src.prompts.meeting_analysis_prompts import SYSTEM_PROMPT, USER_PROMPT
from src.utils.stt_schema import MeetingAnalysis

# 로깅 설정
logger = logging.getLogger("llm_analysis")

# LangSmith 추적 상태 로깅 (config에서 이미 환경변수 설정됨)
if LANGSMITH_TRACING:
    logger.info(f"LangSmith 추적 활성화됨 - 프로젝트: {LANGSMITH_PROJECT}")
else:
    logger.info("LangSmith 추적이 비활성화되어 있습니다")


class BaseMeetingAnalyzer(ABC):    
    """회의 분석을 위한 기본 추상 클래스"""
    
    def __init__(self):
        pass
    
    def _prepare_speaker_stats(self, speaker_stats: Optional[Dict]) -> str:
        #화자 통계 텍스트 준비
        if not speaker_stats:
            return ""
        
        stats_text = "\n화자별 발언 점유율:\n"
        for speaker_name, stats in speaker_stats.items():
            stats_text += f"- {speaker_name}: {stats['percentage']}% ({stats['formatted_time']})\n"
        return stats_text
    
    def _handle_analysis_error(self, error: Exception, error_type: str = "분석 오류") -> str:
        """분석 오류 처리 및 JSON 형식으로 반환"""
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"{error_type} 상세:\n{error_detail}")
        
        error_result = {
            "error": error_type,
            "message": str(error),
            "detail": error_detail
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)
    
    def _execute_chain(self, chain, input_data: Dict, 
                      analysis_type: str = "분석") -> str:
        """체인 실행 및 결과 처리"""
        try:
            logger.info(f"{analysis_type} 요청 데이터 크기: {len(str(input_data))}자")
            
            result = chain.invoke(input_data)
            
            logger.info(f"{analysis_type} 응답 타입: {type(result)}")
            if result:
                logger.debug(f"{analysis_type} 응답 내용 미리보기: {str(result)[:200]}...")
            else:
                logger.warning(f"{analysis_type} 응답: None")
            
            # None 체크
            if result is None:
                logger.warning(f"{analysis_type}에서 None을 반환했습니다. 스키마 검증 실패 또는 내용이 너무 길 가능성이 있습니다.")
                raise ValueError(f"{analysis_type} returned None - possibly due to schema validation failure or content too long")
            
            # JSON 형식으로 반환
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            return self._handle_analysis_error(e, f"{analysis_type} 오류")
    
    def analyze_1on1_meeting(self, transcript: str, 
                            speaker_stats: Dict = None, qa_pairs: List = None, 
                            participants: Dict = None) -> str:
        """1:1 회의 종합 분석"""
        try:
            # 화자 통계 준비
            speaker_stats_text = self._prepare_speaker_stats(speaker_stats)
            
            # 전사 텍스트에 화자 통계만 추가 (참석자 정보는 별도 필드로 전달)
            full_transcript = transcript
            if speaker_stats_text:
                full_transcript += f"\n{speaker_stats_text}"
            
            # 사용자 프롬프트 템플릿
            user_prompt_template = PromptTemplate(
                input_variables=["transcript", "participants_info", "qa_pairs_json"],
                template=USER_PROMPT
            )
            
            # Q&A JSON 준비
            qa_pairs_json = json.dumps(qa_pairs, ensure_ascii=False) if qa_pairs else "[]"
            
            # 참석자 정보를 JSON으로 직접 전달
            participants_info_text = json.dumps(participants, ensure_ascii=False) if participants else ""
            
            # 프롬프트 체인 구성
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", user_prompt_template.template)
            ])
            
            # 체인 생성
            chain = prompt | self.llm.with_structured_output(MeetingAnalysis)
            
            
            # 체인 실행
            input_data = {
                "transcript": full_transcript,
                "participants_info": participants_info_text,
                "qa_pairs_json": qa_pairs_json
            }
            
            return self._execute_chain(chain, input_data, "1:1 회의 분석")
            
        except Exception as e:
            return self._handle_analysis_error(e, "1:1 회의 분석 오류")


class GeminiMeetingAnalyzer(BaseMeetingAnalyzer):    
    """Google Vertex AI Gemini 모델을 사용한 회의 분석기"""
    
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
        logger.info(f"Vertex AI {VERTEX_AI_MODEL} 모델 초기화 완료")
    
