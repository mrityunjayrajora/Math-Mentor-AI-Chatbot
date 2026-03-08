"""
Solver Agent - Solves math problems using RAG context and Python math tools.
"""

import json
import time
from typing import List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.models.schemas import (
    AgentTraceEntry,
    ParsedProblem,
    RetrievedChunk,
    RoutingResult,
    SolutionStep,
    SolverResult,
)
from app.utils.logger import get_logger
from app.utils.math_tools import get_all_math_tools

logger = get_logger(__name__)


class SolverAgent:
    """
    Solves math problems step-by-step using RAG context + Python math tools.
    Uses LangChain tools for SymPy/NumPy computations.
    """

    def __init__(self):
        settings = get_settings()
        self._llm = ChatGoogleGenerativeAI(
            model=settings.llm["model"],
            temperature=settings.llm.get("temperature", 0.2),
            max_output_tokens=settings.llm.get("max_tokens", 4096),
            google_api_key=settings.google_api_key,
        )
        self._system_prompt = settings.agents["solver"]["system_prompt"]
        self._enable_tools = settings.agents["solver"].get("enable_python_tools", True)
        self._math_tools = get_all_math_tools() if self._enable_tools else []

    def run(
        self,
        parsed_problem: ParsedProblem,
        routing: RoutingResult,
        retrieved_context: List[RetrievedChunk],
        similar_solutions: Optional[List[dict]] = None,
    ) -> tuple[SolverResult, AgentTraceEntry]:
        """
        Solve the math problem.

        Args:
            parsed_problem: Structured problem from parser.
            routing: Routing decision from intent router.
            retrieved_context: Chunks from RAG knowledge base.
            similar_solutions: Past similar solved problems from memory.

        Returns:
            Tuple of (SolverResult, AgentTraceEntry).
        """
        start_time = time.time()

        try:
            # Build context string from retrieved chunks
            context_str = ""
            if retrieved_context:
                context_str = "\n\n--- Retrieved Knowledge Base Context ---\n"
                for i, chunk in enumerate(retrieved_context, 1):
                    context_str += (
                        f"\n[SOURCE: {chunk.source}] (relevance: {chunk.relevance_score:.2f})\n"
                        f"{chunk.content}\n"
                    )

            # Build similar solutions string
            similar_str = ""
            if similar_solutions:
                similar_str = "\n\n--- Similar Past Solutions from Memory ---\n"
                for i, sol in enumerate(similar_solutions, 1):
                    similar_str += (
                        f"\nPast Problem {i}: {sol.get('problem_text', 'N/A')}\n"
                        f"Past Answer: {sol.get('final_answer', 'N/A')}\n"
                        f"Past Steps: {sol.get('solution_steps', [])}\n"
                        f"Was Correct: {sol.get('is_correct', 'N/A')}\n"
                    )

            # Build available tools description
            tools_str = ""
            if self._math_tools:
                tools_str = "\n\n--- Available Math Tools ---\n"
                for tool in self._math_tools:
                    tools_str += f"- {tool.name}: {tool.description}\n"

            user_msg = (
                f"Problem: {parsed_problem.problem_text}\n"
                f"Topic: {routing.topic.value} / {routing.sub_type}\n"
                f"Strategy: {routing.strategy.value}\n"
                f"Variables: {parsed_problem.variables}\n"
                f"Constraints: {parsed_problem.constraints}\n"
                f"{context_str}"
                f"{similar_str}"
                f"{tools_str}\n\n"
                "Solve this problem step by step. For each step, show the mathematical "
                "operation and its result. Use tools where appropriate by describing "
                "which tool you would call and with what arguments.\n\n"
                "Return ONLY a valid JSON object with:\n"
                '- "steps": list of objects with "step_number", "description", "result"\n'
                '- "final_answer": the final answer as a string\n'
                '- "tools_used": list of tool names used\n'
                '- "sources_cited": list of source filenames referenced '
                "(only cite sources actually retrieved above)"
            )

            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=user_msg),
            ]

            # If tools are enabled, also try using them via LLM
            # For now, we let the LLM describe tool usage in its response
            # and we can optionally execute tools separately
            response = self._llm.invoke(messages)
            content = response.content.strip()
            parsed = self._extract_json(content)

            # Build solution steps
            steps = []
            raw_steps = parsed.get("steps", [])
            for i, step in enumerate(raw_steps):
                if isinstance(step, dict):
                    steps.append(SolutionStep(
                        step_number=step.get("step_number", i + 1),
                        description=step.get("description", ""),
                        result=step.get("result", ""),
                    ))
                elif isinstance(step, str):
                    steps.append(SolutionStep(
                        step_number=i + 1,
                        description=step,
                        result="",
                    ))

            # Execute math tools if referenced in the solution
            tools_used = parsed.get("tools_used", [])
            executed_tools = []
            if self._enable_tools and tools_used:
                executed_tools = self._execute_referenced_tools(
                    parsed_problem, tools_used
                )

            result = SolverResult(
                steps=steps,
                final_answer=parsed.get("final_answer", ""),
                tools_used=tools_used + [t["tool"] for t in executed_tools],
                sources_cited=parsed.get("sources_cited", []),
            )

            duration = (time.time() - start_time) * 1000
            trace = AgentTraceEntry(
                agent_name="Solver Agent",
                action=f"Solved problem with {len(steps)} steps",
                duration_ms=duration,
                success=True,
                details={
                    "step_count": len(steps),
                    "tools_used": result.tools_used,
                    "sources_cited": result.sources_cited,
                    "final_answer": result.final_answer[:200],
                    "executed_tools": executed_tools,
                },
            )

            logger.info(
                "solver_agent_complete",
                step_count=len(steps),
                tools_used=result.tools_used,
                duration_ms=duration,
            )

            return result, trace

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error("solver_agent_failed", error=str(e))

            result = SolverResult(
                steps=[SolutionStep(
                    step_number=1,
                    description=f"Error during solving: {str(e)}",
                    result="",
                )],
                final_answer="Unable to solve. Please try rephrasing the problem.",
            )

            trace = AgentTraceEntry(
                agent_name="Solver Agent",
                action=f"Failed: {str(e)}",
                duration_ms=duration,
                success=False,
                details={"error": str(e)},
            )

            return result, trace

    def _execute_referenced_tools(
        self, problem: ParsedProblem, tool_names: List[str]
    ) -> List[dict]:
        """
        Try to execute referenced math tools for verification.
        This is a best-effort attempt to validate tool usage.
        """
        results = []
        tool_map = {t.name: t for t in self._math_tools}

        for tool_name in tool_names:
            if tool_name in tool_map:
                try:
                    # Basic auto-execution for common patterns
                    if tool_name == "solve_equation" and problem.variables:
                        result = tool_map[tool_name].invoke({
                            "equation": problem.problem_text,
                            "variable": problem.variables[0],
                        })
                        results.append({
                            "tool": tool_name,
                            "result": result,
                            "success": True,
                        })
                except Exception as e:
                    results.append({
                        "tool": tool_name,
                        "error": str(e),
                        "success": False,
                    })

        return results

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

        return {"steps": [], "final_answer": content[:500]}
