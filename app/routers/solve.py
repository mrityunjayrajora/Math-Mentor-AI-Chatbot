"""
Solve Router - Main endpoint for solving math problems.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import SolveRequest, SolveResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["solve"])

# Pipeline instance will be injected via app state
_pipeline = None


def set_pipeline(pipeline):
    """Set the pipeline instance (called during app startup)."""
    global _pipeline
    _pipeline = pipeline


@router.post("/solve", response_model=SolveResponse)
async def solve_problem(request: SolveRequest):
    """
    Solve a math problem from multimodal input.

    Accepts text, image (base64), or audio (base64) input.
    Returns a complete solution with:
    - Extracted text and confidence
    - Parsed problem structure
    - Retrieved knowledge base context
    - Step-by-step solution
    - Verification result
    - Student-friendly explanation
    - Agent execution trace
    - HITL status
    - Similar past problems from memory
    """
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    try:
        # Validate that the correct input data is provided
        if request.input_mode == "text" and not request.text:
            raise HTTPException(status_code=400, detail="Text input required for text mode")
        elif request.input_mode == "image" and not request.image_base64:
            raise HTTPException(status_code=400, detail="Base64 image required for image mode")
        elif request.input_mode == "audio" and not request.audio_base64:
            raise HTTPException(status_code=400, detail="Base64 audio required for audio mode")

        response = await _pipeline.solve(request)

        logger.info(
            "solve_endpoint_complete",
            session_id=response.session_id,
            hitl_required=response.hitl_required,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("solve_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
