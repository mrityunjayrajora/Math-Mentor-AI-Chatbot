"""
Parser Agent - Converts raw OCR/ASR/text input into a structured math problem.
"""

import json
import time
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.models.schemas import AgentTraceEntry, ParsedProblem
from app.models.enums import MathTopic
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ParserAgent:
    """
    Cleans OCR/ASR output, identifies ambiguities, and produces
    a structured ParsedProblem.
    """

    def __init__(self):
        settings = get_settings()
        self._llm = ChatGoogleGenerativeAI(
            model=settings.llm["model"],
            temperature=settings.llm.get("temperature", 0.2),
            max_output_tokens=settings.llm.get("max_tokens", 4096),
            google_api_key=settings.google_api_key,
        )
        self._system_prompt = settings.agents["parser"]["system_prompt"]

    def run(
        self, raw_text: str, input_mode: str = "text",
        ocr_corrections: Optional[list] = None
    ) -> tuple[ParsedProblem, AgentTraceEntry]:
        """
        Parse raw text into a structured math problem.

        Args:
            raw_text: Raw text from OCR/ASR/user input.
            input_mode: The input modality used.
            ocr_corrections: Known OCR corrections from memory (optional).

        Returns:
            Tuple of (ParsedProblem, AgentTraceEntry).
        """
        start_time = time.time()

        try:
            # Build the user message
            user_msg = f"Input mode: {input_mode}\n\nRaw text:\n{raw_text}"

            if ocr_corrections:
                corrections_str = "\n".join(
                    f"  - '{c['original']}' → '{c['corrected']}'"
                    for c in ocr_corrections
                )
                user_msg += (
                    f"\n\nKnown corrections from past experience:\n{corrections_str}"
                    "\nApply these corrections if the same patterns appear."
                )

            user_msg += (
                "\n\nParse this into a structured math problem. "
                "If the input contains MULTIPLE separate math problems or questions, "
                "list each one in a 'detected_problems' array. "
                "If there is only ONE problem, leave 'detected_problems' as an empty array. "
                "When multiple problems are detected, set 'needs_clarification' to true "
                "and 'clarification_reason' to 'Multiple problems detected. Which would you like to solve?'. "
                "Return ONLY a valid JSON object with the fields: "
                "problem_text, topic, variables, constraints, "
                "detected_problems, needs_clarification, clarification_reason."
            )

            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=user_msg),
            ]

            response = self._llm.invoke(messages)
            content = response.content.strip()

            # Extract JSON from the response
            parsed = self._extract_json(content)

            # Map topic string to enum
            topic_str = parsed.get("topic", "algebra").lower()
            topic_map = {
                "algebra": MathTopic.ALGEBRA,
                "probability": MathTopic.PROBABILITY,
                "calculus": MathTopic.CALCULUS,
                "linear_algebra": MathTopic.LINEAR_ALGEBRA,
            }
            topic = topic_map.get(topic_str, MathTopic.ALGEBRA)

            detected_problems = parsed.get("detected_problems", [])
            needs_clarification = parsed.get("needs_clarification", False)
            clarification_reason = parsed.get("clarification_reason")

            # Force clarification when multiple problems detected
            if len(detected_problems) > 1 and not needs_clarification:
                needs_clarification = True
                clarification_reason = "Multiple problems detected. Which would you like to solve?"

            result = ParsedProblem(
                problem_text=parsed.get("problem_text", raw_text),
                topic=topic,
                variables=parsed.get("variables", []),
                constraints=parsed.get("constraints", []),
                detected_problems=detected_problems,
                needs_clarification=needs_clarification,
                clarification_reason=clarification_reason,
            )

            duration = (time.time() - start_time) * 1000
            trace = AgentTraceEntry(
                agent_name="Parser Agent",
                action="Parsed raw text into structured problem",
                duration_ms=duration,
                success=True,
                details={
                    "topic": result.topic.value,
                    "needs_clarification": result.needs_clarification,
                    "variable_count": len(result.variables),
                },
            )

            logger.info(
                "parser_agent_complete",
                topic=result.topic.value,
                needs_clarification=result.needs_clarification,
                duration_ms=duration,
            )

            return result, trace

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error("parser_agent_failed", error=str(e))

            # Fallback: return raw text as-is
            result = ParsedProblem(
                problem_text=raw_text,
                needs_clarification=True,
                clarification_reason=f"Parser failed: {str(e)}",
            )

            trace = AgentTraceEntry(
                agent_name="Parser Agent",
                action=f"Failed: {str(e)}",
                duration_ms=duration,
                success=False,
                details={"error": str(e)},
            )

            return result, trace

    def _extract_json(self, content: str) -> dict:
        """Extract JSON object from LLM response, handling markdown code blocks."""
        # Try direct JSON parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        if "```" in content:
            # Find JSON block
            start = content.find("```json")
            if start != -1:
                start = content.find("\n", start) + 1
            else:
                start = content.find("```") + 3
                start = content.find("\n", start) + 1

            end = content.find("```", start)
            if end != -1:
                json_str = content[start:end].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

        # Try finding JSON object in the text
        brace_start = content.find("{")
        brace_end = content.rfind("}") + 1
        if brace_start != -1 and brace_end > brace_start:
            try:
                return json.loads(content[brace_start:brace_end])
            except json.JSONDecodeError:
                pass

        logger.warning("parser_json_extraction_failed", content=content[:200])
        return {"problem_text": content, "topic": "algebra"}
