import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from supabase import Client
from src.utils.schemas import MeetingPipelineState
from src.utils.performance_logging import generate_performance_report
from .generate_meeting import (
    retrieve_from_supabase, 
    process_with_assemblyai, 
    analyze_with_llm,
    generate_title_only
)

logger = logging.getLogger("meeting_pipeline")


class MeetingPipeline:
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.workflow = self._build_graph()
        logger.info("MeetingPipeline 초기화 완료")
    
    def _build_graph(self) -> Any:
        workflow = StateGraph(MeetingPipelineState)
        
        retrieve_from_supabase._supabase_client = self.supabase
        
        workflow.add_node("retrieve", retrieve_from_supabase)
        workflow.add_node("transcribe", process_with_assemblyai)
        workflow.add_node("analyze", analyze_with_llm)
        workflow.add_node("generate_title", generate_title_only)
        
        workflow.set_conditional_entry_point(lambda state: "generate_title" if state.get("only_title", False) else "retrieve")
        workflow.add_edge("retrieve", "transcribe")
        workflow.add_edge("transcribe", "analyze")
        workflow.add_edge("analyze", END)
        workflow.add_edge("generate_title", END)
        
        return workflow.compile()
    
    async def run(self, recording_url: Optional[str] = None, **kwargs) -> Dict:
        logger.info(f"파이프라인 실행 시작: {recording_url}")
        
        initial_state: MeetingPipelineState = {
            "recording_url": recording_url,
            "qa_pairs": kwargs.get("qa_pairs"),
            "participants_info": kwargs.get("participants_info"),
            "meeting_datetime": kwargs.get("meeting_datetime"),
            "only_title": kwargs.get("only_title", False),
            "file_url": None,
            "file_path": None,
            "transcript": None,
            "speaker_stats_percent": None,
            "analysis_result": None,
            "errors": [],
            "status": "pending",
            
            # 성능 측정 필드 
            "performance_metrics": None,
            "performance_report": None
        }
        
        result = await self.workflow.ainvoke(initial_state)
        
        if result.get("status") == "completed":
            generate_performance_report(result)
        
        logger.info(f"✅ 파이프라인 실행 완료: {result['status']}")
        
        return result