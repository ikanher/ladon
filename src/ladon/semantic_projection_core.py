"""Shared primitives for bounded semantic-result projections.

This module owns transport limits, deterministic identities, omission records,
and recursive value sanitization.  It deliberately knows nothing about Lean
evidence relationships or the shape of candidate observations.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any

PROJECTION_NAMES = ("llm", "review", "audit")
DIRECT_PROJECTION_MAX_BYTES = 8 * 1024
DISCOVERY_PROJECTION_MAX_BYTES = 32 * 1024

_STRUCTURAL_KEYS = frozenset(
    {
        "artifacts",
        "candidateSubject",
        "subjectRefs",
        "termStructural",
        "typeStructural",
        "valueStructural",
    }
)


class SemanticProjectionError(ValueError):
    """Raised when a compact result would contain unresolved evidence."""


def semantic_projection_bytes(payload: Mapping[str, Any]) -> bytes:
    """Serialize exactly as the installed JSON CLI for byte-limit enforcement."""

    try:
        rendered = json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
    except ValueError as error:
        raise SemanticProjectionError(
            "semantic projection contains a non-finite number"
        ) from error
    return (rendered + "\n").encode("utf-8")


def sanitize(
    value: Any,
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
    *,
    depth: int = 0,
) -> Any:
    """Return a bounded transport value without structural evidence bodies."""

    if depth > 6:
        omit(omissions, pointer, "projection-depth-limit", 1)
        return None
    if isinstance(value, Mapping):
        return _sanitize_mapping(value, projection, omissions, pointer, depth)
    if isinstance(value, list):
        return _sanitize_list(value, projection, omissions, pointer, depth)
    if isinstance(value, str):
        return bounded_text(value, 512, omissions, pointer)
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        omit(omissions, pointer, "projection-non-finite-number", 1)
        return None
    if value is None or isinstance(value, (bool, int)):
        return value
    return bounded_text(str(value), 512, omissions, pointer)


def _sanitize_mapping(
    value: Mapping[str, Any],
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
    depth: int,
) -> dict[str, Any]:
    keys = [key for key in sorted(value) if key not in _STRUCTURAL_KEYS]
    result = {
        str(key): sanitize(
            value[key], projection, omissions, f"{pointer}/{key}", depth=depth + 1
        )
        for key in keys[:24]
    }
    if len(keys) > 24:
        omit(omissions, pointer, "projection-mapping-limit", len(keys) - 24)
    for key in value:
        if key in _STRUCTURAL_KEYS:
            omit(omissions, f"{pointer}/{key}", "structural-evidence-omitted", 1)
    return result


def _sanitize_list(
    value: list[Any],
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
    depth: int,
) -> list[Any]:
    limit = 4 if projection == "llm" else 6
    result = [
        sanitize(item, projection, omissions, f"{pointer}/{index}", depth=depth + 1)
        for index, item in enumerate(value[:limit])
    ]
    if len(value) > limit:
        omit(omissions, pointer, "projection-collection-limit", len(value) - limit)
    return result


def safe_mapping(
    value: Any,
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> dict[str, Any]:
    """Sanitize a mapping value, returning an empty mapping for other inputs."""

    if not isinstance(value, Mapping):
        return {}
    sanitized = sanitize(value, projection, omissions, pointer)
    return sanitized if isinstance(sanitized, dict) else {}


def optional_text(
    value: Any,
    limit: int,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> str | None:
    """Return a bounded string when the canonical value is present."""

    return None if value is None else bounded_text(str(value), limit, omissions, pointer)


def bounded_text(
    value: str,
    limit: int,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> str:
    """Truncate UTF-8 text and record the omitted byte count."""

    encoded = value.encode("utf-8")
    if len(encoded) <= limit:
        return value
    omit(omissions, pointer, "projection-text-byte-limit", len(encoded) - limit)
    return truncate_utf8(value, limit)


def truncate_utf8(value: str, limit: int) -> str:
    """Truncate without splitting a UTF-8 code point."""

    if len(value.encode("utf-8")) <= limit:
        return value
    marker = "…"
    room = max(0, limit - len(marker.encode("utf-8")))
    raw = value.encode("utf-8")[:room]
    while raw:
        try:
            return raw.decode("utf-8") + marker
        except UnicodeDecodeError:
            raw = raw[:-1]
    return marker if limit >= len(marker.encode("utf-8")) else ""


def omit(
    omissions: list[dict[str, Any]], pointer: str, reason: str, omitted: int
) -> None:
    """Add or merge one deterministic omission record."""

    matching = next(
        (
            row
            for row in omissions
            if row["pointer"] == pointer and row["reason"] == reason
        ),
        None,
    )
    if matching is not None:
        matching["omitted"] += omitted
        return
    omissions.append({"pointer": pointer, "reason": reason, "omitted": omitted})
    omissions.sort(key=lambda row: (row["pointer"], row["reason"]))


def identity(value: Mapping[str, Any]) -> str:
    """Return the canonical JSON identity for one mapping."""

    try:
        rendered = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except ValueError as error:
        raise SemanticProjectionError(
            "semantic projection identity contains a non-finite number"
        ) from error
    encoded = rendered.encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def identity_text(value: str) -> str:
    """Return the UTF-8 identity for one text value."""

    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


__all__ = [
    "DIRECT_PROJECTION_MAX_BYTES",
    "DISCOVERY_PROJECTION_MAX_BYTES",
    "PROJECTION_NAMES",
    "SemanticProjectionError",
    "bounded_text",
    "identity",
    "identity_text",
    "omit",
    "optional_text",
    "safe_mapping",
    "sanitize",
    "semantic_projection_bytes",
    "truncate_utf8",
]
