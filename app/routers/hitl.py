"""
HITL Router - Human-in-the-Loop review endpoints.
"""

from typing import List

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    HITLPendingItem,
    HITLReviewRequest,
    HITLReviewResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/hitl", tags=["hitl"])

# HITL manager instance will be injected via app state
_hitl_manager = None


def set_hitl_manager(manager):
    """Set the HITL manager instance (called during app startup)."""
    global _hitl_manager
    _hitl_manager = manager


@router.get("/pending", response_model=List[HITLPendingItem])
async def get_pending_reviews():
    """
    Get all items pending HITL review.

    Returns items that need human review due to:
    - Low OCR/ASR confidence
    - Parser detected ambiguity
    - Verifier is not confident in the solution
    """
    if _hitl_manager is None:
        raise HTTPException(status_code=503, detail="HITL manager not initialized")

    return _hitl_manager.get_pending_items()


@router.post("/review", response_model=HITLReviewResponse)
async def review_item(request: HITLReviewRequest):
    """
    Submit a HITL review for a pending item.

    Actions:
    - "approve": Approve the solution as-is
    - "reject": Reject the solution with optional feedback
    - "correct": Provide corrected text/answer
    """
    if _hitl_manager is None:
        raise HTTPException(status_code=503, detail="HITL manager not initialized")

    if request.action not in ("approve", "reject", "correct"):
        raise HTTPException(
            status_code=400,
            detail="Action must be one of: approve, reject, correct",
        )

    response = _hitl_manager.process_review(request)

    logger.info(
        "hitl_review_submitted",
        session_id=request.session_id,
        action=request.action,
    )

    return response


@router.get("/{session_id}")
async def get_review_status(session_id: str):
    """Get the HITL review status for a specific session."""
    if _hitl_manager is None:
        raise HTTPException(status_code=503, detail="HITL manager not initialized")

    item = _hitl_manager.get_item(session_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "status": item["status"].value,
        "reasons": [r.value for r in item.get("reasons", [])],
        "created_at": item.get("created_at"),
        "corrections": item.get("corrections"),
    }
