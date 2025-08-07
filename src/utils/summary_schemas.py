from pydantic import BaseModel, Field

class SummaryGeneratorOutput(BaseModel):
    """
    생성된 1on1 템플릿 요약 결과 모델
    """
    template_summary: str = Field(..., description="사용자 입력을 바탕으로 한 템플릿 구성 요약")
