"""
Memory Router - Memory search and feedback endpoints.
"""

from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import FeedbackRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/memory", tags=["memory"])

# Memory store instance will be injected via app state
_memory_store = None


def set_memory_store(store):
    """Set the memory store instance (called during app startup)."""
    global _memory_store
    _memory_store = store


@router.get("/similar")
async def find_similar_problems(
    query: str = Query(..., description="Problem text to search for"),
    top_k: int = Query(5, description="Number of results to return"),
):
    """
    Find similar previously solved problems from memory.

    Uses embedding-based similarity search to find past problems
    that are similar to the given query.
    """
    if _memory_store is None:
        raise HTTPException(status_code=503, detail="Memory store not initialized")

    try:
        results = _memory_store.find_similar(query, top_k=top_k)
        return {
            "query": query,
            "count": len(results),
            "results": results,
        }
    except Exception as e:
        logger.error("memory_search_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit user feedback on a solved problem.

    Feedback is stored in memory and used for self-learning:
    - Correct solutions reinforce solution patterns
    - Incorrect solutions help avoid similar mistakes
    """
    if _memory_store is None:
        raise HTTPException(status_code=503, detail="Memory store not initialized")

    try:
        _memory_store.store_feedback(feedback)
        return {
            "session_id": feedback.session_id,
            "status": "feedback_stored",
            "is_correct": feedback.is_correct,
        }
    except Exception as e:
        logger.error("feedback_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to store feedback: {str(e)}")


@router.get("/problems")
async def list_problems(
    page: int = Query(1, description="Page number"),
    per_page: int = Query(20, description="Items per page"),
    topic: str = Query(None, description="Optional topic filter"),
):
    """
    List all solved problems from memory with pagination.
    """
    if _memory_store is None:
        raise HTTPException(status_code=503, detail="Memory store not initialized")

    try:
        return _memory_store.list_problems(page=page, per_page=per_page, topic=topic)
    except Exception as e:
        logger.error("memory_list_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list problems: {str(e)}")


@router.get("/stats")
async def get_memory_stats():
    """Get statistics about the memory store."""
    if _memory_store is None:
        raise HTTPException(status_code=503, detail="Memory store not initialized")

    return _memory_store.get_stats()


@router.delete("/problems/{session_id}")
async def delete_problem(session_id: str):
    """Delete a specific problem from memory."""
    if _memory_store is None:
        raise HTTPException(status_code=503, detail="Memory store not initialized")

    deleted = _memory_store.delete_problem(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"status": "deleted", "session_id": session_id}


@router.delete("/problems")
async def clear_all_memory():
    """Clear all problems from memory."""
    if _memory_store is None:
        raise HTTPException(status_code=503, detail="Memory store not initialized")

    count = _memory_store.clear_all()
    return {"status": "cleared", "deleted_count": count}
