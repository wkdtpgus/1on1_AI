from typing import Optional, Dict, List
from abc import ABC
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
import json
import logging

from src.prompts.stt_generation.meeting_analysis_prompts import SYSTEM_PROMPT, USER_PROMPT
from src.utils.stt_schemas import MeetingAnalysis

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
            # 화자 통계에서 percentage만 추출하여 간소화
            simplified_stats = {}
            if speaker_stats:
                for speaker_name, stats in speaker_stats.items():
                    # speaker_name이 이미 화자 이름으로 되어있음 (예: "김준희", "이영희")
                    simplified_stats[speaker_name] = stats.get('percentage', 0)
            
            # 사용자 프롬프트 템플릿
            user_prompt_template = PromptTemplate(
                input_variables=["transcript", "speaker_stats", "participants", "qa_pairs"],
                template=USER_PROMPT
            )
            
            # 모든 데이터를 JSON 문자열로 변환
            speaker_stats_json = json.dumps(simplified_stats, ensure_ascii=False) if simplified_stats else "{}"
            qa_pairs_json = json.dumps(qa_pairs, ensure_ascii=False) if qa_pairs else "[]"
            participants_json = json.dumps(participants, ensure_ascii=False) if participants else "{}"
            
            # 프롬프트 체인 구성
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", user_prompt_template.template)
            ])
            
            # 체인 생성
            chain = prompt | self.llm.with_structured_output(MeetingAnalysis)
            
            # 체인 실행 및 결과 처리
            input_data = {
                "transcript": transcript,  # 순수한 대화 내용만
                "speaker_stats": speaker_stats_json,  # 간소화된 화자 비율
                "participants": participants_json,  # 참가자 정보
                "qa_pairs": qa_pairs_json  # Q&A 쌍
            }
            
            result = chain.invoke(input_data)
            
            if result is None:
                raise ValueError("1:1 회의 분석 실패")
            
            logger.info("1:1 회의 분석 완료")
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"1:1 회의 분석 오류: {str(e)}")
            raise