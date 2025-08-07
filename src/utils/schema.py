from typing import List
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


class MeetingAnalysis(BaseModel):
    """1-on-1 회의 분석 결과"""
    summary: str = Field(description="전체 회의 요약 내용 (마크다운 형식)")
    feedback: List[FeedbackItem] = Field(description="매니저 개선 피드백 리스트")
    positive_aspects: List[str] = Field(description="매니저가 잘 수행한 측면들")
    qa_summary: List[QAItem] = Field(description="질문별 답변 리스트")