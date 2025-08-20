from typing import List, Optional, Dict, TypedDict
from pydantic import BaseModel, Field

class FeedbackItem(BaseModel):
    """매니저 개선 피드백 항목"""
    title: str = Field(description="개선이 필요한 주제")
    content: str = Field(description="상황, 개선 제안, 중요성, 구체적 실행 방법을 하나의 자연스러운 단락으로 통합한 피드백 내용")

class QAItem(BaseModel):
    """Q&A 항목"""
    question_index: int = Field(description="질문 인덱스 (1부터 시작)")
    answer: str = Field(description="대화록에서 추출한 답변")

# LLM 출력 스키마
class AiCoreSummary(BaseModel):
    """핵심 요약 정보"""
    core_content: str = Field(description="회의의 핵심 내용")
    decisions_made: str = Field(description="회의에서 내려진 공동 결정사항")
    support_needs_blockers: str = Field(description="지원 요청 및 블로커와 해결 방안")

class MeetingAnalysis(BaseModel):
    """1-on-1 회의 분석 결과"""
    title: str = Field(description="회의를 한 줄로 요약한 제목 (예: '3분기 성과 리뷰 및 AI 프로젝트 진행 상황 점검')")
    speaker_mapping: List[str] = Field(description="화자 매핑 정보 - ['A의 실제이름', 'B의 실제이름'] 순서")
    leader_action_items: List[str] = Field(description="리더(매니저)가 수행할 액션 아이템 리스트")
    member_action_items: List[str] = Field(description="멤버(팀원)가 수행할 액션 아이템 리스트")
    ai_summary: str = Field(description="계층적 구조를 따르는 상세한 회의 내용 (마크다운 형식)")
    ai_core_summary: AiCoreSummary = Field(description="핵심 요약 정보")
    leader_feedback: List[FeedbackItem] = Field(description="매니저 개선 피드백 리스트")
    positive_aspects: List[str] = Field(description="매니저가 잘 수행한 측면들")
    qa_summary: List[QAItem] = Field(description="질문별 답변 리스트 - 모든 질문에 대해 완전한 답변 필수")

# 랭그래프 스키마 
class MeetingPipelineState(TypedDict):
    """LangGraph 파이프라인 상태 스키마"""
    # 입력 데이터
    file_id: str
    bucket_name: str
    qa_pairs: Optional[List[Dict]]
    participants_info: Optional[Dict]
    meeting_datetime: Optional[str]  # "2024-12-08T14:30:00" 형식
    
    # Supabase 조회 결과
    file_url: Optional[str]
    file_path: Optional[str]
    
    # STT 결과
    transcript: Optional[Dict]
    speaker_stats_percent: Optional[Dict]
    
    # LLM 분석 결과
    analysis_result: Optional[Dict]
    
    # 성능 측정 필드
    performance_metrics: Optional[Dict]
    token_usage: Optional[Dict]
    costs: Optional[Dict]
    performance_report: Optional[Dict]
    
    # 상태 추적
    errors: List[str]
    status: str  # "pending", "processing", "completed", "failed"


