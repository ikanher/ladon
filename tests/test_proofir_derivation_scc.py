from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from support.proofir_v3_native import (
    ENVIRONMENT,
    attempt_log_artifact,
    derivation_artifact,
    envelope,
    plan_artifact,
    ref,
)

from ladon import proofir_derivation
from ladon.proofir_derivation import DerivationQueryBounds
from ladon.proofir_v3 import ProofIRV3Error, detached_content_id, validate_envelope


def recursive_derivation() -> dict[str, Any]:
    statements = [ref("statement", name) for name in ("A", "B")]
    steps = [ref("derivation-step", name) for name in ("step:a", "step:b")]
    rule = ref("declaration", "rule")
    context = ref("local-context", "context")
    check = ref("check-run", "check")
    payload = {
        "derivationId": "derivation:recursive",
        "acyclic": False,
        "recursion": {
            "policy": "declared-strongly-connected-components",
            "components": [
                {
                    "componentId": "scc:ab",
                    "semantics": "declared-recursive-fixed-point",
                    "statementRefs": statements,
                }
            ],
        },
        "steps": [
            {
                "stepRef": steps[0],
                "kind": "theorem-application",
                "ruleRef": rule,
                "premiseRefs": [statements[1]],
                "conclusionRef": statements[0],
                "substitutions": [],
                "localContextRef": context,
                "checkRunRef": check,
            },
            {
                "stepRef": steps[1],
                "kind": "theorem-application",
                "ruleRef": rule,
                "premiseRefs": [statements[0]],
                "conclusionRef": statements[1],
                "substitutions": [],
                "localContextRef": context,
                "checkRunRef": check,
            },
        ],
    }
    return envelope(
        "proofir.derivation",
        payload,
        [*statements, *steps, rule, context, check],
        environment=ENVIRONMENT,
    )


def scc_analysis(*args: object, **kwargs: object) -> dict[str, Any]:
    implementation = getattr(proofir_derivation, "analyze_sccs", None)
    assert implementation is not None, "analyze_sccs is missing"
    return implementation(*args, **kwargs)


def test_recursive_derivation_requires_and_exposes_exact_declared_scc() -> None:
    artifact = recursive_derivation()
    checked = validate_envelope(artifact)
    result = scc_analysis(checked)

    assert result["queryKind"] == "scc-analysis"
    assert result["status"] == "complete"
    assert result["complete"]
    assert result["checkerAcceptance"] == "not-evaluated"
    assert any("theorem truth" in row for row in result["nonclaims"])
    assert any("fixed-point semantics" in row for row in result["nonclaims"])
    assert result["result"]["recursive"] is True
    assert result["result"]["components"] == [
        {
            "componentId": "scc:ab",
            "semantics": "declared-recursive-fixed-point",
            "statementRefs": [ref("statement", "A"), ref("statement", "B")],
            "internalEdges": [
                {"fromRef": ref("statement", "A"), "toRef": ref("statement", "B")},
                {"fromRef": ref("statement", "B"), "toRef": ref("statement", "A")},
            ],
        }
    ]


def test_recursive_scc_metadata_must_match_the_actual_cycle() -> None:
    artifact = recursive_derivation()
    artifact["payload"]["recursion"]["components"][0]["statementRefs"] = [  # type: ignore[index]
        ref("statement", "A")
    ]
    artifact["artifactId"] = detached_content_id(artifact)

    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(artifact)
    assert captured.value.diagnostic.stage == "semantic-valid"
    assert captured.value.diagnostic.code == "scc-metadata-mismatch"
    assert captured.value.diagnostic.pointer == "/payload/recursion/components"


def test_acyclic_derivation_cannot_smuggle_recursion_metadata() -> None:
    artifact = recursive_derivation()
    artifact["payload"]["acyclic"] = True  # type: ignore[index]
    artifact["artifactId"] = detached_content_id(artifact)

    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(artifact)
    assert captured.value.diagnostic.code == "unexpected-payload-key"
    assert captured.value.diagnostic.pointer == "/payload/recursion"


def test_scc_analysis_is_bounded_without_publishing_partial_components() -> None:
    result = scc_analysis(
        recursive_derivation(),
        bounds=DerivationQueryBounds(max_visited_refs=1),
    )
    assert result["status"] == "truncated"
    assert not result["complete"]
    assert result["result"]["components"] == []
    assert result["truncations"][0]["dimension"] == "maxVisitedRefs"

    edge_limited = scc_analysis(
        recursive_derivation(),
        bounds=DerivationQueryBounds(max_premise_slots=1),
    )
    assert edge_limited["status"] == "truncated"
    assert edge_limited["result"]["components"] == []
    assert edge_limited["truncations"][0]["dimension"] == "maxPremiseSlots"


def test_scc_output_limit_returns_only_a_digest_bearing_header() -> None:
    result = scc_analysis(
        recursive_derivation(), bounds=DerivationQueryBounds(max_output_bytes=1_200)
    )
    assert result["status"] == "unknown"
    assert result["result"] is None
    assert result["truncations"][0]["dimension"] == "maxOutputBytes"
    assert result["truncations"][0]["omittedDigest"].startswith("sha256:")
    assert any("fixed-point semantics" in row for row in result["nonclaims"])


def test_singleton_self_loop_is_an_explicit_recursive_component() -> None:
    artifact = recursive_derivation()
    statement_a = ref("statement", "A")
    artifact["payload"]["steps"] = [artifact["payload"]["steps"][0]]  # type: ignore[index]
    artifact["payload"]["steps"][0]["premiseRefs"] = [statement_a]  # type: ignore[index]
    component = artifact["payload"]["recursion"]["components"][0]  # type: ignore[index]
    component["componentId"] = "scc:a"
    component["statementRefs"] = [statement_a]
    artifact["artifactId"] = detached_content_id(artifact)

    result = scc_analysis(artifact)
    assert result["result"]["components"] == [
        {
            "componentId": "scc:a",
            "semantics": "declared-recursive-fixed-point",
            "statementRefs": [statement_a],
            "internalEdges": [{"fromRef": statement_a, "toRef": statement_a}],
        }
    ]


def test_acyclic_scc_analysis_is_explicitly_not_recursive() -> None:
    result = scc_analysis(derivation_artifact())
    assert result["status"] == "not-recursive"
    assert result["complete"]
    assert result["result"] == {"recursive": False, "components": []}


@pytest.mark.parametrize("factory", [plan_artifact, attempt_log_artifact])
def test_non_derivation_artifacts_cannot_enter_scc_analysis(
    factory: Callable[[], dict[str, Any]],
) -> None:
    result = scc_analysis(factory())
    assert result["status"] == "invalid"
    assert result["result"] is None
    assert result["diagnostics"][0]["code"] == "unexpected-artifact-kind"


@pytest.mark.parametrize("available", [[], [ref("statement", "A")]])
def test_recursive_cycle_is_never_promoted_to_structural_satisfaction(
    available: list[dict[str, str]],
) -> None:
    result = proofir_derivation.structural_satisfaction(
        recursive_derivation(), ref("statement", "A"), available_refs=available
    )
    assert result["status"] == "invalid"
    assert result["checkerAcceptance"] == "not-evaluated"
    assert result["result"] is None
    assert result["diagnostics"][0]["code"] == "recursive-satisfaction-unsupported"
