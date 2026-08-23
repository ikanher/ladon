"""Bounded stderr diagnostics for the ordinary proof-search CLI."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from typing import Any

from ladon.proof_search_index import ProofSearchIndexError

_SEMANTIC_TERMINAL_RESULTS = frozenset(
    {"accepted", "applicable-with-residuals", "rejected"}
)


def emit_terminal(
    operation: str,
    *,
    exit_class: str,
    exit_code: int,
    diagnostic: Mapping[str, Any] | None = None,
) -> None:
    """Write one stable terminal failure record without contaminating stdout."""

    payload: dict[str, Any] = {
        "exitClass": exit_class,
        "exitCode": exit_code,
        "operation": operation,
        "schema": "ladon-proof-search-terminal-v1",
        "status": "interrupted" if exit_class == "interrupted" else "failed",
    }
    if diagnostic is not None:
        payload["diagnostic"] = dict(diagnostic)
    print(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        file=sys.stderr,
        flush=True,
    )


def exception_diagnostic(error: ProofSearchIndexError) -> dict[str, Any]:
    """Project a bounded actionable diagnostic from an index-domain failure."""

    diagnostic: dict[str, Any] = {
        "code": error.code,
        "message": bounded_message(error),
    }
    if error.remediation:
        diagnostic["remediation"] = error.remediation
    if error.details:
        diagnostic["details"] = error.details
    return diagnostic


def bounded_message(error: BaseException, *, limit: int = 4096) -> str:
    """Retain actionable process detail without allowing unbounded stderr records."""

    message = str(error).strip() or type(error).__name__
    if len(message) <= limit:
        return message
    return message[: limit - 1] + "…"


def semantic_payload_failed(operation: str, payload: Mapping[str, Any]) -> bool:
    """Identify semantic result payloads that represent operational failure."""

    coverage = payload.get("coverage")
    if isinstance(coverage, Mapping) and isinstance(
        coverage.get("operationalFailure"), bool
    ):
        return bool(coverage["operationalFailure"])
    if operation == "check.candidate":
        return payload.get("status") not in _SEMANTIC_TERMINAL_RESULTS
    if operation != "discover":
        return False
    candidates = payload.get("candidates")
    return not isinstance(candidates, list) or any(
        _discovery_candidate_failed(candidate) for candidate in candidates
    )


def semantic_progress_fields(
    operation: str,
    payload: Mapping[str, Any],
    exit_code: int,
) -> dict[str, object]:
    """Attach semantic result state only to semantic terminal progress rows."""

    if operation not in {"check.candidate", "discover"}:
        return {}
    return {"exitCode": exit_code, "resultStatus": str(payload.get("status", "unknown"))}


def _discovery_candidate_failed(candidate: Any) -> bool:
    if not isinstance(candidate, Mapping):
        return True
    check = candidate.get("check")
    if not isinstance(check, Mapping):
        return True
    if check.get("status") not in _SEMANTIC_TERMINAL_RESULTS:
        return True
    scratch = check.get("scratch")
    return isinstance(scratch, Mapping) and scratch.get("status") != "compiled"


__all__ = [
    "bounded_message",
    "emit_terminal",
    "exception_diagnostic",
    "semantic_payload_failed",
    "semantic_progress_fields",
]
