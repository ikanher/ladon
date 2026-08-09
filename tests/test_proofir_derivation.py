from __future__ import annotations

import pytest

from ladon.proofir_derivation import (
    evaluate_derivation,
)
from ladon.proofir_v3 import make_envelope

ENVIRONMENT = "sha256:" + "e" * 64
FOREIGN_ARTIFACT = "sha256:" + "f" * 64


def ref(kind: str, local_id: str) -> dict[str, str]:
    return {"kind": kind, "localId": local_id}


def alternative_derivation() -> object:
    goal = ref("statement", "goal")
    premise_a = ref("statement", "a")
    premise_b = ref("statement", "b")
    step_a = ref("derivation-step", "step:a")
    step_b = ref("derivation-step", "step:b")
    rule = ref("declaration", "rule")
    context = ref("local-context", "context")
    check = ref("check-run", "check")
    subjects = [goal, premise_a, premise_b, step_a, step_b, rule, context, check]
    return make_envelope(
        artifact_kind="proofir.derivation",
        producer={"name": "test", "version": "1"},
        environment_ref=ENVIRONMENT,
        subject_refs=subjects,
        coverage={"status": "complete", "observed": len(subjects)},
        payload={
            "derivationId": "derivation:goal",
            "acyclic": True,
            "steps": [
                {
                    "stepRef": step_a,
                    "kind": "theorem-application",
                    "ruleRef": rule,
                    "premiseRefs": [premise_a],
                    "conclusionRef": goal,
                    "substitutions": [],
                    "localContextRef": context,
                    "checkRunRef": check,
                },
                {
                    "stepRef": step_b,
                    "kind": "theorem-application",
                    "ruleRef": rule,
                    "premiseRefs": [premise_b],
                    "conclusionRef": goal,
                    "substitutions": [],
                    "localContextRef": context,
                    "checkRunRef": check,
                },
            ],
        },
    )


def test_evaluation_rejects_an_unresolved_external_owner() -> None:
    artifact = alternative_derivation()
    with pytest.raises(ValueError, match="external"):
        evaluate_derivation(
            artifact,
            ref("statement", "goal"),
            available_refs=[
                {
                    "artifactRef": FOREIGN_ARTIFACT,
                    "kind": "statement",
                    "localId": "a",
                }
            ],
        )


def test_successful_or_alternative_does_not_leak_failed_branch_residuals() -> None:
    artifact = alternative_derivation()
    result = evaluate_derivation(
        artifact,
        ref("statement", "goal"),
        available_refs=[ref("statement", "b")],
    )
    assert result.satisfied
    assert result.selected_step_ref == ref("derivation-step", "step:b")
    assert result.unresolved_refs == ()


def test_structural_satisfaction_does_not_claim_checker_acceptance() -> None:
    artifact = alternative_derivation()
    result = evaluate_derivation(
        artifact,
        ref("statement", "goal"),
        available_refs=[ref("statement", "a")],
    )
    assert result.structurally_satisfied
    assert result.satisfied  # Backward-compatible spelling for structural satisfaction.
    assert not result.checker_accepted
