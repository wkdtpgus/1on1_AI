from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class TemplateGeneratorInput(BaseModel):
    """
    1on1 템플릿 생성을 위한 입력 데이터 모델
    """
    # --- 필수 입력 데이터 (누락 가능) ---
    target_info: Optional[str] = Field(None, description="1on1 대상자에 대한 정보 (팀, 직급, 이름 등)")
    purpose: Optional[str] = Field(None, description="1on1 미팅의 목적 또는 배경")
    problem: Optional[str] = Field(None, description="현재 겪고 있는 어려움이나 문제 상황")

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
        'Experience/Story-based', 'Reflection/Thought-provoking', 'Action/Implementation-focused', 
        'Relationship/Collaboration', 'Growth/Goal-oriented', 'Multiple choice'
    ]] = Field(
        default_factory=list,
        description="Question type combination. Example: ['Experience/Story-based', 'Growth/Goal-oriented']"
    )
    tone_and_manner: Literal['Formal', 'Casual'] = Field(
        'Formal', description="Conversation tone and manner. Formal or Casual."
    )
    creativity: float = Field(
        0.6, ge=0.2, le=1.0, description="질문 생성의 창의성(Temperature). 0.2 ~ 1.0."
    )


class TemplateGeneratorOutput(BaseModel):
    """
    생성된 1on1 템플릿 결과 모델
    """
    generated_questions: List[str] = Field(..., description="생성된 1on1 질문 목록")
    template_summary: str = Field(..., description="사용자 입력을 바탕으로 한 템플릿 구성 요약")
