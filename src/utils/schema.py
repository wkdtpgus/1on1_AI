from typing import List
from pydantic import BaseModel, Field


class QuickReview(BaseModel):
    """회의 빠른 리뷰 정보"""
    key_takeaways: str = Field(description="주요 사항들")
    decisions_made: str = Field(description="회의에서 내린 공동 결정 사항")
    action_items: str = Field(description="담당자와 마감일이 포함된 액션 아이템")
    support_needs_blockers: str = Field(description="지원 요청사항과 블로커 및 해결 방안")


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
    title: str = Field(description="회의를 한 줄로 요약한 제목 (예: '3분기 성과 리뷰 및 AI 프로젝트 진행 상황 점검')")
    quick_review: QuickReview = Field(description="회의 빠른 리뷰 정보")
    detailed_discussion: str = Field(description="계층적 구조를 따르는 상세한 회의 내용 (마크다운 형식)")
    feedback: List[FeedbackItem] = Field(description="매니저 개선 피드백 리스트")
    positive_aspects: List[str] = Field(description="매니저가 잘 수행한 측면들")
    qa_summary: List[QAItem] = Field(description="질문별 답변 리스트")


# 기획회의 전용 스키마
class PlanningQuickReview(BaseModel):
    """기획회의 빠른 리뷰 정보"""
    key_planning_outcomes: str = Field(description="핵심 기획 결과 및 전략적 결정")
    major_decisions: str = Field(description="주요 전략적 선택 및 승인된 접근 방식")
    action_items: str = Field(description="담당자와 마감일이 포함된 기획 액션 아이템")
    resource_timeline: str = Field(description="예산, 리소스, 주요 마일스톤")


class StrategicInsight(BaseModel):
    """전략적 인사이트 항목"""
    category: str = Field(description="전략 영역 (예: 시장 분석, 제품 전략, 리소스 계획)")
    insight: str = Field(description="핵심 전략적 인사이트 또는 결정")
    rationale: str = Field(description="결정의 근거 및 이유")
    impact: str = Field(description="예상되는 영향 또는 결과")


class RiskChallenge(BaseModel):
    """리스크 및 도전 과제 항목"""
    risk: str = Field(description="식별된 리스크 또는 도전 과제")
    impact: str = Field(description="해결하지 않을 경우 예상 영향")
    mitigation: str = Field(description="제안된 해결책 또는 완화 방안")


class NextStep(BaseModel):
    """다음 단계 액션 항목"""
    item: str = Field(description="구체적인 다음 단계 또는 후속 액션")
    owner: str = Field(description="담당자 또는 담당 팀")
    deadline: str = Field(description="목표 완료 일정 (언급된 경우)")
    priority: str = Field(description="우선순위 수준 (High/Medium/Low)")


class PlanningMeetingAnalysis(BaseModel):
    """기획회의 분석 결과"""
    title: str = Field(description="기획회의 포커스를 한 줄로 요약 (예: '2024년 신제품 런칭 전략 기획 회의')")
    quick_review: PlanningQuickReview = Field(description="기획회의 빠른 리뷰 정보")
    detailed_discussion: str = Field(description="한국 기업 회의록 형식을 따르는 상세 회의 내용 (마크다운 형식)")
    strategic_insights: List[StrategicInsight] = Field(description="전략적 인사이트 리스트")
    innovation_ideas: List[str] = Field(description="브레인스토밍 중 논의된 혁신적 컨셉 또는 접근법")
    risks_challenges: List[RiskChallenge] = Field(description="식별된 리스크 및 도전 과제")
    next_steps: List[NextStep] = Field(description="다음 단계 액션 아이템")