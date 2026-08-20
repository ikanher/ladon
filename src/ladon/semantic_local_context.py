"""Ordered caller-local context validation and Lean goal adaptation."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any


def validate_local_context(
    rows: Sequence[Mapping[str, str]],
    *,
    valid_name: Callable[[str], bool],
    validate_type: Callable[[str], None],
) -> None:
    if len(rows) > 256:
        raise ValueError("semantic local context exceeds the row cap")
    total = 0
    for row in rows:
        name, type_text = row.get("name"), row.get("type")
        if not isinstance(name, str) or not valid_name(name):
            raise ValueError("semantic local context contains an invalid name")
        if not isinstance(type_text, str):
            raise TypeError("semantic local context contains an invalid type")
        validate_type(type_text)
        total += len(name.encode()) + len(type_text.encode())
    if total > 1024 * 1024:
        raise ValueError("semantic local context exceeds the byte cap")


def goal_with_local_context(goal: str, rows: Sequence[Mapping[str, str]]) -> str:
    if not rows:
        return goal
    binders = " ".join(f"({row['name']} : {row['type']})" for row in rows)
    return f"∀ {binders}, {goal}"


def validate_observed_local_context(
    observed: Sequence[Mapping[str, Any]], requested: Sequence[Mapping[str, str]]
) -> None:
    observed_names = [row.get("userName") for row in observed[: len(requested)]]
    requested_names = [row["name"] for row in requested]
    if observed_names != requested_names:
        raise ValueError("Lean semantic helper did not elaborate the requested local context")


__all__ = [
    "goal_with_local_context",
    "validate_local_context",
    "validate_observed_local_context",
]
