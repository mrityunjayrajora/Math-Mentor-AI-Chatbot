"""
Intent Router Agent - Classifies problem type and determines solving strategy.
"""

import json
import time
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.models.schemas import AgentTraceEntry, ParsedProblem, RoutingResult
from app.models.enums import MathTopic, SolvingStrategy
from app.utils.logger import get_logger

logger = get_logger(__name__)


class IntentRouterAgent:
    """
    Classifies the math problem type, determines solving strategy,
    and identifies required tools and retrieval queries.
    """

    def __init__(self):
        settings = get_settings()
        self._llm = ChatGoogleGenerativeAI(
            model=settings.llm["model"],
            temperature=settings.llm.get("temperature", 0.1),
            max_output_tokens=settings.llm.get("max_tokens", 2048),
            google_api_key=settings.google_api_key,
        )
        self._system_prompt = settings.agents["intent_router"]["system_prompt"]

    def run(self, parsed_problem: ParsedProblem) -> tuple[RoutingResult, AgentTraceEntry]:
        """
        Route a parsed problem to the appropriate solving strategy.

        Args:
            parsed_problem: The structured math problem from the Parser Agent.

        Returns:
            Tuple of (RoutingResult, AgentTraceEntry).
        """
        start_time = time.time()

        try:
            user_msg = (
                f"Problem: {parsed_problem.problem_text}\n"
                f"Initial topic classification: {parsed_problem.topic.value}\n"
                f"Variables: {parsed_problem.variables}\n"
                f"Constraints: {parsed_problem.constraints}\n\n"
                "Analyze this problem and return ONLY a valid JSON object with: "
                "topic, sub_type, strategy, required_tools, retrieval_queries.\n\n"
                "Available tools: solve_equation, solve_system_of_equations, "
                "differentiate, integrate, compute_limit, matrix_operations, "
                "probability_calculator, simplify_expression, evaluate_expression."
            )

            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=user_msg),
            ]

            response = self._llm.invoke(messages)
            content = response.content.strip()
            parsed = self._extract_json(content)

            # Map to enums
            topic_str = parsed.get("topic", parsed_problem.topic.value).lower()
            topic_map = {
                "algebra": MathTopic.ALGEBRA,
                "probability": MathTopic.PROBABILITY,
                "calculus": MathTopic.CALCULUS,
                "linear_algebra": MathTopic.LINEAR_ALGEBRA,
            }
            topic = topic_map.get(topic_str, parsed_problem.topic)

            strategy_str = parsed.get("strategy", "analytical").lower()
            strategy_map = {
                "analytical": SolvingStrategy.ANALYTICAL,
                "numerical": SolvingStrategy.NUMERICAL,
                "hybrid": SolvingStrategy.HYBRID,
            }
            strategy = strategy_map.get(strategy_str, SolvingStrategy.ANALYTICAL)

            result = RoutingResult(
                topic=topic,
                sub_type=parsed.get("sub_type", ""),
                strategy=strategy,
                required_tools=parsed.get("required_tools", []),
                retrieval_queries=parsed.get("retrieval_queries", []),
            )

            duration = (time.time() - start_time) * 1000
            trace = AgentTraceEntry(
                agent_name="Intent Router Agent",
                action=f"Classified as {topic.value}/{result.sub_type}, strategy: {strategy.value}",
                duration_ms=duration,
                success=True,
                details={
                    "topic": topic.value,
                    "sub_type": result.sub_type,
                    "strategy": strategy.value,
                    "tools": result.required_tools,
                    "queries": result.retrieval_queries,
                },
            )

            logger.info(
                "intent_router_complete",
                topic=topic.value,
                sub_type=result.sub_type,
                strategy=strategy.value,
                duration_ms=duration,
            )

            return result, trace

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error("intent_router_failed", error=str(e))

            # Fallback routing
            result = RoutingResult(
                topic=parsed_problem.topic,
                sub_type="general",
                strategy=SolvingStrategy.ANALYTICAL,
                required_tools=["solve_equation", "simplify_expression"],
                retrieval_queries=[parsed_problem.problem_text[:200]],
            )

            trace = AgentTraceEntry(
                agent_name="Intent Router Agent",
                action=f"Failed, using fallback routing: {str(e)}",
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
