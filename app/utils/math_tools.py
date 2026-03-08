"""
Math tools for the Solver Agent.
Wraps SymPy, NumPy, and SciPy functions as LangChain tools.
"""

import json
from typing import Any, Dict, List, Optional

import numpy as np
import sympy as sp
from langchain_core.tools import tool

from app.utils.logger import get_logger

logger = get_logger(__name__)


@tool
def solve_equation(equation: str, variable: str = "x") -> str:
    """
    Solve an algebraic equation using SymPy.

    Args:
        equation: The equation as a string (e.g., 'x**2 - 5*x + 6' for x^2 - 5x + 6 = 0).
        variable: The variable to solve for (default: 'x').

    Returns:
        JSON string with the solutions.
    """
    try:
        var = sp.Symbol(variable)
        expr = sp.sympify(equation)
        solutions = sp.solve(expr, var)
        result = {
            "solutions": [str(s) for s in solutions],
            "count": len(solutions),
            "equation": str(equation),
        }
        logger.info("solve_equation", equation=equation, solutions=result["solutions"])
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def solve_system_of_equations(equations: str, variables: str) -> str:
    """
    Solve a system of equations.

    Args:
        equations: Comma-separated equations (e.g., 'x + y - 3, 2*x - y - 0').
        variables: Comma-separated variable names (e.g., 'x, y').

    Returns:
        JSON string with the solutions.
    """
    try:
        var_names = [v.strip() for v in variables.split(",")]
        vars_sym = sp.symbols(var_names)
        eq_strs = [e.strip() for e in equations.split(",")]
        eqs = [sp.sympify(e) for e in eq_strs]
        solutions = sp.solve(eqs, vars_sym)
        result = {"solutions": str(solutions)}
        logger.info("solve_system", equations=eq_strs, solutions=result["solutions"])
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def differentiate(expression: str, variable: str = "x", order: int = 1) -> str:
    """
    Compute the derivative of an expression.

    Args:
        expression: Mathematical expression as a string.
        variable: Variable to differentiate with respect to.
        order: Order of differentiation (default: 1).

    Returns:
        JSON string with the derivative.
    """
    try:
        var = sp.Symbol(variable)
        expr = sp.sympify(expression)
        derivative = sp.diff(expr, var, order)
        result = {
            "expression": str(expression),
            "derivative": str(derivative),
            "simplified": str(sp.simplify(derivative)),
            "order": order,
        }
        logger.info("differentiate", expression=expression, result=result["derivative"])
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def integrate(expression: str, variable: str = "x",
              lower_bound: str = None, upper_bound: str = None) -> str:
    """
    Compute the integral of an expression (definite or indefinite).

    Args:
        expression: Mathematical expression as a string.
        variable: Variable of integration.
        lower_bound: Lower bound for definite integral (optional).
        upper_bound: Upper bound for definite integral (optional).

    Returns:
        JSON string with the integral.
    """
    try:
        var = sp.Symbol(variable)
        expr = sp.sympify(expression)

        if lower_bound is not None and upper_bound is not None:
            lb = sp.sympify(lower_bound)
            ub = sp.sympify(upper_bound)
            integral = sp.integrate(expr, (var, lb, ub))
            result = {
                "type": "definite",
                "integral": str(integral),
                "simplified": str(sp.simplify(integral)),
            }
        else:
            integral = sp.integrate(expr, var)
            result = {
                "type": "indefinite",
                "integral": str(integral) + " + C",
                "simplified": str(sp.simplify(integral)) + " + C",
            }

        logger.info("integrate", expression=expression, result=result["integral"])
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def compute_limit(expression: str, variable: str = "x", point: str = "0",
                   direction: str = "") -> str:
    """
    Compute the limit of an expression.

    Args:
        expression: Mathematical expression as a string.
        variable: Variable approaching the point.
        point: The point to approach (can be 'oo' for infinity).
        direction: '+' for right, '-' for left, '' for both sides.

    Returns:
        JSON string with the limit.
    """
    try:
        var = sp.Symbol(variable)
        expr = sp.sympify(expression)
        pt = sp.sympify(point)

        if direction:
            limit_val = sp.limit(expr, var, pt, direction)
        else:
            limit_val = sp.limit(expr, var, pt)

        result = {
            "expression": str(expression),
            "limit": str(limit_val),
            "point": str(point),
            "direction": direction or "both",
        }
        logger.info("compute_limit", expression=expression, result=result["limit"])
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def matrix_operations(matrix_str: str, operation: str,
                      matrix_b_str: str = None) -> str:
    """
    Perform matrix operations using NumPy.

    Args:
        matrix_str: Matrix as a nested list string, e.g., '[[1,2],[3,4]]'.
        operation: One of 'determinant', 'inverse', 'eigenvalues',
                   'transpose', 'rank', 'multiply', 'add'.
        matrix_b_str: Second matrix for binary operations (multiply, add).

    Returns:
        JSON string with the result.
    """
    try:
        matrix_a = np.array(json.loads(matrix_str), dtype=float)

        if operation == "determinant":
            det = np.linalg.det(matrix_a)
            result = {"determinant": float(det)}

        elif operation == "inverse":
            inv = np.linalg.inv(matrix_a)
            result = {"inverse": inv.tolist()}

        elif operation == "eigenvalues":
            eigenvalues, eigenvectors = np.linalg.eig(matrix_a)
            result = {
                "eigenvalues": eigenvalues.tolist(),
                "eigenvectors": eigenvectors.tolist(),
            }

        elif operation == "transpose":
            result = {"transpose": matrix_a.T.tolist()}

        elif operation == "rank":
            result = {"rank": int(np.linalg.matrix_rank(matrix_a))}

        elif operation in ("multiply", "add"):
            if matrix_b_str is None:
                return json.dumps({"error": f"Second matrix required for {operation}"})
            matrix_b = np.array(json.loads(matrix_b_str), dtype=float)
            if operation == "multiply":
                res = matrix_a @ matrix_b
            else:
                res = matrix_a + matrix_b
            result = {"result": res.tolist()}

        else:
            return json.dumps({"error": f"Unknown operation: {operation}"})

        logger.info("matrix_operation", operation=operation)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def probability_calculator(operation: str, n: int = 0, r: int = 0,
                          p: float = 0.0, values: str = None) -> str:
    """
    Calculate probability values.

    Args:
        operation: One of 'combination', 'permutation', 'binomial_prob',
                   'expected_value', 'bayes'.
        n: Total number of items.
        r: Number of chosen items.
        p: Probability of success (for binomial).
        values: JSON string of additional values (for Bayes/expected value).

    Returns:
        JSON string with the result.
    """
    try:
        import math

        if operation == "combination":
            result = {"nCr": math.comb(n, r), "n": n, "r": r}

        elif operation == "permutation":
            result = {"nPr": math.perm(n, r), "n": n, "r": r}

        elif operation == "binomial_prob":
            # P(X = r) = C(n, r) * p^r * (1-p)^(n-r)
            prob = math.comb(n, r) * (p ** r) * ((1 - p) ** (n - r))
            result = {"probability": prob, "n": n, "r": r, "p": p}

        elif operation == "expected_value":
            if values:
                vals = json.loads(values)
                # vals should be {"values": [...], "probabilities": [...]}
                v = vals["values"]
                probs = vals["probabilities"]
                ev = sum(x * px for x, px in zip(v, probs))
                result = {"expected_value": ev}
            else:
                result = {"error": "values parameter required for expected_value"}

        elif operation == "bayes":
            if values:
                vals = json.loads(values)
                # P(A|B) = P(B|A) * P(A) / P(B)
                p_b_given_a = vals["p_b_given_a"]
                p_a = vals["p_a"]
                p_b = vals["p_b"]
                p_a_given_b = (p_b_given_a * p_a) / p_b
                result = {"p_a_given_b": p_a_given_b}
            else:
                result = {"error": "values parameter required for bayes"}

        else:
            result = {"error": f"Unknown operation: {operation}"}

        logger.info("probability_calc", operation=operation)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def simplify_expression(expression: str) -> str:
    """
    Simplify a mathematical expression using SymPy.

    Args:
        expression: Mathematical expression as a string.

    Returns:
        JSON string with the simplified expression.
    """
    try:
        expr = sp.sympify(expression)
        simplified = sp.simplify(expr)
        expanded = sp.expand(expr)
        factored = sp.factor(expr)
        result = {
            "original": str(expression),
            "simplified": str(simplified),
            "expanded": str(expanded),
            "factored": str(factored),
        }
        logger.info("simplify", expression=expression, simplified=result["simplified"])
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def evaluate_expression(expression: str, substitutions: str = None) -> str:
    """
    Evaluate a mathematical expression, optionally with variable substitutions.

    Args:
        expression: Mathematical expression as a string.
        substitutions: JSON string of variable substitutions, e.g., '{"x": 2, "y": 3}'.

    Returns:
        JSON string with the evaluated result.
    """
    try:
        expr = sp.sympify(expression)

        if substitutions:
            subs = json.loads(substitutions)
            subs_sym = {sp.Symbol(k): v for k, v in subs.items()}
            result_val = expr.subs(subs_sym)
        else:
            result_val = expr

        # Try to evaluate to a number
        try:
            numerical = float(result_val.evalf())
            result = {
                "symbolic": str(result_val),
                "numerical": numerical,
            }
        except (TypeError, AttributeError):
            result = {"symbolic": str(result_val)}

        logger.info("evaluate", expression=expression, result=result)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_all_math_tools() -> list:
    """Return all math tools as a list for the Solver Agent."""
    return [
        solve_equation,
        solve_system_of_equations,
        differentiate,
        integrate,
        compute_limit,
        matrix_operations,
        probability_calculator,
        simplify_expression,
        evaluate_expression,
    ]
