"""Machine-readable authority-safe integration gate evaluation."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any


def evaluate_authority_safe_gate(
    correctness: Mapping[str, Any], authority: Mapping[str, Any]
) -> dict[str, Any]:
    """Require matching successful child receipts before integration claims."""
    correctness_error = _validate_child(correctness, "correctness")
    authority_error = _validate_child(authority, "authority")
    if correctness_error or authority_error:
        return _result(
            "failed",
            correctness_error or authority_error or "invalid child receipt",
        )
    candidate = correctness.get("candidateIdentity")
    if not candidate or candidate != authority.get("candidateIdentity"):
        return _result("failed", "child receipts do not identify the same candidate")
    if correctness.get("status") != "passed" or authority.get("status") != "passed":
        return _result("failed", "both correctness and authority child gates must pass")
    return {
        "schema": "ladon-authority-safe-gate-v1",
        "status": "passed",
        "candidateIdentity": candidate,
        "children": {
            "correctness": correctness["receiptIdentity"],
            "authority": authority["receiptIdentity"],
        },
        "nonclaims": ["The integration gate does not grant public distribution authority."],
    }


def _result(status: str, reason: str) -> dict[str, Any]:
    return {"schema": "ladon-authority-safe-gate-v1", "status": status, "reason": reason}


def _validate_child(receipt: Mapping[str, Any], expected_exit: str) -> str | None:
    validators = (
        _child_shape_error,
        _child_scope_error,
        _child_commands_error,
        _child_identity_error,
    )
    for validator in validators:
        if error := validator(receipt, expected_exit):
            return error
    return None


def _child_shape_error(receipt: Mapping[str, Any], expected_exit: str) -> str | None:
    if receipt.get("schema") != "ladon-child-exit-receipt-v1":
        return f"{expected_exit} child receipt has an unsupported schema"
    if receipt.get("exitClass") != expected_exit:
        return f"{expected_exit} child receipt has the wrong exit class"
    if receipt.get("status") != "passed":
        return f"{expected_exit} child receipt did not pass"
    if not _digest(receipt.get("candidateIdentity")):
        return f"{expected_exit} child receipt has no exact candidate digest"
    return None


def _child_scope_error(receipt: Mapping[str, Any], expected_exit: str) -> str | None:
    if receipt.get("analysisCompleteness") != "complete" or receipt.get("omissions") != []:
        return f"{expected_exit} child receipt is partial"
    return None


def _child_commands_error(receipt: Mapping[str, Any], expected_exit: str) -> str | None:
    commands = receipt.get("commands")
    if (
        not isinstance(commands, list)
        or not commands
        or any(not _valid_command(row) for row in commands)
    ):
        return f"{expected_exit} child receipt has invalid command evidence"
    return None


def _child_identity_error(receipt: Mapping[str, Any], expected_exit: str) -> str | None:
    expected_identity = _receipt_identity(receipt)
    if receipt.get("receiptIdentity") != expected_identity:
        return f"{expected_exit} child receipt identity is invalid"
    return None


def _valid_command(row: Any) -> bool:
    return (
        isinstance(row, Mapping)
        and isinstance(row.get("command"), str)
        and bool(row["command"])
        and row.get("status") == "passed"
        and _digest(row.get("evidenceDigest"))
    )


def _digest(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def _receipt_identity(receipt: Mapping[str, Any]) -> str:
    body = dict(receipt)
    body.pop("receiptIdentity", None)
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


__all__ = ["evaluate_authority_safe_gate"]
