from typing import List, Optional, Dict, TypedDict
from pydantic import BaseModel, Field


class FeedbackItem(BaseModel):
    """매니저 개선 피드백 항목"""
    title: str = Field(description="개선이 필요한 주제")
    situation: str = Field(description="대화록에서 인용한 구체적인 상황이나 발언")
    suggestion: str = Field(description="개선된 행동 제안")
    importance: str = Field(description="중요한 이유")
    implementation: str = Field(description="다음 1on1에서 적용할 수 있는 구체적인 방법")


class QAItem(BaseModel):
    """Q&A 항목"""
    question: str = Field(description="질문 목록")
    answer: str = Field(description="대화록에서 추출한 답변")


# =============================================================================
# LangGraph 파이프라인 상태 스키마
# =============================================================================

class MeetingPipelineState(TypedDict):
    """LangGraph 파이프라인 상태 스키마"""
    # 입력 데이터
    file_id: str
    bucket_name: str
    qa_data: Optional[List[Dict]]
    participants_info: Optional[Dict]
    meeting_datetime: Optional[str]  # "2024-12-08T14:30:00" 형식
    
    # Supabase 조회 결과
    file_url: Optional[str]
    file_path: Optional[str]
    file_metadata: Optional[Dict]
    
    # STT 결과
    transcript: Optional[Dict]
    speaker_stats: Optional[Dict]
    
    # LLM 분석 결과
    analysis_result: Optional[Dict]
    
    # 상태 추적
    errors: List[str]
    status: str  # "pending", "processing", "completed", "failed"


# =============================================================================
# LLM 출력 스키마
# =============================================================================

class MeetingAnalysis(BaseModel):
    """1-on-1 회의 분석 결과"""
    title: str = Field(description="회의를 한 줄로 요약한 제목 (예: '3분기 성과 리뷰 및 AI 프로젝트 진행 상황 점검')")
    action_items: str = Field(description="담당자와 마감일이 포함된 액션 아이템")
    detailed_discussion: str = Field(description="계층적 구조를 따르는 상세한 회의 내용 (마크다운 형식)")
    feedback: List[FeedbackItem] = Field(description="매니저 개선 피드백 리스트")
    positive_aspects: List[str] = Field(description="매니저가 잘 수행한 측면들")
    qa_summary: List[QAItem] = Field(description="질문별 답변 리스트 - 모든 질문에 대해 완전한 답변 필수")
