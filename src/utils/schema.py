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
    qa_summary: List[QAItem] = Field(description="질문별 답변 리스트 - 모든 질문에 대해 완전한 답변 필수")
    quick_review: QuickReview = Field(description="회의 빠른 리뷰 정보")
    detailed_discussion: str = Field(description="계층적 구조를 따르는 상세한 회의 내용 (마크다운 형식)")
    feedback: List[FeedbackItem] = Field(description="매니저 개선 피드백 리스트")
    positive_aspects: List[str] = Field(description="매니저가 잘 수행한 측면들")


# 기획회의 전용 스키마
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
    detailed_discussion: str = Field(description="한국 기업 회의록 형식을 따르는 상세 회의 내용 (마크다운 형식)")
    strategic_insights: List[StrategicInsight] = Field(description="전략적 인사이트 리스트")
    innovation_ideas: List[str] = Field(description="브레인스토밍 중 논의된 혁신적 컨셉 또는 접근법")
    risks_challenges: List[RiskChallenge] = Field(description="식별된 리스크 및 도전 과제")
    next_steps: List[NextStep] = Field(description="다음 단계 액션 아이템")


# 일반회의 전용 스키마
class DiscussionTopic(BaseModel):
    """논의 주제 항목"""
    topic: str = Field(description="주요 논의 주제 또는 안건 항목")
    summary: str = Field(description="논의된 핵심 사항 및 결과")
    participants: str = Field(description="이 논의의 주요 기여자들 (알려진 경우)")
    decisions: str = Field(description="이 주제와 관련된 결정 사항")


class TeamContribution(BaseModel):
    """팀 기여 항목"""
    contribution: str = Field(description="회의 중 공유된 개인 또는 팀의 기여 및 가치있는 입력")


class ActionItem(BaseModel):
    """액션 아이템"""
    item: str = Field(description="구체적인 액션 아이템 또는 작업")
    owner: str = Field(description="담당자 또는 담당 팀")
    deadline: str = Field(description="목표 완료 일정 (언급된 경우)")
    priority: str = Field(description="우선순위 수준 (High/Medium/Low)")


class FollowUpItem(BaseModel):
    """후속 조치 항목"""
    item: str = Field(description="향후 논의 또는 후속 조치가 필요한 항목")
    context: str = Field(description="후속 조치의 배경 또는 이유")
    next_steps: str = Field(description="제안된 다음 단계 또는 일정")


class GeneralMeetingAnalysis(BaseModel):
    """일반회의 분석 결과"""
    title: str = Field(description="일반회의 포커스를 한 줄로 요약")
    detailed_discussion: str = Field(description="한국 기업 회의록 형식을 따르는 상세 회의 내용 (마크다운 형식)")
    discussion_topics: List[DiscussionTopic] = Field(description="논의 주제 리스트")
    team_contributions: List[str] = Field(description="팀 기여 및 가치있는 입력")
    action_items: List[ActionItem] = Field(description="액션 아이템 리스트")
    follow_up_items: List[FollowUpItem] = Field(description="후속 조치 항목 리스트")


# 주간회의 전용 스키마
class ProgressUpdate(BaseModel):
    """진행 상황 업데이트"""
    area: str = Field(description="프로젝트 또는 업무 영역")
    status: str = Field(description="현재 진행 상황 및 완료 비율")
    owner: str = Field(description="담당자 또는 담당 팀")
    achievements: str = Field(description="이번 주에 완료된 사항")
    next_steps: str = Field(description="다음 주 계획된 작업")


class BlockerChallenge(BaseModel):
    """블로커 및 도전과제"""
    blocker: str = Field(description="구체적인 도전과제 또는 장애물")
    impact: str = Field(description="진행이나 일정에 미치는 영향")
    owner: str = Field(description="영향을 받는 사람 또는 해결 담당자")
    proposed_solution: str = Field(description="제안된 해결 접근법")
    support_needed: str = Field(description="필요한 지원 또는 리소스")


class WeeklyPriority(BaseModel):
    """주간 우선순위"""
    priority: str = Field(description="High/Medium/Low 우선순위 작업 또는 목표")
    description: str = Field(description="작업에 대한 상세 설명")
    owner: str = Field(description="담당자 또는 담당 팀")
    deadline: str = Field(description="목표 완료 일정")
    dependencies: str = Field(description="종속성 또는 블로커")


class TeamCoordination(BaseModel):
    """팀 협업"""
    item: str = Field(description="협업 또는 조율이 필요한 사항")
    participants: str = Field(description="관련된 사람 또는 팀")
    timeline: str = Field(description="협업이 필요한 시점")
    purpose: str = Field(description="협업의 목표 또는 결과")


class WeeklyMeetingAnalysis(BaseModel):
    """주간회의 분석 결과"""
    title: str = Field(description="주간회의 포커스를 한 줄로 요약")
    detailed_discussion: str = Field(description="한국 기업 회의록 형식을 따르는 상세 회의 내용 (마크다운 형식)")
    progress_updates: List[ProgressUpdate] = Field(description="진행 상황 업데이트 리스트")
    blockers_challenges: List[BlockerChallenge] = Field(description="블로커 및 도전과제 리스트")
    next_week_priorities: List[WeeklyPriority] = Field(description="다음 주 우선순위 리스트")
    team_coordination: List[TeamCoordination] = Field(description="팀 협업 리스트")