from typing import Optional, Literal, Dict
from pydantic import BaseModel, Field, field_validator

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
    tone_and_manner: str = Field(..., description="원하는 어조와 말투 (e.g., '전문적이고 차분하게', '친근하고 부드럽게')")
    language: str = Field(default="Korean", description="출력 언어")
    include_guide: bool = Field(default=False, description="생성된 질문에 대한 활용 가이드 생성 여부")
    
    # 선택 필드
    use_previous_data: bool = Field(default=False, description="'반복' 선택 시 활성화. 이전 1on1 요약 데이터를 불러와 활용할지 여부.")
    previous_summary: Optional[str] = Field(default=None, description="'지난 기록 활용하기' 선택 시 자동으로 삽입될 이전 1on1 요약 및 액션아이템 정보.")
    generated_questions: Optional[Dict[str, str]] = Field(default=None, description="[가이드 생성용] 생성된 질문들 (key: 질문 번호, value: 질문 내용)")

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
    language: str = "Korean"

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
    language: str = Field(default="Korean", description="출력 언어")

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

class UsageGuideOutput(BaseModel):
    """활용 가이드 출력 스키마 - 단일 필드"""
    usage_guide: str = Field(..., description="이모지로 구분된 세 파트로 구성된 활용 가이드 텍스트")