from typing import List, Optional, Dict, TypedDict, Literal
from pydantic import BaseModel, Field


# ==================== STT & Meeting Analysis Schemas ====================

class FeedbackItem(BaseModel):
    """피드백 항목 (긍정적/개선 피드백 공통 사용)"""
    title: str = Field(description="피드백 주제")
    content: str = Field(description="피드백 내용을 자연스러운 단락으로 작성")

class LeaderFeedback(BaseModel):
    """매니저 피드백 (긍정적 피드백과 개선 피드백으로 구분)"""
    positive: List[FeedbackItem] = Field(description="매니저가 잘 수행한 측면들 (기존 positive_aspects)")
    negative: List[FeedbackItem] = Field(description="매니저 개선 피드백 리스트 (기존 leader_feedback)")

class QAItem(BaseModel):
    """Q&A 항목"""
    question_index: int = Field(description="질문 인덱스 (1부터 시작)")
    answer: str = Field(description="대화록에서 추출한 답변")

# LLM 출력 스키마
class AiCoreSummary(BaseModel):
    """핵심 요약 정보"""
    core_content: str = Field(description="회의의 핵심 내용")
    decisions_made: List[str] = Field(description="회의에서 내려진 공동 결정사항들")
    support_needs_blockers: List[str] = Field(description="지원 요청 및 블로커와 해결 방안들")

class MeetingAnalysis(BaseModel):
    """1-on-1 회의 분석 결과"""
    title: str = Field(description="회의를 한 줄로 요약한 제목 (예: '3분기 성과 리뷰 및 AI 프로젝트 진행 상황 점검')")
    speaker_mapping: List[str] = Field(description="화자 매핑 정보 - ['A의 실제이름', 'B의 실제이름'] 순서")
    leader_action_items: List[str] = Field(description="리더(매니저)가 수행할 액션 아이템 리스트")
    member_action_items: List[str] = Field(description="멤버(팀원)가 수행할 액션 아이템 리스트")
    ai_summary: str = Field(description="계층적 구조를 따르는 상세한 회의 내용 (마크다운 형식)")
    ai_core_summary: AiCoreSummary = Field(description="핵심 요약 정보")
    leader_feedback: LeaderFeedback = Field(description="매니저 피드백 (긍정적/개선 피드백)")
    qa_summary: List[QAItem] = Field(description="질문별 답변 리스트 - 모든 질문에 대해 완전한 답변 필수")

# 랭그래프 스키마 
class MeetingPipelineState(TypedDict):
    """LangGraph 파이프라인 상태 스키마"""
    recording_url: Optional[str]  # 프론트에서 전달받은 전체 URL
    qa_pairs: Optional[List[Dict]]
    participants_info: Optional[Dict]
    meeting_datetime: Optional[str]  # "2024-12-08T14:30:00" 형식
    only_title: Optional[bool]  # 제목만 생성할지 여부
    
    # Supabase 조회 결과 (내부 처리용)
    file_url: Optional[str]
    file_path: Optional[str]
    
    transcript: Optional[Dict]
    speaker_stats_percent: Optional[Dict]
    
    analysis_result: Optional[Dict]
    
    # 성능 측정 필드
    performance_metrics: Optional[Dict]
    performance_report: Optional[Dict]
    
    errors: List[str]
    status: str  # "pending", "processing", "completed", "failed"


# 미팅 분석 요청
class AnalyzeMeetingInput(BaseModel):
    """1on1 미팅 분석을 위한 입력 데이터 모델"""
    recording_url: Optional[str] = Field(default=None, description="녹음 파일의 전체 URL - only_title=true일 때는 불필요")
    qa_pairs: Optional[str] = Field(default=None, description="미리 준비된 질문-답변 쌍 (JSON 문자열)")
    participants_info: Optional[str] = Field(default=None, description="참가자 정보 (JSON 문자열, 예: {\"leader\": \"김지현\", \"member\": \"김준희\"})")
    meeting_datetime: Optional[str] = Field(default=None, description="회의 일시 (ISO 8601 형식, 예: 2024-12-08T14:30:00)")
    only_title: Optional[bool] = Field(default=False, description="제목만 생성할지 여부 (기본값: False)")


# ==================== Template Generator Schemas ====================

# 템플릿(질문) 생성
class TemplateGeneratorInput(BaseModel):
    """
    1on1 템플릿 생성을 위한 입력 데이터 모델
    """
    # --- 필수 필드 (반드시 입력해야 함) ---
    user_id: str = Field(..., description="조회할 사용자의 고유 ID")
    target_info: str = Field(..., description="1on1 대상자에 대한 정보 (팀, 직급, 이름 등)")
    purpose: str = Field(
        ...,
        description="1on1에서 리더가 얻고자 하는 정보의 카테고리 (쉼표로 구분된 값들)"
    )
    detailed_context: str = Field(default="Not specified", description="상세한 맥락, 구체적인 상황, 논의할 핵심 이슈. AI는 여기서 설명된 핵심 문제에 집중합니다.")
    num_questions: Literal['Simple', 'Standard', 'Advanced'] = Field(default="Standard", description="생성할 질문 수. Simple(~3개), Standard(~5개), Advanced(~7개).")
    question_composition: str = Field(
        default="Experience/Story-based",
        description="질문 유형 조합 (쉼표로 구분된 값들). 예시: 'Experience/Story-based, Growth/Goal-oriented'"
    )
    tone_and_manner: str = Field(..., description="원하는 어조와 말투 (e.g., 'Formal', 'Casual')")
    language: str = Field(default="Korean", description="출력 언어")
    include_guide: bool = Field(default=False, description="생성된 질문에 대한 활용 가이드 생성 여부")
    
    # 선택 필드
    use_previous_data: bool = Field(default=False, description="'반복' 선택 시 활성화. 이전 1on1 요약 데이터를 불러와 활용할지 여부.")
    previous_summary: Optional[str] = Field(default=None, description="'지난 기록 활용하기' 선택 시 자동으로 삽입될 이전 1on1 요약 및 액션아이템 정보.")
    generated_questions: Optional[Dict[str, str]] = Field(default=None, description="[가이드 생성용] 생성된 질문들 (key: 질문 번호, value: 질문 내용)")

class TemplateGeneratorOutput(BaseModel):
    """
    템플릿 생성 결과 모델.
    """
    generated_questions: Dict[str, str]

# 이메일 생성
class EmailGeneratorInput(BaseModel):
    """
    1on1 요약 이메일 생성을 위한 입력 데이터 모델
    """
    user_id: str
    target_info: str
    purpose: str
    detailed_context: str
    use_previous_data: bool
    previous_summary: Optional[str] = None
    language: Optional[str] = None  # 사용자가 선택한 언어 (미선택시 기본값 사용)

class EmailGeneratorOutput(BaseModel):
    """
    생성된 1on1 요약 이메일 결과 모델
    """
    generated_email: str = Field(..., description="사용자 입력을 바탕으로 생성된 이메일 본문")

# 활용 가이드 생성
class UsageGuideInput(BaseModel):
    """활용 가이드 생성 요청 스키마"""
    # 원본 입력 데이터
    user_id: str = Field(..., description="사용자 ID")
    target_info: str = Field(..., description="1on1 대상자 정보")
    purpose: str = Field(..., description="1on1 목적")
    detailed_context: str = Field(..., description="상세 맥락")
    
    # 생성된 템플릿 데이터
    generated_questions: Dict[str, str] = Field(..., description="생성된 질문들 (key: 질문 번호, value: 질문 내용)")
    
    # 추가 메타데이터
    language: Optional[str] = Field(default=None, description="사용자가 선택한 출력 언어 (미선택시 기본값 사용)")