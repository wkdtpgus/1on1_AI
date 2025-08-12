from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

from src.services.template_generator.generate_template_streaming_v2 import generate_template_streaming_v2
from src.utils.template_schemas import TemplateGeneratorInput

app = FastAPI(
    title="1on1 AI Template Generator API V2",
    description="Provides streaming and non-streaming endpoints for generating 1-on-1 meeting templates.",
    version="2.0.0",
)

async def stream_wrapper(input_data: TemplateGeneratorInput) -> AsyncGenerator[str, None]:
    """A wrapper to handle the async generator and potential exceptions."""
    try:
        async for chunk in generate_template_streaming_v2(input_data):
            yield chunk
    except ValueError as e:
        # This part might not be able to send a proper HTTP exception if streaming has started.
        # Logging is important here.
        print(f"Validation Error: {e}")
        # A more robust solution would involve a different error signaling mechanism.
    except Exception as e:
        print(f"An unexpected error occurred during streaming: {e}")

@app.get("/", tags=["Status"])
async def read_root():
    """Root endpoint to check API status."""
    return {"status": "1on1 AI Template Generator API V2 is running"}

@app.post("/templates/generate-streaming-v2", tags=["Template Generation"])
async def generate_template_endpoint_v2(input_data: TemplateGeneratorInput):
    """Streams a 1-on-1 meeting template based on the provided input data."""
    return StreamingResponse(stream_wrapper(input_data), media_type="text/plain; charset=utf-8")
