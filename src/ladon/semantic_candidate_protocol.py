"""Closed validation helpers for Lean semantic-candidate protocol frames."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


def decode_single_frame(stdout: str, prefix: str) -> dict[str, Any]:
    frames = [line[len(prefix) :] for line in stdout.splitlines() if line.startswith(prefix)]
    if not frames:
        raise ValueError("Lean semantic helper emitted no JSON payload")
    if len(frames) != 1:
        raise ValueError("Lean semantic helper emitted duplicate terminal frames")
    try:
        payload = json.loads(frames[0])
    except json.JSONDecodeError as error:
        raise ValueError("Lean semantic helper emitted non-framed JSON output") from error
    if not isinstance(payload, dict):
        raise TypeError("Lean semantic helper emitted a non-object frame")
    return payload


def validate_worker_subject(subject: Any, label: str, expected_name: str) -> None:
    if not isinstance(subject, dict) or subject.get("name") != expected_name:
        raise ValueError(f"Lean semantic helper returned a foreign {label} identity")
    if not all(
        isinstance(subject.get(field), str) and subject[field]
        for field in ("name", "typeDisplay", "typeStructural")
    ):
        raise ValueError(f"Lean semantic helper returned an invalid {label} subject")


def validate_worker_modules(modules: Any, requested_module: str) -> None:
    if not isinstance(modules, list):
        raise TypeError("Lean semantic helper modules must be an array")
    valid = all(
        isinstance(row, dict)
        and set(row) == {"module", "oleanPath"}
        and all(isinstance(row[field], str) and row[field] for field in row)
        for row in modules
    )
    if not valid or not any(row["module"] == requested_module for row in modules):
        raise ValueError("Lean semantic helper environment omits the requested module")


def validate_application_rows(payload: Mapping[str, Any]) -> None:
    substitution_fields = {"variable", "termDisplay", "termStructural"}
    discharged_fields = {
        "premiseOrdinal",
        "premiseTypeDisplay",
        "dischargedByLocalRef",
        "method",
    }
    expression_fields = {"typeDisplay", "typeStructural"}
    local_fields = {
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
    if not _closed_string_rows(payload["substitutions"], substitution_fields):
        raise ValueError("Lean semantic helper returned invalid substitutions")
    if not _closed_discharged_rows(payload["dischargedHypotheses"], discharged_fields):
        raise ValueError("Lean semantic helper returned invalid discharged hypotheses")
    local_ids = {
        row.get("localId") for row in payload["localContext"] if isinstance(row, dict)
    }
    for row in payload["dischargedHypotheses"]:
        if row["dischargedByLocalRef"] not in local_ids:
            raise ValueError("Lean semantic helper discharged premise via an unknown local")
    if not _closed_string_rows(payload["residualPremises"], expression_fields):
        raise ValueError("Lean semantic helper returned invalid residual premises")
    if not _closed_local_context_rows(payload["localContext"], local_fields):
        raise ValueError("Lean semantic helper returned invalid local context")


def _closed_string_rows(rows: list[Any], fields: set[str]) -> bool:
    return all(
        isinstance(row, dict)
        and set(row) == fields
        and all(isinstance(row[field], str) and row[field] for field in fields)
        for row in rows
    )


def _closed_discharged_rows(rows: list[Any], fields: set[str]) -> bool:
    return all(
        isinstance(row, dict)
        and set(row) == fields
        and isinstance(row["premiseOrdinal"], int)
        and not isinstance(row["premiseOrdinal"], bool)
        and row["premiseOrdinal"] >= 0
        and all(isinstance(row[field], str) and row[field] for field in fields - {"premiseOrdinal"})
        for row in rows
    )


def _closed_local_context_rows(rows: list[Any], fields: set[str]) -> bool:
    return all(
        isinstance(row, dict)
        and set(row) == fields
        and _valid_local_context_scalars(row)
        and isinstance(row["dependencies"], list)
        and all(isinstance(dep, str) and dep for dep in row["dependencies"])
        for row in rows
    )


def _valid_local_context_scalars(row: dict[str, Any]) -> bool:
    string_fields = {
        "localId",
        "userName",
        "binderInfo",
        "typeDisplay",
        "typeStructural",
        "valueDisplay",
        "valueStructural",
        "origin",
    }
    required_fields = string_fields - {"valueDisplay", "valueStructural"}
    return all(isinstance(row[field], str) for field in string_fields) and all(
        row[field] for field in required_fields
    )


__all__ = [
    "decode_single_frame",
    "validate_application_rows",
    "validate_worker_modules",
    "validate_worker_subject",
]
