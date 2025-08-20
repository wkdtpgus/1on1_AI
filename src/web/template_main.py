"""
FastAPI server for testing streaming template generation.
Run with: uvicorn test_streaming_api:app --reload --port 8000
"""

import json
from typing import Dict, Any, Union, Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from src.utils.template_schemas import TemplateGeneratorInput, EmailGeneratorOutput, UsageGuideOutput, UsageGuideInput, EmailGeneratorInput
from src.services.template_generator.generate_template import generate
from src.services.template_generator.generate_email import generate_email
from src.services.template_generator.generate_usage_guide import generate_usage_guide


app = FastAPI(title="1on1 Template Generator API")

# Add CORS middleware for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/generate", response_model=Union[Dict[str, Any], EmailGeneratorOutput, UsageGuideOutput])
async def generate_endpoint(
    input_data: TemplateGeneratorInput,
    generation_type: Literal['template', 'email', 'guide'] = Query("template", description="Generation type")
):
    """
    Generate a 1-on-1 template, a summary email, or a usage guide based on the input.
    """
    try:
        if generation_type == 'template':
            result = await generate(input_data)
        elif generation_type == 'email':
            email_input = EmailGeneratorInput(
                user_id=input_data.user_id,
                target_info=input_data.target_info,
                purpose=input_data.purpose,
                detailed_context=input_data.detailed_context,
                use_previous_data=input_data.use_previous_data,
                previous_summary=input_data.previous_summary,
                language=input_data.language
            )
            result = await generate_email(email_input)
        elif generation_type == 'guide':
            if not input_data.generated_questions:
                raise HTTPException(status_code=400, detail="Usage guide generation requires 'generated_questions'.")
            
            guide_input = UsageGuideInput(
                user_id=input_data.user_id,
                target_info=input_data.target_info,
                purpose=input_data.purpose,
                detailed_context=input_data.detailed_context,
                generated_questions=input_data.generated_questions,
                language=input_data.language
            )
            result = await generate_usage_guide(guide_input)
        else:
            # This case might be redundant due to Literal validation, but good for safety
            raise HTTPException(status_code=400, detail="Invalid generation type specified.")
        return result
    except Exception as e:
        # Log the exception for debugging purposes
        print(f"Error during generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # reload=True 옵션을 사용하려면 애플리케이션을 "파일명:객체명" 형태의 문자열로 전달해야 합니다.
    uvicorn.run("src.web.template_main:app", host="0.0.0.0", port=8000, reload=True)
