"""Shared finite limits for the proposition-discovery testing profile."""

from __future__ import annotations

import math

MAX_SEMANTIC_TIMEOUT_SECONDS = 600.0
MAX_SEMANTIC_OUTPUT_BYTES = 64 * 1024 * 1024
MAX_SEMANTIC_RSS_BYTES = 64 * 1024 * 1024 * 1024
MAX_SEMANTIC_TERM_BYTES = 64 * 1024
MAX_SEMANTIC_CANDIDATE_BYTES = 4096
MAX_SEMANTIC_BATCH_CANDIDATES = 100
MAX_SEMANTIC_BATCH_BYTES = 64 * 1024
MAX_DISCOVERY_CANDIDATES = 1000
MAX_DISCOVERY_BATCH_SIZE = 100
MAX_DISCOVERY_PROCESS_SECONDS = 600.0
MAX_DISCOVERY_SCRATCH_ATTEMPTS = 1
MAX_DISCOVERY_RESULT_BYTES = 64 * 1024 * 1024


def validate_semantic_bounds(
    timeout_seconds: float, max_output_bytes: int, max_rss_bytes: int
) -> None:
    _validate_timeout(timeout_seconds)
    _validate_integer_bound(
        "output", max_output_bytes, maximum=MAX_SEMANTIC_OUTPUT_BYTES
    )
    _validate_integer_bound("memory", max_rss_bytes, maximum=MAX_SEMANTIC_RSS_BYTES)


def _validate_timeout(timeout_seconds: float) -> None:
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
        raise TypeError("semantic check timeout must be a finite number")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("semantic check timeout must be positive and finite")
    if timeout_seconds > MAX_SEMANTIC_TIMEOUT_SECONDS:
        raise ValueError("semantic check timeout exceeds the supported cap")


def _validate_integer_bound(label: str, value: int, *, maximum: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"semantic check {label} bound must be an integer")
    if value <= 0:
        raise ValueError(f"semantic check {label} bound must be positive")
    if value > maximum:
        raise ValueError(f"semantic check {label} bound exceeds the supported cap")


def validate_transport_text(module: str, goal: str, candidate: str | None = None) -> None:
    if len(module.encode("utf-8")) > MAX_SEMANTIC_TERM_BYTES:
        raise ValueError("semantic check module exceeds the supported byte cap")
    if len(goal.encode("utf-8")) > MAX_SEMANTIC_TERM_BYTES:
        raise ValueError("semantic check goal exceeds the supported byte cap")
    if candidate is not None and len(candidate.encode("utf-8")) > MAX_SEMANTIC_CANDIDATE_BYTES:
        raise ValueError("semantic check candidate exceeds the supported transport byte cap")


__all__ = [
    "MAX_DISCOVERY_BATCH_SIZE",
    "MAX_DISCOVERY_CANDIDATES",
    "MAX_DISCOVERY_PROCESS_SECONDS",
    "MAX_DISCOVERY_RESULT_BYTES",
    "MAX_DISCOVERY_SCRATCH_ATTEMPTS",
    "MAX_SEMANTIC_BATCH_BYTES",
    "MAX_SEMANTIC_BATCH_CANDIDATES",
    "MAX_SEMANTIC_CANDIDATE_BYTES",
    "MAX_SEMANTIC_OUTPUT_BYTES",
    "MAX_SEMANTIC_RSS_BYTES",
    "MAX_SEMANTIC_TERM_BYTES",
    "MAX_SEMANTIC_TIMEOUT_SECONDS",
    "validate_semantic_bounds",
    "validate_transport_text",
]
