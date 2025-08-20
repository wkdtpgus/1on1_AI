import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from supabase import Client

from src.utils.model import MeetingAnalyzer
from src.utils.stt_schemas import MeetingPipelineState
from src.utils.performance_logging import generate_performance_report
from src.config.config import SUPABASE_BUCKET_NAME
from .transcribe_analyze import (
    retrieve_from_supabase, 
    process_with_assemblyai, 
    analyze_with_llm
)

logger = logging.getLogger("meeting_pipeline")


class MeetingPipeline:
    
    def __init__(self, supabase_client: Client, analyzer: MeetingAnalyzer):
        self.supabase = supabase_client
        self.analyzer = analyzer
        self.workflow = self._build_graph()
        logger.info("MeetingPipeline 초기화 완료")
    
    def _build_graph(self) -> Any:
        workflow = StateGraph(MeetingPipelineState)
        
        # 노드 함수에 필요한 리소스 바인딩
        retrieve_from_supabase._supabase_client = self.supabase
        analyze_with_llm._analyzer = self.analyzer
        
        # 노드 추가
        workflow.add_node("retrieve", retrieve_from_supabase)
        workflow.add_node("transcribe", process_with_assemblyai)
        workflow.add_node("analyze", analyze_with_llm)
        
        # 엣지 연결 (파이프라인 흐름 정의)
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "transcribe")
        workflow.add_edge("transcribe", "analyze")
        workflow.add_edge("analyze", END)
        
        return workflow.compile()
    
    async def run(self, file_id: str, **kwargs) -> Dict:
        logger.info(f"파이프라인 실행 시작: {file_id}")
        
        # 초기 상태 설정
        bucket_name = kwargs.get("bucket_name", SUPABASE_BUCKET_NAME)
        
        initial_state: MeetingPipelineState = {
            "file_id": file_id,
            "bucket_name": bucket_name,
            "qa_pairs": kwargs.get("qa_pairs"),
            "participants_info": kwargs.get("participants_info"),
            "meeting_datetime": kwargs.get("meeting_datetime"),
            "file_url": None,
            "file_path": None,
            "transcript": None,
            "speaker_stats_percent": None,
            "analysis_result": None,
            "errors": [],
            "status": "pending",
            
            # 성능 측정 필드 
            "performance_metrics": None,
            "token_usage": None,
            "costs": None,
            "performance_report": None
        }
        
        # LangGraph 워크플로우 실행
        result = await self.workflow.ainvoke(initial_state)
        
        # 성공적으로 완료된 경우 성능 리포트 생성
        if result.get("status") == "completed":
            generate_performance_report(result)
        
        logger.info(f"✅ 파이프라인 실행 완료: {result['status']}")
        
        return result