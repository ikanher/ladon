from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from ladon import proofir_derivation, proofir_v3
from ladon.proofir_v3 import (
    ProofIRV3Error,
    detached_content_id,
    make_envelope,
    validate_envelope,
)

ENVIRONMENT = "sha256:" + "e" * 64
LEGACY_ARTIFACT_KINDS = frozenset(
    {
        "proofir_bridge_index",
        "proof_ir_lean_surface_bundle",
        "proof_ir_lean_replay_provenance",
        "proof_ir_v2_obligation_dag",
        "proof_ir_v2_obligation_dag_check_witness",
        "proof_surface_witness",
        "ladon_proof_surface_witness",
    }
)


def ref(kind: str, local_id: str) -> dict[str, str]:
    return {"kind": kind, "localId": local_id}


def coverage(*, observed: int = 1) -> dict[str, object]:
    return {
        "status": "complete",
        "population": {"kind": "artifact-subjects", "selector": {}},
        "universeKnown": True,
        "observed": observed,
        "omissions": [],
        "bounds": {},
    }


def claim_envelope() -> dict[str, object]:
    statement = ref("statement", "statement:goal")
    return make_envelope(
        artifact_kind="proofir.claim",
        producer={"name": "test-producer", "version": "1"},
        environment_ref=ENVIRONMENT,
        subject_refs=[statement],
        coverage=coverage(),
        payload={
            "claimId": "claim:goal",
            "statementRef": statement,
            "assertionState": "asserted",
        },
    ).to_dict()


def derivation_envelope(*, cyclic: bool = False) -> dict[str, object]:
    rule = ref("declaration", "decl:rule")
    premise_a = ref("statement", "statement:a")
    premise_b = ref("statement", "statement:b")
    premise_c = ref("statement", "statement:c")
    goal = ref("statement", "statement:goal")
    step_a = ref("derivation-step", "step:a")
    step_b = ref("derivation-step", "step:b")
    check = ref("check-run", "check:1")
    local_context = ref("local-context", "context:1")
    term = ref("term", "term:x")
    subjects = [
        rule,
        premise_a,
        premise_b,
        premise_c,
        goal,
        step_a,
        step_b,
        check,
        local_context,
        term,
    ]
    first_premises = [goal] if cyclic else [premise_a, premise_b]
    return make_envelope(
        artifact_kind="proofir.derivation",
        producer={"name": "test-producer", "version": "1"},
        environment_ref=ENVIRONMENT,
        subject_refs=subjects,
        coverage=coverage(observed=len(subjects)),
        payload={
            "derivationId": "derivation:goal",
            "acyclic": True,
            "steps": [
                {
                    "stepRef": step_a,
                    "kind": "theorem-application",
                    "ruleRef": rule,
                    "premiseRefs": first_premises,
                    "conclusionRef": goal,
                    "substitutions": [{"variable": "x", "termRef": term}],
                    "localContextRef": local_context,
                    "checkRunRef": check,
                },
                {
                    "stepRef": step_b,
                    "kind": "theorem-application",
                    "ruleRef": rule,
                    "premiseRefs": [premise_c],
                    "conclusionRef": goal,
                    "substitutions": [],
                    "localContextRef": local_context,
                    "checkRunRef": check,
                },
            ],
        },
    ).to_dict()


def evaluate_derivation(*args: object, **kwargs: object) -> Any:
    evaluator = getattr(proofir_derivation, "evaluate_derivation", None)
    assert evaluator is not None, "native-v3 derivation evaluator is missing"
    return evaluator(*args, **kwargs)


def test_validated_artifact_is_deeply_immutable_and_serializes_by_copy() -> None:
    source = claim_envelope()
    checked = validate_envelope(source)
    original_id = checked.content_id

    source["producer"]["name"] = "mutated"  # type: ignore[index]
    source["payload"]["claimId"] = "mutated"  # type: ignore[index]
    assert checked.payload["producer"]["name"] == "test-producer"
    assert checked.payload["payload"]["claimId"] == "claim:goal"
    assert checked.content_id == original_id

    with pytest.raises(TypeError):
        checked.payload["payload"]["claimId"] = "forbidden"  # type: ignore[index]

    serialized = checked.to_dict()
    serialized["payload"]["claimId"] = "copy-only"  # type: ignore[index]
    assert checked.payload["payload"]["claimId"] == "claim:goal"


def test_legacy_kind_registry_is_explicit() -> None:
    assert proofir_v3.LEGACY_ARTIFACT_KINDS == LEGACY_ARTIFACT_KINDS


@pytest.mark.parametrize(
    "artifact_kind",
    sorted(
        LEGACY_ARTIFACT_KINDS
        | {"proofir.compatibility.v2", "proofir.review-projection", "proofir.future"}
    ),
)
def test_legacy_unknown_and_projection_kinds_are_rejected_before_projection(
    artifact_kind: str,
) -> None:
    source = claim_envelope()
    source["artifactKind"] = artifact_kind
    source["artifactId"] = detached_content_id(source)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(source)
    diagnostic = captured.value.diagnostic
    assert diagnostic.stage == "kind-schema-valid"
    assert diagnostic.code in {"legacy-artifact-kind", "unsupported-artifact-kind"}
    assert diagnostic.pointer == "/artifactKind"


def test_common_envelope_is_closed() -> None:
    source = claim_envelope()
    source["extra"] = True
    source["artifactId"] = detached_content_id(source)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(source)
    assert captured.value.diagnostic.code == "unexpected-envelope-key"
    assert captured.value.diagnostic.pointer == "/extra"


def test_typed_references_are_artifact_scoped_and_closed() -> None:
    source = derivation_envelope()
    source["payload"]["steps"][0]["premiseRefs"][0] = ref(
        "statement", "statement:missing"
    )  # type: ignore[index]
    source["artifactId"] = detached_content_id(source)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(source)
    assert captured.value.diagnostic.stage == "reference-valid"
    assert captured.value.diagnostic.pointer == "/payload/steps/0/premiseRefs/0"

    obsolete_scope = derivation_envelope()
    obsolete_scope["payload"]["steps"][0]["ruleRef"]["environmentRef"] = (
        "sha256:" + "f" * 64
    )  # type: ignore[index]
    obsolete_scope["artifactId"] = detached_content_id(obsolete_scope)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(obsolete_scope)
    assert captured.value.diagnostic.code == "invalid-reference-shape"

    extra_field = derivation_envelope()
    extra_field["payload"]["steps"][0]["checkRunRef"]["extra"] = "no"  # type: ignore[index]
    extra_field["artifactId"] = detached_content_id(extra_field)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(extra_field)
    assert captured.value.diagnostic.code == "invalid-reference-shape"


def test_duplicate_subjects_and_duplicate_steps_are_rejected() -> None:
    duplicate_subject = derivation_envelope()
    duplicate_subject["subjectRefs"].append(
        copy.deepcopy(duplicate_subject["subjectRefs"][0])
    )  # type: ignore[union-attr,index]
    duplicate_subject["artifactId"] = detached_content_id(duplicate_subject)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(duplicate_subject)
    assert captured.value.diagnostic.code == "duplicate-subject-reference"

    duplicate_step = derivation_envelope()
    duplicate_step["payload"]["steps"][1]["stepRef"] = copy.deepcopy(  # type: ignore[index]
        duplicate_step["payload"]["steps"][0]["stepRef"]  # type: ignore[index]
    )
    duplicate_step["artifactId"] = detached_content_id(duplicate_step)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(duplicate_step)
    assert captured.value.diagnostic.code == "duplicate-step-reference"


def test_conflicting_duplicate_substitutions_are_rejected() -> None:
    source = derivation_envelope()
    source["payload"]["steps"][0]["substitutions"].append(  # type: ignore[index]
        {
            "variable": "x",
            "termRef": ref("term", "term:other"),
        }
    )
    source["subjectRefs"].append(ref("term", "term:other"))  # type: ignore[union-attr]
    source["artifactId"] = detached_content_id(source)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(source)
    assert captured.value.diagnostic.code == "conflicting-substitution"
    assert (
        captured.value.diagnostic.pointer == "/payload/steps/0/substitutions/1/variable"
    )


def test_derivation_evaluation_preserves_and_or_semantics() -> None:
    artifact = validate_envelope(derivation_envelope())
    a = ref("statement", "statement:a")
    b = ref("statement", "statement:b")
    c = ref("statement", "statement:c")
    goal = ref("statement", "statement:goal")

    assert not evaluate_derivation(artifact, goal, available_refs=[a]).satisfied
    first = evaluate_derivation(artifact, goal, available_refs=[a, b])
    assert first.satisfied
    assert first.selected_step_ref == ref("derivation-step", "step:a")
    second = evaluate_derivation(artifact, goal, available_refs=[c])
    assert second.satisfied
    assert second.selected_step_ref == ref("derivation-step", "step:b")


def test_cycles_and_partial_derivations_are_not_success() -> None:
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(derivation_envelope(cyclic=True))
    assert captured.value.diagnostic.stage == "semantic-valid"
    assert captured.value.diagnostic.code == "derivation-cycle"

    artifact = validate_envelope(derivation_envelope())
    result = evaluate_derivation(
        artifact,
        ref("statement", "statement:goal"),
        available_refs=[ref("statement", "statement:a")],
    )
    assert not result.satisfied
    assert ref("statement", "statement:b") in result.unresolved_refs


def test_diagnostics_are_deterministic_attributable_and_rfc6901_escaped() -> None:
    source = claim_envelope()
    source["bad/key~"] = True
    source["artifactId"] = detached_content_id(source)
    diagnostics = []
    for _ in range(2):
        with pytest.raises(ProofIRV3Error) as captured:
            validate_envelope(source)
        diagnostics.append(captured.value.diagnostic.to_dict())
    assert diagnostics[0] == diagnostics[1]
    assert diagnostics[0]["artifactId"] == source["artifactId"]
    assert diagnostics[0]["pointer"] == "/bad~1key~0"
    assert diagnostics[0]["message"]


def test_converter_product_surface_is_absent() -> None:
    root = Path(__file__).parents[1]
    assert not (root / "src/ladon/proofir_converter.py").exists()
    cli_source = (root / "src/ladon/proofir_v3_cli.py").read_text(encoding="utf-8")
    assert "proofir_converter" not in cli_source
    assert 'add_parser("convert")' not in cli_source
