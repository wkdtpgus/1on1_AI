from fastapi import APIRouter, HTTPException, status

from src.template_generator.chains import generate_template
from src.template_generator.schemas import TemplateGeneratorInput, TemplateGeneratorOutput

router = APIRouter(
    prefix="/templates",
    tags=["Template Generator"],
)


@router.post(
    "/generate", 
    response_model=TemplateGeneratorOutput, 
    summary="Generate 1-on-1 Template",
    description="Generates a personalized 1-on-1 meeting template using LangChain."
)
async def generate_1on1_template(input_data: TemplateGeneratorInput):
    """
    사용자 입력을 받아 1on1 템플릿을 생성합니다.
    
    - **target_info**: 1on1 대상자 정보 (필수)
    - **purpose**: 1on1 목적/배경
    - **problem**: 주요 문제 상황
    - **...** (기타 커스터마이징 옵션)
    """
    try:
        # LangChain 체인을 호출하여 결과를 생성합니다.
        result = await generate_template(input_data)
        return TemplateGeneratorOutput(**result)
    except Exception as e:
        # 에러 발생 시 500 Internal Server Error를 반환합니다.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during template generation: {str(e)}"
        )
