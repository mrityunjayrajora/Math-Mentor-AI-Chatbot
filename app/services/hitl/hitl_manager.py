"""
HITL Manager - Human-in-the-Loop queue and review logic.
"""

from datetime import datetime
from typing import Dict, List, Optional

from app.models.enums import HITLStatus, HITLTriggerReason
from app.models.schemas import (
    HITLPendingItem,
    HITLReviewRequest,
    HITLReviewResponse,
    SolveResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HITLManager:
    """
    Manages the Human-in-the-Loop queue.
    Stores items pending review and processes approvals/corrections.
    """

    def __init__(self):
        # In-memory queue: session_id → pending item data
        self._pending: Dict[str, dict] = {}
        # History of all HITL interactions
        self._history: List[dict] = []

    def add_to_queue(
        self,
        session_id: str,
        reasons: List[HITLTriggerReason],
        solve_response: SolveResponse,
    ):
        """
        Add an item to the HITL review queue.

        Args:
            session_id: The pipeline session ID.
            reasons: List of reasons HITL was triggered.
            solve_response: The full pipeline response.
        """
        pending_item = {
            "session_id": session_id,
            "reasons": reasons,
            "solve_response": solve_response,
            "status": HITLStatus.PENDING_REVIEW,
            "created_at": datetime.utcnow(),
        }

        self._pending[session_id] = pending_item

        logger.info(
            "hitl_item_added",
            session_id=session_id,
            reasons=[r.value for r in reasons],
        )

    def get_pending_items(self) -> List[HITLPendingItem]:
        """Get all items pending HITL review."""
        items = []
        for session_id, data in self._pending.items():
            if data["status"] == HITLStatus.PENDING_REVIEW:
                response = data["solve_response"]
                items.append(HITLPendingItem(
                    session_id=session_id,
                    reasons=data["reasons"],
                    extracted_text=response.extracted_text,
                    parsed_problem=response.parsed_problem,
                    solution=response.solution,
                    verification=response.verification,
                    created_at=data["created_at"],
                ))
        return items

    def get_item(self, session_id: str) -> Optional[dict]:
        """Get a specific HITL item by session ID."""
        return self._pending.get(session_id)

    def process_review(self, review: HITLReviewRequest) -> HITLReviewResponse:
        """
        Process a HITL review action (approve, reject, correct).

        Args:
            review: The review request with action and optional corrections.

        Returns:
            HITLReviewResponse with updated status.
        """
        item = self._pending.get(review.session_id)
        if item is None:
            return HITLReviewResponse(
                session_id=review.session_id,
                status=HITLStatus.NOT_REQUIRED,
                message="Session not found in HITL queue",
            )

        if review.action == "approve":
            item["status"] = HITLStatus.APPROVED
            message = "Solution approved by reviewer"

        elif review.action == "reject":
            item["status"] = HITLStatus.REJECTED
            message = f"Solution rejected: {review.feedback or 'No reason provided'}"

        elif review.action == "correct":
            item["status"] = HITLStatus.CORRECTED
            # Store the corrections
            item["corrections"] = {
                "corrected_text": review.corrected_text,
                "corrected_answer": review.corrected_answer,
                "feedback": review.feedback,
                "corrected_at": datetime.utcnow().isoformat(),
            }
            message = "Solution corrected by reviewer"

        else:
            return HITLReviewResponse(
                session_id=review.session_id,
                status=item["status"],
                message=f"Unknown action: {review.action}",
            )

        # Record in history
        self._history.append({
            "session_id": review.session_id,
            "action": review.action,
            "feedback": review.feedback,
            "corrected_text": review.corrected_text,
            "corrected_answer": review.corrected_answer,
            "timestamp": datetime.utcnow().isoformat(),
        })

        logger.info(
            "hitl_review_processed",
            session_id=review.session_id,
            action=review.action,
        )

        return HITLReviewResponse(
            session_id=review.session_id,
            status=item["status"],
            message=message,
        )

    def get_corrections_history(self) -> List[dict]:
        """
        Get all past corrections for learning.
        Used by the memory system to learn from HITL corrections.
        """
        return [
            h for h in self._history
            if h["action"] == "correct"
        ]

    def get_ocr_corrections(self) -> List[dict]:
        """
        Extract OCR-specific corrections from history.
        Returns list of {"original": ..., "corrected": ...} dicts.
        """
        corrections = []
        for h in self._history:
            if (
                h["action"] == "correct"
                and h.get("corrected_text")
            ):
                item = self._pending.get(h["session_id"], {})
                response = item.get("solve_response")
                if response:
                    corrections.append({
                        "original": response.extracted_text,
                        "corrected": h["corrected_text"],
                    })
        return corrections
