"""
FastAPI server for testing streaming template generation.
Run with: uvicorn test_streaming_api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from src.utils.template_schemas import TemplateGeneratorInput
from src.services.template_generator.generate_template import generate_template

app = FastAPI(title="1on1 Template Generator API")

# Add CORS middleware for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/generate")
async def generate_template_endpoint(input_data: TemplateGeneratorInput):
    """
    Generate template with streaming (SSE response).
    """
    try:
        return StreamingResponse(
            generate_template(input_data),
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
