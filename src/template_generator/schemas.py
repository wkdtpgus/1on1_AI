from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class TemplateGeneratorInput(BaseModel):
    """
    1on1 템플릿 생성을 위한 입력 데이터 모델
    """
    target_info: str = Field(..., description="1on1 대상자 정보 (이름, 직무, 담당 역할 등)")
    purpose: Optional[str] = Field(None, description="1on1 목적/배경 (연간 리뷰, 온보딩, 이슈 대응 등)")
    problem: Optional[str] = Field(None, description="문제 상황 (퍼포먼스, 협업, 이직징후 등)")
    
    # Customization options
    is_new_1on1: bool = Field(False, description="신규 1on1 여부 (True: 신규, False: 반복)")
    num_questions: Literal['간결형', '표준형', '심층형'] = Field('표준형', description="생성할 질문 수")
    question_composition: Literal['오픈형', '객관형', '혼합형'] = Field('혼합형', description="질문 구성 요소")
    tone_and_manner: Literal['정중하게', '캐주얼하게', '구체적으로'] = Field('정중하게', description="대화 톤앤매너")
    include_report: bool = Field(False, description="결과 리포트 포함 여부")
    previous_summary: Optional[str] = Field(None, description="이전 1on1 요약 (반복 1on1의 경우)")


class TemplateGeneratorOutput(BaseModel):
    """
    생성된 1on1 템플릿 결과 모델
    """
    generated_questions: List[str] = Field(..., description="생성된 1on1 질문 목록")
    action_items_guidance: str = Field(..., description="액션 아이템 가이드")
    suggestion: Optional[str] = Field(None, description="입력이 부족할 경우를 위한 추가 제안 프롬프트")
