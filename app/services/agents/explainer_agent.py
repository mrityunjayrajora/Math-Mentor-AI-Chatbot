"""
Explainer / Tutor Agent - Produces student-friendly step-by-step explanations.
"""

import json
import time

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.models.schemas import (
    AgentTraceEntry,
    ExplanationResult,
    ParsedProblem,
    SolverResult,
    VerificationResult,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ExplainerAgent:
    """
    Produces clear, student-friendly explanations of math solutions.
    Includes step-by-step reasoning, key concepts, and common pitfalls.
    """

    def __init__(self):
        settings = get_settings()
        self._llm = ChatGoogleGenerativeAI(
            model=settings.llm["model"],
            temperature=settings.llm.get("temperature", 0.3),
            max_output_tokens=settings.llm.get("max_tokens", 4096),
            google_api_key=settings.google_api_key,
        )
        self._system_prompt = settings.agents["explainer"]["system_prompt"]

    def run(
        self,
        parsed_problem: ParsedProblem,
        solution: SolverResult,
        verification: VerificationResult,
    ) -> tuple[ExplanationResult, AgentTraceEntry]:
        """
        Generate a student-friendly explanation of the solution.

        Args:
            parsed_problem: The structured problem.
            solution: The solver's output.
            verification: The verification result.

        Returns:
            Tuple of (ExplanationResult, AgentTraceEntry).
        """
        start_time = time.time()

        try:
            steps_str = "\n".join(
                f"  Step {s.step_number}: {s.description}"
                + (f" → {s.result}" if s.result else "")
                for s in solution.steps
            )

            verification_str = (
                f"Verification: {'Correct' if verification.is_correct else 'Has issues'}\n"
                f"Confidence: {verification.confidence:.2f}\n"
            )
            if verification.issues:
                verification_str += f"Issues: {', '.join(verification.issues)}\n"

            user_msg = (
                f"Problem: {parsed_problem.problem_text}\n"
                f"Topic: {parsed_problem.topic.value}\n\n"
                f"Solution Steps:\n{steps_str}\n\n"
                f"Final Answer: {solution.final_answer}\n\n"
                f"{verification_str}\n"
                "You are a friendly tutor explaining this to a young student. "
                "Your MOST IMPORTANT job is the 'detailed_steps' — explain the solution "
                "step-by-step in very simple language, as if teaching a 10-year-old. "
                "Each step should:\n"
                "  - Start with what we're doing and WHY\n"
                "  - Show the math operation clearly\n"
                "  - Explain the result in plain English\n"
                "  - Use encouraging, friendly language\n\n"
                "Return ONLY a valid JSON object with:\n"
                '- "summary": 1-2 sentence overview of what we solved and how (simple language)\n'
                '- "detailed_steps": list of strings, each being a clear step-by-step explanation '
                '(this is the MOST IMPORTANT part — make each step crystal clear)\n'
                '- "key_concepts": list of the formulas or math concepts used\n'
                '- "common_mistakes": 1-2 common mistakes students make on this type of problem\n'
                '- "tips": 1-2 short practical tips for similar problems'
            )

            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=user_msg),
            ]

            response = self._llm.invoke(messages)
            content = response.content.strip()
            parsed = self._extract_json(content)

            result = ExplanationResult(
                summary=parsed.get("summary", ""),
                detailed_steps=parsed.get("detailed_steps", []),
                key_concepts=parsed.get("key_concepts", []),
                common_mistakes=parsed.get("common_mistakes", []),
                tips=parsed.get("tips", []),
            )

            duration = (time.time() - start_time) * 1000
            trace = AgentTraceEntry(
                agent_name="Explainer Agent",
                action=f"Generated explanation with {len(result.detailed_steps)} steps",
                duration_ms=duration,
                success=True,
                details={
                    "step_count": len(result.detailed_steps),
                    "concept_count": len(result.key_concepts),
                },
            )

            logger.info(
                "explainer_agent_complete",
                step_count=len(result.detailed_steps),
                duration_ms=duration,
            )

            return result, trace

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error("explainer_agent_failed", error=str(e))

            result = ExplanationResult(
                summary=f"Solution: {solution.final_answer}",
                detailed_steps=[s.description for s in solution.steps],
            )

            trace = AgentTraceEntry(
                agent_name="Explainer Agent",
                action=f"Failed: {str(e)}",
                duration_ms=duration,
                success=False,
                details={"error": str(e)},
            )

            return result, trace

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

        return {}
