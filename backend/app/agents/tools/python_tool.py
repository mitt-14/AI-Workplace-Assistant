from __future__ import annotations

import ast
import json
import math
import operator
from statistics import mean, median
from typing import Any


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def _safe_number_expression(
    expression: str,
) -> float | int:
    """
    Evaluate arithmetic only.

    No function calls, attributes, imports, indexing, comprehensions,
    file access, or arbitrary Python execution are allowed.
    """

    tree = ast.parse(
        expression,
        mode="eval",
    )

    def evaluate(node: ast.AST):
        if isinstance(
            node,
            ast.Expression,
        ):
            return evaluate(
                node.body
            )

        if isinstance(
            node,
            ast.Constant,
        ) and isinstance(
            node.value,
            (int, float),
        ):
            return node.value

        if isinstance(
            node,
            ast.Name,
        ) and node.id in _CONSTANTS:
            return _CONSTANTS[
                node.id
            ]

        if isinstance(
            node,
            ast.BinOp,
        ) and type(node.op) in _BINARY_OPERATORS:
            left = evaluate(
                node.left
            )
            right = evaluate(
                node.right
            )

            if (
                isinstance(
                    node.op,
                    ast.Pow,
                )
                and abs(right) > 12
            ):
                raise ValueError(
                    "Exponent is too large."
                )

            return _BINARY_OPERATORS[
                type(node.op)
            ](
                left,
                right,
            )

        if isinstance(
            node,
            ast.UnaryOp,
        ) and type(node.op) in _UNARY_OPERATORS:
            return _UNARY_OPERATORS[
                type(node.op)
            ](
                evaluate(
                    node.operand
                )
            )

        raise ValueError(
            "Only basic arithmetic is allowed."
        )

    result = evaluate(
        tree
    )

    if isinstance(
        result,
        complex,
    ):
        raise ValueError(
            "Complex-number results are not supported."
        )

    return result


async def run_python_utility(
    *,
    operation: str,
    expression: str | None = None,
    values: list[Any] | None = None,
    text: str | None = None,
    data: Any | None = None,
) -> dict[str, Any]:
    """
    Run a small allowlisted Python utility.

    This is deliberately NOT arbitrary Python code execution.
    """

    normalized = operation.strip().lower()

    if normalized == "calculator":
        if not expression:
            raise ValueError(
                "expression is required."
            )

        result = _safe_number_expression(
            expression
        )

    elif normalized == "mean":
        numeric = [
            float(value)
            for value in (
                values or []
            )
        ]

        if not numeric:
            raise ValueError(
                "values are required."
            )

        result = mean(
            numeric
        )

    elif normalized == "median":
        numeric = [
            float(value)
            for value in (
                values or []
            )
        ]

        if not numeric:
            raise ValueError(
                "values are required."
            )

        result = median(
            numeric
        )

    elif normalized == "sort":
        result = sorted(
            values or [],
            key=lambda value: str(
                value
            ).casefold(),
        )

    elif normalized == "unique":
        result = list(
            dict.fromkeys(
                values or []
            )
        )

    elif normalized == "word_count":
        result = len(
            (text or "").split()
        )

    elif normalized == "json_pretty":
        result = json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=str,
        )

    else:
        raise ValueError(
            "Unsupported python_utility operation. "
            "Allowed: calculator, mean, median, sort, "
            "unique, word_count, json_pretty."
        )

    return {
        "operation": normalized,
        "result": result,
    }
