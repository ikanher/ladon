"""Machine-readable authority-safe integration gate evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def evaluate_authority_safe_gate(
    correctness: Mapping[str, Any], authority: Mapping[str, Any]
) -> dict[str, Any]:
    """Require matching successful child receipts before integration claims."""
    candidate = correctness.get("candidateIdentity")
    if not candidate or candidate != authority.get("candidateIdentity"):
        return _result("failed", "child receipts do not identify the same candidate")
    if correctness.get("status") != "passed" or authority.get("status") != "passed":
        return _result("failed", "both correctness and authority child gates must pass")
    return {
        "schema": "ladon-authority-safe-gate-v1",
        "status": "passed",
        "candidateIdentity": candidate,
        "children": {"correctness": "passed", "authority": "passed"},
        "nonclaims": ["The integration gate does not grant public distribution authority."],
    }


def _result(status: str, reason: str) -> dict[str, Any]:
    return {"schema": "ladon-authority-safe-gate-v1", "status": status, "reason": reason}


__all__ = ["evaluate_authority_safe_gate"]
