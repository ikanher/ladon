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
    names: set[str] = set()
    for row in rows:
        name, type_text = row.get("name"), row.get("type")
        if not isinstance(name, str) or not valid_name(name):
            raise ValueError("semantic local context contains an invalid name")
        if not isinstance(type_text, str):
            raise TypeError("semantic local context contains an invalid type")
        if name in names:
            raise ValueError("semantic local context contains duplicate names")
        names.add(name)
        if any(token in type_text for token in ("\n", "\r", ":=", ";", "(", ")", "{", "}")):
            raise ValueError("semantic local context type contains unsupported binder syntax")
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
    local_ids: set[str] = set()
    local_names: set[str] = set()
    prefix = observed[: len(requested)]
    if len(prefix) != len(requested):
        raise ValueError("Lean semantic helper did not elaborate the requested local context")
    for observed_row, requested_row in zip(prefix, requested):
        _validate_observed_row_shape(observed_row)
        local_id = observed_row["localId"]
        user_name = observed_row["userName"]
        if local_id in local_ids or user_name in local_names:
            raise ValueError("Lean semantic helper returned duplicate local identity")
        local_ids.add(local_id)
        local_names.add(user_name)
        if observed_row.get("userName") != requested_row["name"]:
            raise ValueError("Lean semantic helper returned a reordered local context")
        if _normalize_type(observed_row.get("typeDisplay")) != _normalize_type(
            requested_row["type"]
        ):
            raise ValueError(
                f"Lean semantic helper returned a mismatched type for local {requested_row['name']}"
            )
        structural = _normalize_type(observed_row.get("typeStructural"))
        displayed = _normalize_type(observed_row.get("typeDisplay"))
        if structural.isidentifier() and structural not in displayed.split():
            raise ValueError(
                f"Lean semantic helper returned a structurally mismatched type for local {requested_row['name']}"
            )
    for row in observed[len(requested) :]:
        _validate_observed_row_shape(row)
        if row["localId"] in local_ids or row["userName"] in local_names:
            raise ValueError("Lean semantic helper returned duplicate local identity")
        local_ids.add(row["localId"])
        local_names.add(row["userName"])


def _validate_observed_row_shape(row: Mapping[str, Any]) -> None:
    required = {
        "localId",
        "userName",
        "binderInfo",
        "typeDisplay",
        "typeStructural",
        "valueDisplay",
        "valueStructural",
        "dependencies",
        "origin",
    }
    if set(row) != required:
        raise ValueError("Lean semantic helper returned an incomplete local context row")
    if any(not isinstance(row[field], str) for field in required - {"dependencies"}):
        raise TypeError("Lean semantic helper returned malformed local context metadata")
    if not isinstance(row["dependencies"], list) or any(
        not isinstance(item, str) for item in row["dependencies"]
    ):
        raise TypeError("Lean semantic helper returned malformed local dependencies")


def _normalize_type(value: Any) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


__all__ = [
    "goal_with_local_context",
    "validate_local_context",
    "validate_observed_local_context",
]
