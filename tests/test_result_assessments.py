"""Assessments are attributed revision-scoped observations, not manifest authority."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon.result_assessments import assessment_currency, validate_result_assessments
from ladon.result_manifest_io import content_revision

FIXTURE = Path(__file__).parent / "fixtures/result_manifest/finite-map.json"


def manifest():
    return json.loads(FIXTURE.read_text())


def assessment(claim, component, *, targets=None, kind="source-correspondence"):
    target_ids = targets or []
    revisions = {row["id"]: row["revision"] for row in manifest()["targets"]}
    return {
        "id": f"assessment-{component}",
        "claimId": claim["id"],
        "componentId": component,
        "claimRevision": claim["revision"],
        "targetRevisions": [
            {"targetId": target_id, "revision": revisions[target_id]}
            for target_id in target_ids
        ],
        "kind": kind,
        "author": {"id": "reviewer-1", "kind": "human"},
        "basis": "reviewed against the supplied statement",
        "scope": "only this component",
        "differences": [],
        "evidenceRefs": ["review:example-1"],
    }


def companion(value, rows):
    return {
        "schema": "ladon-result-assessments-v1",
        "resultId": value["resultId"],
        "manifestRevision": value["revision"],
        "assessments": rows,
    }


def test_multiple_attributed_assessments_for_one_component_remain_distinct():
    value = manifest()
    claim = value["claims"][0]
    rows = [
        assessment(claim, "implication", targets=["finite-map"]),
        {**assessment(claim, "implication", targets=["finite-map"]),
         "id": "assessment-implication-2", "author": {"id": "model-7", "kind": "model"},
         "kind": "reported-implication-without-checked-adapter"},
    ]
    validated = validate_result_assessments(companion(value, rows), value)

    assert [row["id"] for row in validated["assessments"]] == [
        "assessment-implication", "assessment-implication-2"
    ]
    assert [assessment_currency(row, validated, value) for row in validated["assessments"]] == [
        "current", "current"
    ]


def test_unmapped_component_can_have_attributed_reason_without_target():
    value = manifest()
    claim = value["claims"][0]
    row = assessment(claim, "unrestricted-domain", kind="conventional-only")
    validated = validate_result_assessments(companion(value, [row]), value)

    assert validated["assessments"][0]["targetRevisions"] == []
    assert assessment_currency(validated["assessments"][0], validated, value) == "current"


def test_old_revision_assessment_is_retained_as_historical():
    value = manifest()
    claim = value["claims"][0]
    row = assessment(claim, "implication", targets=["finite-map"])
    attached = companion(value, [row])
    target = value["targets"][0]
    target["source"]["path"] = "Changed.lean"
    target["revision"] = content_revision("target", target)
    value["revision"] = content_revision("manifest", value)

    validated = validate_result_assessments(attached, value)
    assert assessment_currency(validated["assessments"][0], validated, value) == "historical"


def test_assessment_rejects_unknown_fields_and_wrong_component_target_set():
    value = manifest()
    claim = value["claims"][0]
    row = assessment(claim, "implication", targets=["finite-map"])
    with pytest.raises(ValueError):
        validate_result_assessments(companion(value, [{**row, "reviewed": True}]), value)

    row["targetRevisions"] = []
    with pytest.raises(ValueError):
        validate_result_assessments(companion(value, [row]), value)


def test_validator_returns_detached_snapshot():
    value = manifest()
    claim = value["claims"][0]
    supplied = companion(value, [assessment(claim, "unrestricted-domain", kind="unassessed")])
    validated = validate_result_assessments(supplied, value)
    validated["assessments"][0]["scope"] = "mutated"
    assert supplied["assessments"][0]["scope"] == "only this component"
