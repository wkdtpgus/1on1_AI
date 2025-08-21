from typing import Union, Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.services.template_generator.generate_email import generate_email
from src.services.template_generator.generate_template import generate_template
from src.services.template_generator.generate_usage_guide import generate_usage_guide
from src.utils.template_schemas import (
    EmailGeneratorInput,
    EmailGeneratorOutput,
    TemplateGeneratorInput,
    TemplateGeneratorOutput,
    UsageGuideInput,
    UsageGuideOutput,
)

app = FastAPI(title="1on1 Template Generator API")

# Add CORS middleware for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post(
    "/generate",
    response_model=Union[TemplateGeneratorOutput, EmailGeneratorOutput, UsageGuideOutput],
)
async def generate_endpoint(
    input_data: TemplateGeneratorInput,
    generation_type: Literal["template", "email", "guide"] = Query(
        "template", description="Generation type"
    ),
):

    try:
        if generation_type == "template":
            result = await generate_template(input_data)
        elif generation_type == "email":
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
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
