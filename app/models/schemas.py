"""
Pydantic schemas for request/response models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.enums import (
    HITLStatus,
    HITLTriggerReason,
    InputMode,
    MathTopic,
    SolvingStrategy,
)


# ── Input Schemas ──


class SolveRequest(BaseModel):
    """Request to solve a math problem."""
    input_mode: InputMode
    text: Optional[str] = None
    image_base64: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_format: Optional[str] = "wav"  # wav, mp3, etc.


# ── Agent Output Schemas ──


class ExtractionResult(BaseModel):
    """Result from OCR / ASR / text extraction."""
    extracted_text: str
    confidence: float = 1.0
    input_mode: InputMode
    hitl_required: bool = False
    hitl_reason: Optional[HITLTriggerReason] = None
    raw_details: Optional[Dict[str, Any]] = None


class ParsedProblem(BaseModel):
    """Structured math problem from the Parser Agent."""
    problem_text: str
    topic: MathTopic = MathTopic.ALGEBRA
    variables: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    detected_problems: List[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_reason: Optional[str] = None


class RoutingResult(BaseModel):
    """Routing decision from the Intent Router Agent."""
    topic: MathTopic
    sub_type: str = ""
    strategy: SolvingStrategy = SolvingStrategy.ANALYTICAL
    required_tools: List[str] = Field(default_factory=list)
    retrieval_queries: List[str] = Field(default_factory=list)


class SolutionStep(BaseModel):
    """A single step in the solution."""
    step_number: int
    description: str
    result: str = ""


class SolverResult(BaseModel):
    """Solution from the Solver Agent."""
    steps: List[SolutionStep] = Field(default_factory=list)
    final_answer: str = ""
    tools_used: List[str] = Field(default_factory=list)
    sources_cited: List[str] = Field(default_factory=list)


class VerificationResult(BaseModel):
    """Verification result from the Verifier Agent."""
    is_correct: bool = True
    confidence: float = 0.0
    issues: List[str] = Field(default_factory=list)
    verification_method: str = ""
    suggestions: List[str] = Field(default_factory=list)


class ExplanationResult(BaseModel):
    """Explanation from the Explainer Agent."""
    summary: str = ""
    detailed_steps: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    tips: List[str] = Field(default_factory=list)


# ── Agent Trace ──


class AgentTraceEntry(BaseModel):
    """A single entry in the agent execution trace."""
    agent_name: str
    action: str
    duration_ms: float = 0.0
    success: bool = True
    details: Optional[Dict[str, Any]] = None


# ── Retrieved Context ──


class RetrievedChunk(BaseModel):
    """A chunk retrieved from the knowledge base."""
    content: str
    source: str
    relevance_score: float = 0.0


# ── Pipeline Response ──


class SolveResponse(BaseModel):
    """Complete response from the solve pipeline."""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    input_mode: InputMode
    extracted_text: str = ""
    extraction_confidence: float = 1.0

    parsed_problem: Optional[ParsedProblem] = None
    routing: Optional[RoutingResult] = None
    retrieved_context: List[RetrievedChunk] = Field(default_factory=list)
    solution: Optional[SolverResult] = None
    verification: Optional[VerificationResult] = None
    explanation: Optional[ExplanationResult] = None

    overall_confidence: float = 0.0
    agent_trace: List[AgentTraceEntry] = Field(default_factory=list)

    hitl_required: bool = False
    hitl_status: HITLStatus = HITLStatus.NOT_REQUIRED
    hitl_reasons: List[HITLTriggerReason] = Field(default_factory=list)

    memory_similar_problems: List[Dict[str, Any]] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── HITL Schemas ──


class HITLReviewRequest(BaseModel):
    """Request to review a HITL item."""
    session_id: str
    action: str  # "approve", "reject", "correct"
    corrected_text: Optional[str] = None
    corrected_answer: Optional[str] = None
    feedback: Optional[str] = None


class HITLReviewResponse(BaseModel):
    """Response after HITL review."""
    session_id: str
    status: HITLStatus
    message: str = ""
    updated_response: Optional[SolveResponse] = None


class HITLPendingItem(BaseModel):
    """An item pending HITL review."""
    session_id: str
    reasons: List[HITLTriggerReason]
    extracted_text: str
    parsed_problem: Optional[ParsedProblem] = None
    solution: Optional[SolverResult] = None
    verification: Optional[VerificationResult] = None
    created_at: datetime


# ── Memory Schemas ──


class MemoryEntry(BaseModel):
    """A stored memory record of a solved problem."""
    session_id: str
    input_mode: InputMode
    original_input: str = ""
    parsed_problem_text: str = ""
    topic: MathTopic = MathTopic.ALGEBRA
    retrieved_context_summary: str = ""
    final_answer: str = ""
    solution_steps: List[str] = Field(default_factory=list)
    explanation_summary: str = ""
    verification_confidence: float = 0.0
    is_correct: bool = True
    user_feedback: Optional[str] = None
    user_feedback_correct: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackRequest(BaseModel):
    """User feedback on a solved problem."""
    session_id: str
    is_correct: bool
    comment: Optional[str] = None
