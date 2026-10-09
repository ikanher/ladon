"""Compact text projection for index status, search and lifecycle operations."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


def render_lifecycle(payload: Mapping[str, Any]) -> str:
        lines = [
            f"proof-search index {payload.get('operation')}: {payload.get('status')}",
            f"directory: {payload.get('directory')}",
        ]
        for key in ("total", "returned", "totalBytes", "eligibleBytes", "reclaimedBytes"):
            if key in payload:
                lines.append(f"{key}: {payload[key]}")
        for row in payload.get("rows", []):
            lines.append(
                f"- {row.get('name')}: {row.get('status', row.get('classification'))} "
                f"bytes={row.get('bytes', 0)} reason={row.get('reason', '')}"
            )
        if payload.get("truncated"):
            lines.append("further entries omitted; use a larger --limit")
        return "\n".join(lines) + "\n"

def _render_header(payload: Mapping[str, Any]) -> list[str]:
    operation = str(payload.get("operation", "index"))
    lines = [
        f"proof-search {operation}: {payload.get('status', 'unknown')}",
        f"path: {payload.get('indexPath', 'unavailable')}",
    ]
    if operation in {"query", "search-name"}:
        lines.extend(_query_lines(payload))
    lines.extend(_change_lines(payload, operation))
    if operation == "status":
        lines.extend(_status_lines(payload))
    for key, label in (
        ("generationIdentity", "generation"),
        ("freshness", "freshness"),
        ("evidenceStatus", "evidence"),
        ("databaseBytes", "bytes"),
        ("elapsedSeconds", "elapsed_seconds"),
    ):
        if payload.get(key) is not None:
            lines.append(f"{label}: {payload[key]}")
    if operation == "status":
        lines.append(f"budget_bytes: {payload.get('maxIndexBytes', 'unknown')}")
        lock = payload.get("buildLock", {})
        if isinstance(lock, Mapping):
            lines.append(f"publisher: {lock.get('status', 'unknown')}")
    counts = payload.get("counts")
    if isinstance(counts, Mapping):
        lines.append("counts: " + ", ".join(f"{key}={counts[key]}" for key in sorted(counts)))
    return lines


def _query_lines(payload: Mapping[str, Any]) -> list[str]:
    lines = []
    freshness = payload.get("freshness")
    if freshness == "unchecked":
        lines.append("current sources: not checked; results describe stored index rows only")
    elif freshness not in {None, "fresh"}:
        lines.append(f"current sources: {freshness}; results may omit current declarations")
    match = payload.get("matchSummary")
    if isinstance(match, Mapping) and match.get("exactCountScope") != "not-applicable":
        lines.append(
            f"{match.get('exactMatches', 0)} exact matches "
            f"({match.get('exactCountScope', 'unknown')})"
        )
        if match.get("lexicalSuggestionsReturned"):
            lines.append("lexical suggestions from stored rows:")
    return lines


def _change_lines(payload: Mapping[str, Any], operation: str) -> list[str]:
    lines = []
    changes = payload.get("sourceChanges")
    if isinstance(changes, Mapping) and changes.get("status") == "compared":
        counts = changes.get("counts", {})
        lines.append(
            "source changes: " + ", ".join(
                f"{kind}={counts.get(kind, 0)}" for kind in ("added", "changed", "removed")
            )
        )
        if operation == "status" and (
            payload.get("detailsRequested") or payload.get("changedRequested")
        ):
            for kind in ("added", "changed", "removed"):
                for row in changes.get("samples", {}).get(kind, []):
                    lines.append(f"  {kind}: {row['module']} {row['path']}")
                if changes.get("truncated", {}).get(kind):
                    lines.append(f"  {kind}: further rows omitted")
    return lines


def _status_lines(payload: Mapping[str, Any]) -> list[str]:
    identity = payload.get("currentGenerationIdentity") or "unavailable"
    lines = [f"current_inputs_generation: {identity}"]
    if not payload.get("detailsRequested"):
        return lines + ["detailed index inventory: rerun with --details"]
    for key in (
        "storage", "lookupIndexes", "lookupIndexColumns", "querySurfaces",
        "foreignKeys", "unconstrainedExternalReferences",
    ):
        if key in payload:
            lines.append(f"{key}: {json.dumps(payload[key], sort_keys=True)}")
    return lines
