"""Machine-readable authority-safe integration gate evaluation.

ladon-quality: reviewed-schema-hotspot
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.child_acceptance import validate_child_bundle

CHILD_EXIT_CLASSES = {
    "correctness": "installed-scope-freshness-and-type-evidence-honest-discovery",
    "authority": "single-context-secret-safe-non-escalating-evidence-receipts",
}


def evaluate_authority_safe_gate(
    correctness: Mapping[str, Any], authority: Mapping[str, Any], *,
    evidence_root: Path | None = None,
    inventories: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Require both complete child bundles from the same release scope.

    Receipt metadata alone cannot establish suite coverage or artifact contents.
    The caller supplies the expected acceptance inventories independently of the
    receipts, and the bundle validator resolves their required evidence bytes.
    """
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
    if (
        correctness.get("sourceTreeIdentity"),
        correctness.get("environmentRef"),
        correctness.get("producerIdentity"),
        correctness.get("workingDirectory"),
    ) != (
        authority.get("sourceTreeIdentity"),
        authority.get("environmentRef"),
        authority.get("producerIdentity"),
        authority.get("workingDirectory"),
    ):
        return _result("failed", "child receipts do not identify the same release scope")
    if error := _bundle_error(correctness, authority, evidence_root, inventories):
        return _result("failed", error)
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


def _bundle_error(
    correctness: Mapping[str, Any], authority: Mapping[str, Any],
    evidence_root: Path | None,
    inventories: Mapping[str, Mapping[str, Any]] | None,
) -> str | None:
    """Resolve both independently required child bundles before conjunction."""
    if evidence_root is None or not isinstance(inventories, Mapping):
        return "child evidence root and acceptance inventories are required; metadata is insufficient"
    for role, receipt in (("correctness", correctness), ("authority", authority)):
        inventory = inventories.get(role)
        if not isinstance(inventory, Mapping):
            return f"{role} acceptance inventory is required"
        if inventory.get("exitClass") != CHILD_EXIT_CLASSES[role]:
            return f"{role} acceptance inventory has the wrong exit class"
        try:
            validate_child_bundle(receipt, bundle_root=evidence_root, inventory=inventory)
        except ValueError as error:
            return f"{role} child evidence is invalid: {error}"
    return None


def _validate_child(receipt: Mapping[str, Any], expected_exit: str) -> str | None:
    validators = (
        _child_shape_error,
        _child_scope_error,
        _child_commands_error,
        _child_identity_error,
        _child_provenance_error,
    )
    for validator in validators:
        if error := validator(receipt, expected_exit):
            return error
    return None


def _child_shape_error(receipt: Mapping[str, Any], expected_exit: str) -> str | None:
    if not isinstance(receipt, Mapping):
        return f"{expected_exit} child receipt must be an object"
    if receipt.get("schema") != "ladon-child-exit-receipt-v1":
        return f"{expected_exit} child receipt has an unsupported schema"
    if receipt.get("exitClass") == expected_exit:
        return f"{expected_exit} child receipt uses a legacy shorthand; a full exit class is required"
    if receipt.get("exitClass") != CHILD_EXIT_CLASSES[expected_exit]:
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


def _child_provenance_error(receipt: Mapping[str, Any], expected_exit: str) -> str | None:
    required = ("producerIdentity", "sourceTreeIdentity", "environmentRef", "workingDirectory")
    if any(not receipt.get(field) for field in required):
        return f"{expected_exit} child receipt lacks execution provenance"
    if not isinstance(receipt.get("commandVector"), list) or not receipt["commandVector"]:
        return f"{expected_exit} child receipt lacks a command vector"
    refs = receipt.get("resultArtifactRefs")
    logs = receipt.get("logArtifactRefs")
    if not isinstance(refs, list) or not refs or any(not _digest(ref) for ref in refs):
        return f"{expected_exit} child receipt lacks resolvable result artifacts"
    if not isinstance(logs, list) or not logs or any(not _digest(ref) for ref in logs):
        return f"{expected_exit} child receipt lacks resolvable logs"
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


__all__ = ["CHILD_EXIT_CLASSES", "evaluate_authority_safe_gate"]
