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


def validate_application_rows(payload: Mapping[str, Any], *, protocol: str | None = None) -> None:
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
    _validate_discharged_local_refs(payload)
    if not _closed_string_rows(payload["residualPremises"], expression_fields):
        raise ValueError("Lean semantic helper returned invalid residual premises")
    if not _closed_local_context_rows(payload["localContext"], local_fields):
        raise ValueError("Lean semantic helper returned invalid local context")
    _validate_versioned_rows(payload, protocol)


def _validate_versioned_rows(payload, protocol) -> None:
    protocol = protocol or payload.get("protocol", "ladon-lean-semantic-v3/check-candidate")
    if payload.get("protocol") is not None and payload.get("protocol") != protocol:
        raise ValueError("semantic application rows disagree with their declared protocol")
    if protocol == "ladon-lean-semantic-v4/check-candidate" or protocol == "ladon-lean-semantic-v4/check-candidates":
        if not {"residualContexts", "declarationBinders"} <= set(payload):
            raise ValueError("v4 observation omitted residual context or declaration binder evidence")
        validate_v4_context_populations(
            payload["residualContexts"], payload["declarationBinders"],
            residual_count=len(payload["residualPremises"]),
        )


def _validate_discharged_local_refs(payload) -> None:
    local_ids = {
        row.get("localId") for row in payload["localContext"] if isinstance(row, dict)
    }
    for row in payload["dischargedHypotheses"]:
        if row["dischargedByLocalRef"] not in local_ids:
            raise ValueError("Lean semantic helper discharged premise via an unknown local")


def validate_v4_context_populations(contexts, binders, *, residual_count=None) -> None:
    """Validate owned rows; an unavailable expression inventory supplies no count."""
    if not isinstance(contexts, list):
        raise TypeError("v4 residual context population must be an array")
    if residual_count is not None and len(contexts) != residual_count:
        raise ValueError("v4 residual context population disagrees with residual premises")
    local_fields = {"localId", "userName", "binderInfo", "typeDisplay", "typeStructural",
                    "valueDisplay", "valueStructural", "dependencies", "origin"}
    if not isinstance(binders, list) or not _closed_local_context_rows(binders, local_fields):
        raise ValueError("v4 declaration binder inventory is invalid")
    _validate_binder_provenance(binders)
    _validate_context_dependencies(binders)
    goal_ids: set[str] = set()
    for context in contexts:
        _validate_residual_context(context, local_fields)
        if context["goalId"] in goal_ids:
            raise ValueError("v4 residual context goal identities are duplicated")
        goal_ids.add(context["goalId"])


def _validate_binder_provenance(binders) -> None:
    for row in binders:
        if row["origin"] != "declaration-parameter" or row["valueDisplay"] or row["valueStructural"]:
            raise ValueError("v4 declaration binder has invalid provenance or value")


def _validate_residual_context(context, local_fields) -> None:
    if not isinstance(context, dict) or set(context) != {"goalId", "localContext"}:
        raise ValueError("v4 residual context row is invalid")
    if not isinstance(context["goalId"], str) or not context["goalId"]:
        raise ValueError("v4 residual context goal identity is invalid")
    rows = context["localContext"]
    if not isinstance(rows, list) or not _closed_local_context_rows(rows, local_fields):
        raise ValueError("v4 residual local context is invalid")
    _validate_context_dependencies(rows)


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


def _validate_context_dependencies(rows: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for row in rows:
        local_id = row["localId"]
        if local_id in seen:
            raise ValueError("v4 local context contains duplicate local identity")
        deps = row["dependencies"]
        if len(deps) != len(set(deps)) or any(dep not in seen for dep in deps):
            raise ValueError("v4 local context has unknown or forward dependencies")
        if bool(row["valueDisplay"]) != bool(row["valueStructural"]):
            raise ValueError("v4 local value display and structure disagree")
        seen.add(local_id)


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
