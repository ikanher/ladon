from __future__ import annotations

from typing import Any

import pytest

from ladon import proofir_derivation
from ladon.proofir_v3 import make_envelope


class MissingDerivationQueryBounds:
    def __init__(self, **_: object) -> None:
        raise AssertionError("DerivationQueryBounds is missing")


DerivationQueryBounds = getattr(
    proofir_derivation, "DerivationQueryBounds", MissingDerivationQueryBounds
)


def query(name: str, *args: object, **kwargs: object) -> dict[str, Any]:
    implementation = getattr(proofir_derivation, name, None)
    assert implementation is not None, f"{name} is missing"
    return implementation(*args, **kwargs)


def navigation_path(*args: object, **kwargs: object) -> dict[str, Any]:
    return query("navigation_path", *args, **kwargs)


def complete_derivation_slice(*args: object, **kwargs: object) -> dict[str, Any]:
    return query("complete_derivation_slice", *args, **kwargs)


def structural_satisfaction(*args: object, **kwargs: object) -> dict[str, Any]:
    return query("structural_satisfaction", *args, **kwargs)


def analyze_alternatives(*args: object, **kwargs: object) -> dict[str, Any]:
    return query("analyze_alternatives", *args, **kwargs)


ENVIRONMENT = "sha256:" + "e" * 64
FOREIGN_ARTIFACT = "sha256:" + "f" * 64


def ref(kind: str, local_id: str) -> dict[str, str]:
    return {"kind": kind, "localId": local_id}


def derivation(
    rows: list[tuple[str, list[str], str]],
) -> object:
    statements = sorted(
        {
            statement
            for _, premises, conclusion in rows
            for statement in [*premises, conclusion]
        }
    )
    subjects = [ref("statement", statement) for statement in statements]
    subjects.extend(ref("derivation-step", step) for step, _, _ in rows)
    rule = ref("declaration", "rule")
    context = ref("local-context", "context")
    check = ref("check-run", "check")
    subjects.extend((rule, context, check))
    steps: list[dict[str, Any]] = []
    for step, premises, conclusion in rows:
        steps.append(
            {
                "stepRef": ref("derivation-step", step),
                "kind": "theorem-application",
                "ruleRef": rule,
                "premiseRefs": [ref("statement", premise) for premise in premises],
                "conclusionRef": ref("statement", conclusion),
                "substitutions": [],
                "localContextRef": context,
                "checkRunRef": check,
            }
        )
    return make_envelope(
        artifact_kind="proofir.derivation",
        producer={"name": "test", "version": "1"},
        environment_ref=ENVIRONMENT,
        subject_refs=subjects,
        coverage={"status": "complete", "observed": len(subjects)},
        payload={"derivationId": "derivation:test", "acyclic": True, "steps": steps},
    )


def assert_common(result: dict[str, Any], query_kind: str, artifact: Any) -> None:
    assert result["queryVersion"] == "1"
    assert result["queryKind"] == query_kind
    assert result["environmentRef"] == ENVIRONMENT
    assert result["ownerArtifactId"] == artifact.content_id
    assert result["checkerAcceptance"] == "not-evaluated"
    assert result["nonclaims"]
    assert result["boundsApplied"]
    assert result["counters"]
    assert isinstance(result["truncations"], list)


def test_navigation_is_a_linear_route_with_sibling_requirements() -> None:
    artifact = derivation([("step:ab", ["A", "B"], "G")])
    result = navigation_path(artifact, ref("statement", "A"), ref("statement", "G"))
    assert_common(result, "navigation-path", artifact)
    assert result["status"] == "found"
    assert result["result"]["path"] == [
        {
            "statementRef": ref("statement", "A"),
            "viaStepRef": ref("derivation-step", "step:ab"),
            "viaPremiseOrdinal": 0,
        },
        {
            "statementRef": ref("statement", "G"),
            "viaStepRef": None,
            "viaPremiseOrdinal": None,
        },
    ]
    assert result["result"]["requirements"] == [
        {
            "stepRef": ref("derivation-step", "step:ab"),
            "chosenPremiseOrdinal": 0,
            "siblingPremiseOccurrences": [{"ordinal": 1, "ref": ref("statement", "B")}],
        }
    ]


def test_complete_slice_selects_one_or_branch_and_all_and_slots() -> None:
    artifact = derivation([("step:b", ["B"], "G"), ("step:a", ["A", "A"], "G")])
    result = complete_derivation_slice(
        artifact,
        ref("statement", "G"),
        available_refs=[ref("statement", "A")],
        selection={"G": ref("derivation-step", "step:a")},
    )
    assert_common(result, "complete-derivation-slice", artifact)
    assert result["status"] == "complete"
    assert result["result"]["structurallyClosed"]
    assert result["result"]["selections"] == [
        {
            "conclusionRef": ref("statement", "G"),
            "stepRef": ref("derivation-step", "step:a"),
        }
    ]
    assert result["result"]["premiseOccurrences"] == [
        {
            "stepRef": ref("derivation-step", "step:a"),
            "ordinal": 0,
            "ref": ref("statement", "A"),
        },
        {
            "stepRef": ref("derivation-step", "step:a"),
            "ordinal": 1,
            "ref": ref("statement", "A"),
        },
    ]
    assert result["result"]["unselectedAlternatives"] == [
        {
            "conclusionRef": ref("statement", "G"),
            "stepRefs": [ref("derivation-step", "step:b")],
        }
    ]


def test_satisfaction_is_deterministic_and_has_no_failed_or_residual_leak() -> None:
    artifact = derivation([("step:b", ["B"], "G"), ("step:a", ["A"], "G")])
    result = structural_satisfaction(
        artifact,
        ref("statement", "G"),
        available_refs=[ref("statement", "B")],
    )
    assert_common(result, "structural-satisfaction", artifact)
    assert result["status"] == "true"
    assert result["result"]["selectedStepRef"] == ref("derivation-step", "step:b")
    assert result["result"]["selectionFinal"]
    assert result["result"]["witnessResidualOccurrences"] == []
    assert result["result"]["alternativeFailures"] == [
        {
            "stepRef": ref("derivation-step", "step:a"),
            "status": "false",
            "residualOccurrences": [{"ordinal": 0, "ref": ref("statement", "A")}],
        }
    ]


def test_alternatives_remain_separate_and_sorted_by_step_identity() -> None:
    artifact = derivation([("step:b", ["B"], "G"), ("step:a", ["A"], "G")])
    result = analyze_alternatives(
        artifact,
        ref("statement", "G"),
        available_refs=[ref("statement", "B")],
    )
    assert_common(result, "alternative-analysis", artifact)
    assert result["status"] == "complete"
    rows = result["result"]["rows"]
    assert [row["stepRef"]["localId"] for row in rows] == ["step:a", "step:b"]
    assert rows[0]["structuralStatus"] == "false"
    assert rows[0]["residualOccurrences"] == [
        {"ordinal": 0, "ref": ref("statement", "A")}
    ]
    assert rows[1]["structuralStatus"] == "true"
    assert rows[1]["residualOccurrences"] == []
    assert result["result"]["selectedStepRef"] == ref("derivation-step", "step:b")


def test_external_owner_is_not_treated_as_an_artifact_local_reference() -> None:
    artifact = derivation([("step:a", ["A"], "G")])
    result = structural_satisfaction(
        artifact,
        ref("statement", "G"),
        available_refs=[
            {
                "artifactRef": FOREIGN_ARTIFACT,
                "kind": "statement",
                "localId": "A",
            }
        ],
    )
    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == "external-reference-not-local"
    assert result["result"] is None


def test_bounds_return_unknown_not_false_or_partial_success() -> None:
    artifact = derivation([("step:a", ["A"], "G"), ("step:seed", ["Seed"], "A")])
    result = structural_satisfaction(
        artifact,
        ref("statement", "G"),
        available_refs=[ref("statement", "Seed")],
        bounds=DerivationQueryBounds(max_depth=1),
    )
    assert result["status"] == "unknown"
    assert not result["complete"]
    assert result["truncations"][0]["dimension"] == "maxDepth"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_depth": 0},
        {"max_visited_refs": -1},
        {"max_evaluated_steps": True},
        {"max_output_bytes": 1},
    ],
)
def test_invalid_bounds_are_rejected_deterministically(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="bound"):
        DerivationQueryBounds(**kwargs)  # type: ignore[arg-type]
