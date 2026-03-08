"""
Verifier / Critic Agent - Checks correctness of the solution.
"""

import json
import time
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.models.schemas import (
    AgentTraceEntry,
    ParsedProblem,
    SolverResult,
    VerificationResult,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VerifierAgent:
    """
    Checks the correctness of solutions by:
    - Verifying logical consistency of steps
    - Substitution checking
    - Boundary condition analysis
    - Domain and unit validation
    """

    def __init__(self):
        settings = get_settings()
        self._llm = ChatGoogleGenerativeAI(
            model=settings.llm["model"],
            temperature=settings.llm.get("temperature", 0.1),
            max_output_tokens=settings.llm.get("max_tokens", 4096),
            google_api_key=settings.google_api_key,
        )
        self._system_prompt = settings.agents["verifier"]["system_prompt"]
        self._confidence_threshold = settings.agents["verifier"].get(
            "confidence_threshold", 0.7
        )

    def run(
        self,
        parsed_problem: ParsedProblem,
        solution: SolverResult,
    ) -> tuple[VerificationResult, AgentTraceEntry]:
        """
        Verify the correctness of a solution.

        Args:
            parsed_problem: The original structured problem.
            solution: The solver's output.

        Returns:
            Tuple of (VerificationResult, AgentTraceEntry).
        """
        start_time = time.time()

        try:
            # Build the steps summary
            steps_str = "\n".join(
                f"  Step {s.step_number}: {s.description}"
                + (f" → {s.result}" if s.result else "")
                for s in solution.steps
            )

            user_msg = (
                f"Original Problem: {parsed_problem.problem_text}\n\n"
                f"Variables: {parsed_problem.variables}\n"
                f"Constraints: {parsed_problem.constraints}\n\n"
                f"Solution Steps:\n{steps_str}\n\n"
                f"Final Answer: {solution.final_answer}\n\n"
                "Verify this solution thoroughly. Perform at least one independent "
                "check (substitution, alternative method, boundary check).\n\n"
                "Return ONLY a valid JSON object with:\n"
                '- "is_correct": boolean\n'
                '- "confidence": float between 0 and 1\n'
                '- "issues": list of issues found (empty list if correct)\n'
                '- "verification_method": description of how you verified\n'
                '- "suggestions": list of improvement suggestions'
            )

            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=user_msg),
            ]

            response = self._llm.invoke(messages)
            content = response.content.strip()
            parsed = self._extract_json(content)

            result = VerificationResult(
                is_correct=parsed.get("is_correct", True),
                confidence=float(parsed.get("confidence", 0.5)),
                issues=parsed.get("issues", []),
                verification_method=parsed.get("verification_method", ""),
                suggestions=parsed.get("suggestions", []),
            )

            duration = (time.time() - start_time) * 1000
            trace = AgentTraceEntry(
                agent_name="Verifier Agent",
                action=f"Verified: {'correct' if result.is_correct else 'incorrect'}, "
                       f"confidence: {result.confidence:.2f}",
                duration_ms=duration,
                success=True,
                details={
                    "is_correct": result.is_correct,
                    "confidence": result.confidence,
                    "issue_count": len(result.issues),
                    "hitl_triggered": result.confidence < self._confidence_threshold,
                },
            )

            logger.info(
                "verifier_agent_complete",
                is_correct=result.is_correct,
                confidence=result.confidence,
                issue_count=len(result.issues),
                duration_ms=duration,
            )

            return result, trace

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error("verifier_agent_failed", error=str(e))

            result = VerificationResult(
                is_correct=False,
                confidence=0.0,
                issues=[f"Verification failed: {str(e)}"],
                verification_method="failed",
                suggestions=["Manual verification recommended"],
            )

            trace = AgentTraceEntry(
                agent_name="Verifier Agent",
                action=f"Failed: {str(e)}",
                duration_ms=duration,
                success=False,
                details={"error": str(e)},
            )

            return result, trace

    @property
    def confidence_threshold(self) -> float:
        return self._confidence_threshold

    def _extract_json(self, content: str) -> dict:
        """Extract JSON object from LLM response."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        if "```" in content:
            start = content.find("```json")
            if start != -1:
                start = content.find("\n", start) + 1
            else:
                start = content.find("```") + 3
                start = content.find("\n", start) + 1
            end = content.find("```", start)
            if end != -1:
                try:
                    return json.loads(content[start:end].strip())
                except json.JSONDecodeError:
                    pass

        brace_start = content.find("{")
        brace_end = content.rfind("}") + 1
        if brace_start != -1 and brace_end > brace_start:
            try:
                return json.loads(content[brace_start:brace_end])
            except json.JSONDecodeError:
                pass

        return {"is_correct": False, "confidence": 0.0, "issues": ["Failed to parse verification"]}
