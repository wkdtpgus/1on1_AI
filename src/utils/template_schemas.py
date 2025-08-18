from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union, Literal, Dict

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

    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, v):
        if not v:
            return v
        
        allowed_values = {'Growth', 'Satisfaction', 'Relationships', 'Junior Development', 'Work'}
        input_values = {val.strip() for val in v.split(',')}
        
        invalid_values = input_values - allowed_values
        if invalid_values:
            raise ValueError(f"Invalid purpose values: {invalid_values}. Allowed values are: {allowed_values}")
        
        return v
    detailed_context: str = Field(default="Not specified", description="상세한 맥락, 구체적인 상황, 논의할 핵심 이슈. AI는 여기서 설명된 핵심 문제에 집중합니다.")
    num_questions: Literal['Simple', 'Standard', 'Advanced'] = Field(default="Standard", description="생성할 질문 수. Simple(~3개), Standard(~5개), Advanced(~7개).")
    question_composition: str = Field(
        default="Experience/Story-based",
        description="질문 유형 조합 (쉼표로 구분된 값들). 예시: 'Experience/Story-based, Growth/Goal-oriented'"
    )

    @field_validator('question_composition')
    @classmethod
    def validate_question_composition(cls, v):
        if not v:
            return v
        
        allowed_values = {
            'Experience/Story-based', 
            'Reflection/Thought-provoking', 
            'Action/Implementation-focused', 
            'Relationship/Collaboration', 
            'Growth/Goal-oriented', 
            'Multiple choice'
        }
        input_values = {val.strip() for val in v.split(',')}
        
        invalid_values = input_values - allowed_values
        if invalid_values:
            raise ValueError(f"Invalid question_composition values: {invalid_values}. Allowed values are: {allowed_values}")
        
        return v
    tone_and_manner: str = Field(default="Formal", description="질문의 톤과 매너", example='Formal')
    language: str = Field(default="Korean", description="생성될 질문의 언어", example='Korean')
    
    # 선택 필드
    use_previous_data: bool = Field(default=False, description="'반복' 선택 시 활성화. 이전 1on1 요약 데이터를 불러와 활용할지 여부.")
    previous_summary: Optional[str] = Field(default=None, description="'지난 기록 활용하기' 선택 시 자동으로 삽입될 이전 1on1 요약 및 액션아이템 정보.")

class TemplateGeneratorOutput(BaseModel):
    """
    생성된 1on1 템플릿 결과 모델
    """
    generated_questions: List[str] = Field(..., description="생성된 1on1 질문 목록")

class SummaryGeneratorOutput(BaseModel):
    """
    생성된 1on1 템플릿 요약 결과 모델
    """
    template_summary: str = Field(..., description="사용자 입력을 바탕으로 한 템플릿 구성 요약")

class UsageGuideInput(BaseModel):
    """활용 가이드 생성을 위한 입력 스키마"""
    # 원본 입력 데이터
    user_id: str = Field(..., description="사용자 ID")
    target_info: str = Field(..., description="1on1 대상자 정보")
    purpose: str = Field(..., description="1on1 목적")
    detailed_context: str = Field(..., description="상세 맥락")
    
    # 생성된 템플릿 데이터
    generated_questions: List[Dict[str, str]] = Field(..., description="생성된 질문들 (question, intent 포함)")
    
    # 추가 메타데이터
    language: str = Field(default="Korean", description="출력 언어")


class UsageGuideOutput(BaseModel):
    """활용 가이드 출력 스키마 - 3문장 구조"""
    opening_strategy: str = Field(..., description="리더가 질문을 어떻게 활용할지, 1on1 흐름과 분위기 조성 방법")
    needs_reflection: str = Field(..., description="어떤 니즈를 어떤 질문으로 반영했는지에 대한 안내")
    flow_management: str = Field(..., description="전체 질문들의 흐름, 맥락, 정보 획득 전략")


class GuideMetadata(BaseModel):
    """가이드 생성을 위한 분석 메타데이터"""
    total_questions: int
    intent_distribution: Dict[str, int]
    sensitive_topics: List[str]
    question_flow_pattern: str