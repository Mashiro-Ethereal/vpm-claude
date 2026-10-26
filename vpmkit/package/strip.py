"""Remove reward functions while preserving all other source text."""

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class StripResult:
    text: str
    removed: list[tuple[str, int, int]]


class ResidualRewardError(ValueError):
    """Lowercase reward text remains after removing the functions."""


def strip_reward_functions(source: str) -> StripResult:
    """Report removed ranges in original numbering and residuals in stripped numbering."""
    tree = ast.parse(source)
    removed = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in (
            "compute_dense_reward", "compute_normalized_dense_reward"
        ):
            first = min([node.lineno, *(item.lineno for item in node.decorator_list)])
            removed.append((node.name, first, node.end_lineno))
    removed.sort(key=lambda item: item[1])
    deleted = {line for _, first, last in removed for line in range(first, last + 1)}
    text = "".join(line for number, line in enumerate(source.splitlines(keepends=True), 1)
                   if number not in deleted)
    residuals = [f"{number}: {line}" for number, line in enumerate(text.splitlines(), 1)
                 if "reward" in line]
    if residuals:
        raise ResidualRewardError("Residual 'reward' in stripped source:\n" + "\n".join(residuals))
    return StripResult(text, removed)
