"""
FastAPI server for testing streaming template generation.
Run with: uvicorn test_streaming_api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from src.utils.template_schemas import TemplateGeneratorInput, EmailGeneratorOutput
from src.services.template_generator.generate_template import generate
from src.services.template_generator.generate_email import generate_email


app = FastAPI(title="1on1 Template Generator API")

# Add CORS middleware for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/generate_template")
async def generate_template_endpoint(input_data: TemplateGeneratorInput):
    """
    Generate template with streaming (SSE response).
    """
    try:
        return StreamingResponse(
            generate(input_data),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
    except Exception as e:
        # Log the exception for debugging purposes
        print(f"Error during template generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_email", response_model=EmailGeneratorOutput)
async def generate_email_endpoint(input_data: TemplateGeneratorInput):
    """
    Generate a summary email based on the input data.
    """
    try:
        result = await generate_email(input_data)
        return result
    except Exception as e:
        print(f"Error during email generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # reload=True 옵션을 사용하려면 애플리케이션을 "파일명:객체명" 형태의 문자열로 전달해야 합니다.
    uvicorn.run("template_main:app", host="0.0.0.0", port=8000, reload=True)
