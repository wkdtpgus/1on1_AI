from typing import Optional, Dict, List
from abc import ABC
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
import json
import logging

from src.prompts.meeting_analysis_prompts import SYSTEM_PROMPT, USER_PROMPT
from src.utils.stt_schemas import MeetingAnalysis
from .speaker_stats import prepare_speaker_stats

# 로깅 설정
logger = logging.getLogger("meeting_analyzer")


class BaseMeetingAnalyzer(ABC):    
    """회의 분석을 위한 기본 추상 클래스"""
    
    def __init__(self):
        pass
    
    

    def analyze_1on1_meeting(self, transcript: str, 
                            speaker_stats: Dict = None, qa_pairs: List = None, 
                            participants: Dict = None) -> str:
        """1:1 회의 종합 분석"""
        try:
            # 화자 통계 준비
            speaker_stats_text = prepare_speaker_stats(speaker_stats)
            
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
            
            
            # 체인 실행 및 결과 처리
            input_data = {
                "transcript": full_transcript,
                "participants_info": participants_info_text,
                "qa_pairs_json": qa_pairs_json
            }
            
            result = chain.invoke(input_data)
            
            if result is None:
                raise ValueError("1:1 회의 분석 실패")
            
            logger.info("1:1 회의 분석 완료")
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"1:1 회의 분석 오류: {str(e)}")
            raise