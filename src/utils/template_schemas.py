from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal

class TemplateGeneratorInput(BaseModel):
    """
    1on1 템플릿 생성을 위한 입력 데이터 모델
    """
    user_id: str = Field(..., description="조회할 사용자의 고유 ID")
    # --- 필수 입력 데이터 (누락 가능) ---
    target_info: Optional[str] = Field(None, description="1on1 대상자에 대한 정보 (팀, 직급, 이름 등)")
    purpose: List[Literal[
        'Growth',
        'Satisfaction',
        'Relationships',
        'Junior Development',
        'Work'
    ]] = Field(
        default_factory=list,
        description="Categories of information the leader wants to gain from the 1on1 (multiple selections possible)"
    )
    detailed_context: Optional[str] = Field(None, description="Detailed context, specific situations, or key issues to discuss. The AI will focus on the core problem described here.")

    # --- 커스터마이징 옵션 ---
    dialogue_type: Optional[Literal['New', 'Recurring']] = Field(
        None, description="Whether the conversation is new or recurring."
    )
    use_previous_data: bool = Field(
        False, description="'반복' 선택 시 활성화. 이전 1on1 요약 데이터를 불러와 활용할지 여부."
    )
    previous_summary: Optional[str] = Field(
        None, description="'지난 기록 활용하기' 선택 시 자동으로 삽입될 이전 1on1 요약 및 액션아이템 정보."
    )
    num_questions: Optional[Literal['Simple', 'Standard', 'Advanced']] = Field(
        None, description="Number of questions to generate. Simple(~3), Standard(~5), Advanced(~7)."
    )
    question_composition: List[Literal[
        'Experience/Story-based', 
        'Reflection/Thought-provoking', 
        'Action/Implementation-focused', 
        'Relationship/Collaboration', 
        'Growth/Goal-oriented', 
        'Multiple choice'
    ]] = Field(
        default_factory=list,
        description="Question type combination. Example: ['Experience/Story-based', 'Growth/Goal-oriented']"
    )
    tone_and_manner: Optional[Literal['Formal', 'Casual']] = Field(
        'Formal', 
        description="The desired tone and manner of the questions."
    )


class TemplateGeneratorOutput(BaseModel):
    """
    생성된 1on1 템플릿 결과 모델
    """
    generated_questions: List[str] = Field(..., description="생성된 1on1 질문 목록")
