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
    dialogue_type: Literal['신규', '반복'] = Field(
        '반복', description="대화가 신규인지, 반복 대화인지 선택."
    )
    use_previous_data: bool = Field(
        False, description="'반복' 선택 시 활성화. 이전 1on1 요약 데이터를 불러와 활용할지 여부."
    )
    previous_summary: Optional[str] = Field(
        None, description="'지난 기록 활용하기' 선택 시 자동으로 삽입될 이전 1on1 요약 및 액션아이템 정보."
    )
    num_questions: Literal['간단', '표준', '심화'] = Field(
        '표준', description="생성할 질문의 개수. 간단(약 3개), 표준(약 5개), 심화(약 7개)."
    )
    question_composition: List[Literal[
        '오픈형', '행동유도형', '객관식', 
        '성과/목표', '관계/협업', '성장/커리어', '개인/안부'
    ]] = Field(
        default_factory=list,
        description="질문 유형 조합. 예: ['오픈형', '성과/목표']"
    )
    tone_and_manner: int = Field(
        3, ge=0, le=5, description="대화의 톤앤매너. 0(정중) ~ 5(캐주얼)."
    )
    creativity: float = Field(
        0.6, ge=0.2, le=1.0, description="질문 생성의 창의성(Temperature). 0.2 ~ 1.0."
    )


class TemplateGeneratorOutput(BaseModel):
    """
    생성된 1on1 템플릿 결과 모델
    """
    generated_questions: List[str] = Field(..., description="생성된 1on1 질문 목록")
    action_items_guidance: str = Field(..., description="미팅 후 도출할 액션 아이템 가이드")
    suggestion: Optional[str] = Field(None, description="입력이 부족할 경우를 위한 추가 제안 프롬프트")
