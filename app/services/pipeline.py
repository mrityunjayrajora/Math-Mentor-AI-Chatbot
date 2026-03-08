"""
Pipeline Orchestrator - Orchestrates the full math solving pipeline.
Input → Parse → Route → Retrieve → Solve → Verify → Explain → Store
"""

import time
from typing import List, Optional
from uuid import uuid4

from app.config import get_settings
from app.models.enums import HITLStatus, HITLTriggerReason, InputMode
from app.models.schemas import (
    AgentTraceEntry,
    ExtractionResult,
    MemoryEntry,
    RetrievedChunk,
    SolveRequest,
    SolveResponse,
)
from app.services.agents.explainer_agent import ExplainerAgent
from app.services.agents.intent_router_agent import IntentRouterAgent
from app.services.agents.parser_agent import ParserAgent
from app.services.agents.solver_agent import SolverAgent
from app.services.agents.verifier_agent import VerifierAgent
from app.services.hitl.hitl_manager import HITLManager
from app.services.input_handlers.audio_handler import AudioHandler
from app.services.input_handlers.image_handler import ImageHandler
from app.services.input_handlers.text_handler import TextHandler
from app.services.memory.memory_store import MemoryStore
from app.services.rag.retriever import HybridRetriever
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Pipeline:
    """
    Orchestrates the full math solving pipeline:
    1. Extract text from input (image/audio/text)
    2. Check memory for OCR corrections
    3. Parse into structured problem (Parser Agent)
    4. Route to appropriate strategy (Intent Router Agent)
    5. Retrieve relevant context (RAG)
    6. Check memory for similar problems
    7. Solve the problem (Solver Agent)
    8. Verify the solution (Verifier Agent)
    9. Generate explanation (Explainer Agent)
    10. Store in memory
    11. Check for HITL triggers
    """

    def __init__(
        self,
        retriever: HybridRetriever,
        memory_store: MemoryStore,
        hitl_manager: HITLManager,
    ):
        self._retriever = retriever
        self._memory_store = memory_store
        self._hitl_manager = hitl_manager

        # Initialize handlers
        self._image_handler = ImageHandler()
        self._text_handler = TextHandler()
        self._audio_handler = None  # Lazy-load (Whisper is heavy)

        # Initialize agents
        self._parser_agent = ParserAgent()
        self._intent_router_agent = IntentRouterAgent()
        self._solver_agent = SolverAgent()
        self._verifier_agent = VerifierAgent()
        self._explainer_agent = ExplainerAgent()

        self._settings = get_settings()

    def _get_audio_handler(self) -> AudioHandler:
        """Lazy-load the audio handler."""
        if self._audio_handler is None:
            self._audio_handler = AudioHandler()
        return self._audio_handler

    async def solve(self, request: SolveRequest) -> SolveResponse:
        """
        Execute the full solving pipeline.

        Args:
            request: SolveRequest with input mode and data.

        Returns:
            SolveResponse with all pipeline outputs.
        """
        session_id = str(uuid4())
        agent_trace: List[AgentTraceEntry] = []
        hitl_reasons: List[HITLTriggerReason] = []
        pipeline_start = time.time()

        logger.info("pipeline_started", session_id=session_id, input_mode=request.input_mode.value)

        # === Step 1: Extract text from input ===
        extraction = self._extract_input(request)
        agent_trace.append(AgentTraceEntry(
            agent_name="Input Handler",
            action=f"Extracted text via {request.input_mode.value}",
            success=True,
            details={
                "confidence": extraction.confidence,
                "text_length": len(extraction.extracted_text),
            },
        ))

        if extraction.hitl_required and extraction.hitl_reason:
            hitl_reasons.append(extraction.hitl_reason)

        # === Step 2: Check memory for OCR corrections ===
        ocr_corrections = []
        if request.input_mode == InputMode.IMAGE:
            ocr_corrections = self._memory_store.get_ocr_corrections()
            if ocr_corrections:
                agent_trace.append(AgentTraceEntry(
                    agent_name="Memory",
                    action=f"Found {len(ocr_corrections)} OCR corrections from past experience",
                    success=True,
                ))

        # === Step 3: Parse into structured problem ===
        parsed_problem, parse_trace = self._parser_agent.run(
            raw_text=extraction.extracted_text,
            input_mode=request.input_mode.value,
            ocr_corrections=ocr_corrections if ocr_corrections else None,
        )
        agent_trace.append(parse_trace)

        if parsed_problem.needs_clarification:
            hitl_reasons.append(HITLTriggerReason.PARSER_AMBIGUITY)

        # === Step 4: Route to strategy ===
        routing, route_trace = self._intent_router_agent.run(parsed_problem)
        agent_trace.append(route_trace)

        # === Step 5: Retrieve context from RAG ===
        retrieval_start = time.time()
        retrieved_context: List[RetrievedChunk] = self._retriever.retrieve(
            query=parsed_problem.problem_text,
            queries=routing.retrieval_queries,
        )
        retrieval_duration = (time.time() - retrieval_start) * 1000

        agent_trace.append(AgentTraceEntry(
            agent_name="RAG Retriever",
            action=f"Retrieved {len(retrieved_context)} chunks from knowledge base",
            duration_ms=retrieval_duration,
            success=True,
            details={
                "chunk_count": len(retrieved_context),
                "sources": list(set(c.source for c in retrieved_context)),
            },
        ))

        # === Step 6: Check memory for similar problems ===
        similar_problems = self._memory_store.find_similar(parsed_problem.problem_text)
        if similar_problems:
            agent_trace.append(AgentTraceEntry(
                agent_name="Memory",
                action=f"Found {len(similar_problems)} similar past problems",
                success=True,
                details={
                    "top_similarity": similar_problems[0]["similarity"] if similar_problems else 0,
                    "topics": [p.get("topic", "unknown") for p in similar_problems[:3]],
                },
            ))

            # Short-circuit: if top match is very similar, return cached solution
            top_match = similar_problems[0]
            if top_match["similarity"] >= 0.99:
                logger.info(
                    "memory_cache_hit",
                    session_id=session_id,
                    similarity=top_match["similarity"],
                    cached_session=top_match["session_id"],
                )
                agent_trace.append(AgentTraceEntry(
                    agent_name="Memory",
                    action=f"Returning cached solution (similarity: {top_match['similarity']:.0%})",
                    success=True,
                ))

                from app.models.schemas import SolverResult, SolutionStep, VerificationResult, ExplanationResult

                cached_steps = []
                for i, step_desc in enumerate(top_match.get("solution_steps", []), 1):
                    cached_steps.append(SolutionStep(
                        step_number=i,
                        description=str(step_desc),
                        math_expression="",
                        result="",
                    ))

                cached_solution = SolverResult(
                    steps=cached_steps,
                    final_answer=top_match.get("final_answer", ""),
                    tools_used=[],
                    sources_cited=[],
                )

                cached_verification = VerificationResult(
                    is_correct=top_match.get("is_correct", True),
                    confidence=top_match.get("verification_confidence", 0.9),
                    verification_method="memory_cache",
                )

                # Use the originally stored explanation, not a generic message
                stored_explanation = top_match.get("explanation_summary", "")
                cached_explanation = ExplanationResult(
                    summary=stored_explanation if stored_explanation else f"The answer to '{parsed_problem.problem_text}' is {top_match.get('final_answer', '')}.",
                    detailed_steps=[],
                    key_concepts=[],
                    common_mistakes=[],
                    tips=[],
                )

                overall_confidence = self._compute_overall_confidence(
                    extraction.confidence, cached_verification.confidence
                )

                pipeline_duration = (time.time() - pipeline_start) * 1000
                logger.info(
                    "pipeline_complete_from_memory",
                    session_id=session_id,
                    duration_ms=pipeline_duration,
                )

                return SolveResponse(
                    session_id=session_id,
                    input_mode=request.input_mode,
                    extracted_text=extraction.extracted_text,
                    extraction_confidence=extraction.confidence,
                    parsed_problem=parsed_problem,
                    routing=routing,
                    retrieved_context=retrieved_context,
                    solution=cached_solution,
                    verification=cached_verification,
                    explanation=cached_explanation,
                    overall_confidence=overall_confidence,
                    agent_trace=agent_trace,
                    hitl_required=False,
                    hitl_status=HITLStatus.NOT_REQUIRED,
                    hitl_reasons=[],
                    memory_similar_problems=similar_problems,
                )

        # === Step 7: Solve the problem ===
        solution, solve_trace = self._solver_agent.run(
            parsed_problem=parsed_problem,
            routing=routing,
            retrieved_context=retrieved_context,
            similar_solutions=similar_problems if similar_problems else None,
        )
        agent_trace.append(solve_trace)

        # === Step 8: Verify the solution ===
        verification, verify_trace = self._verifier_agent.run(
            parsed_problem=parsed_problem,
            solution=solution,
        )
        agent_trace.append(verify_trace)

        if (
            verification.confidence < self._verifier_agent.confidence_threshold
            or not verification.is_correct
        ):
            hitl_reasons.append(HITLTriggerReason.LOW_VERIFIER_CONFIDENCE)

        # === Step 9: Generate explanation ===
        explanation, explain_trace = self._explainer_agent.run(
            parsed_problem=parsed_problem,
            solution=solution,
            verification=verification,
        )
        agent_trace.append(explain_trace)

        # === Build Response ===
        overall_confidence = self._compute_overall_confidence(
            extraction.confidence, verification.confidence
        )

        hitl_required = len(hitl_reasons) > 0
        hitl_status = HITLStatus.PENDING_REVIEW if hitl_required else HITLStatus.NOT_REQUIRED

        response = SolveResponse(
            session_id=session_id,
            input_mode=request.input_mode,
            extracted_text=extraction.extracted_text,
            extraction_confidence=extraction.confidence,
            parsed_problem=parsed_problem,
            routing=routing,
            retrieved_context=retrieved_context,
            solution=solution,
            verification=verification,
            explanation=explanation,
            overall_confidence=overall_confidence,
            agent_trace=agent_trace,
            hitl_required=hitl_required,
            hitl_status=hitl_status,
            hitl_reasons=hitl_reasons,
            memory_similar_problems=similar_problems,
        )

        # === Step 10: Store in memory ===
        try:
            context_summary = "; ".join(
                f"[{c.source}]: {c.content[:100]}..." for c in retrieved_context[:3]
            )
            memory_entry = MemoryEntry(
                session_id=session_id,
                input_mode=request.input_mode,
                original_input=extraction.extracted_text,
                parsed_problem_text=parsed_problem.problem_text,
                topic=parsed_problem.topic,
                retrieved_context_summary=context_summary,
                final_answer=solution.final_answer,
                solution_steps=[s.description for s in solution.steps],
                explanation_summary=explanation.summary if explanation else "",
                verification_confidence=verification.confidence,
                is_correct=verification.is_correct,
            )
            self._memory_store.store(memory_entry)
            agent_trace.append(AgentTraceEntry(
                agent_name="Memory",
                action="Stored solution in memory for future reference",
                success=True,
            ))
        except Exception as e:
            logger.error("memory_store_failed_in_pipeline", error=str(e))

        # === Step 11: Add to HITL queue if needed ===
        if hitl_required:
            self._hitl_manager.add_to_queue(session_id, hitl_reasons, response)

        pipeline_duration = (time.time() - pipeline_start) * 1000
        logger.info(
            "pipeline_complete",
            session_id=session_id,
            duration_ms=pipeline_duration,
            hitl_required=hitl_required,
            overall_confidence=overall_confidence,
        )

        return response

    def _extract_input(self, request: SolveRequest) -> ExtractionResult:
        """Extract text from the input based on the input mode."""
        if request.input_mode == InputMode.IMAGE:
            if not request.image_base64:
                return ExtractionResult(
                    extracted_text="",
                    confidence=0.0,
                    input_mode=InputMode.IMAGE,
                    hitl_required=True,
                    hitl_reason=HITLTriggerReason.LOW_OCR_CONFIDENCE,
                    raw_details={"error": "No image data provided"},
                )
            return self._image_handler.extract(request.image_base64)

        elif request.input_mode == InputMode.AUDIO:
            if not request.audio_base64:
                return ExtractionResult(
                    extracted_text="",
                    confidence=0.0,
                    input_mode=InputMode.AUDIO,
                    hitl_required=True,
                    hitl_reason=HITLTriggerReason.LOW_ASR_CONFIDENCE,
                    raw_details={"error": "No audio data provided"},
                )
            handler = self._get_audio_handler()
            return handler.extract(
                request.audio_base64,
                request.audio_format or "wav",
            )

        elif request.input_mode == InputMode.TEXT:
            if not request.text:
                return ExtractionResult(
                    extracted_text="",
                    confidence=1.0,
                    input_mode=InputMode.TEXT,
                    raw_details={"error": "No text provided"},
                )
            return self._text_handler.extract(request.text)

        else:
            return ExtractionResult(
                extracted_text="",
                confidence=0.0,
                input_mode=request.input_mode,
                hitl_required=True,
                raw_details={"error": f"Unknown input mode: {request.input_mode}"},
            )

    def _compute_overall_confidence(
        self, extraction_confidence: float, verification_confidence: float
    ) -> float:
        """Compute overall pipeline confidence."""
        # Weighted geometric mean
        if extraction_confidence <= 0 or verification_confidence <= 0:
            return 0.0
        return (extraction_confidence * 0.3 + verification_confidence * 0.7)
