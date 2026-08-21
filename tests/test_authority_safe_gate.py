from __future__ import annotations

import hashlib
import json

from ladon.authority_safe_gate import evaluate_authority_safe_gate


def _receipt(exit_class: str, candidate: str = "sha256:" + "a" * 64) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema": "ladon-child-exit-receipt-v1",
        "exitClass": exit_class,
        "status": "passed",
        "candidateIdentity": candidate,
        "analysisCompleteness": "complete",
        "omissions": [],
        "commands": [
            {
                "command": "uv run pytest -q",
                "status": "passed",
                "evidenceDigest": "sha256:" + "b" * 64,
            }
        ],
        "producerIdentity": "ladon-tests/v1",
        "sourceTreeIdentity": "sha256:" + "c" * 64,
        "environmentRef": "sha256:" + "d" * 64,
        "commandVector": ["python", "-m", "pytest"],
        "workingDirectory": "/repo",
        "resultArtifactRefs": ["sha256:" + "e" * 64],
        "logArtifactRefs": ["sha256:" + "f" * 64],
    }
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    receipt["receiptIdentity"] = "sha256:" + hashlib.sha256(encoded).hexdigest()
    return receipt


def test_authority_safe_gate_requires_matching_passed_children() -> None:
    result = evaluate_authority_safe_gate(_receipt("correctness"), _receipt("authority"))
    assert result["status"] == "passed"


def test_authority_safe_gate_rejects_partial_or_mismatched_children() -> None:
    result = evaluate_authority_safe_gate(
        _receipt("correctness", "sha256:" + "a" * 64),
        _receipt("authority", "sha256:" + "b" * 64),
    )
    assert result["status"] == "failed"


def test_authority_safe_gate_rejects_minimal_labels_and_tampered_receipts() -> None:
    minimal = {"status": "passed", "candidateIdentity": "not-a-digest"}
    assert evaluate_authority_safe_gate(minimal, minimal)["status"] == "failed"
    correctness = _receipt("correctness")
    correctness["commands"] = []
    assert evaluate_authority_safe_gate(correctness, _receipt("authority"))["status"] == "failed"
