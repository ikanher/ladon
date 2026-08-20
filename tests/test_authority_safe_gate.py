from __future__ import annotations

from ladon.authority_safe_gate import evaluate_authority_safe_gate


def test_authority_safe_gate_requires_matching_passed_children() -> None:
    receipt = {"status": "passed", "candidateIdentity": "sha256:candidate"}
    result = evaluate_authority_safe_gate(receipt, receipt)
    assert result["status"] == "passed"


def test_authority_safe_gate_rejects_partial_or_mismatched_children() -> None:
    result = evaluate_authority_safe_gate(
        {"status": "passed", "candidateIdentity": "sha256:a"},
        {"status": "failed", "candidateIdentity": "sha256:b"},
    )
    assert result["status"] == "failed"
