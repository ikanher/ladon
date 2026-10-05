"""Authority boundaries for stored ProofIR check observations in result inspection."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from support.semantic_evidence import semantic_evidence
from support.semantic_execution import with_execution_context

from ladon.evidence_receipt_readers import stored_check_receipt
from ladon.proofir_v3 import detached_content_id
from ladon.result_inspection import inspect_result_manifest
from ladon.result_manifest_io import ResultManifestError, content_revision

FIXTURE = Path(__file__).parent / "fixtures/result_manifest/finite-map.json"


def manifest():
    return json.loads(FIXTURE.read_text())


def seal(value):
    for target in value["targets"]:
        target["revision"] = content_revision("target", target)
    for claim in value["claims"]:
        claim["revision"] = content_revision("claim", claim)
    value["revision"] = content_revision("manifest", value)


def check_inputs(label="main", *, candidate=None):
    artifacts, _registry, _receipt = semantic_evidence(label, candidate=candidate)
    artifacts, _receipt = with_execution_context(artifacts, "explicit")
    return artifacts


def target_owned_by_check(value, artifacts, *, check_index=1):
    """Make the declared target point at one exact check-run subject owner."""
    check = artifacts[check_index]
    subject = next(row for row in check["subjectRefs"] if row["kind"] == "candidate-application")
    candidate = subject["searchShape"]["candidate"]
    target = value["targets"][0]
    target.update(
        name=candidate,
        typeText="True",
        subjectRef={"artifactId": check["artifactId"], "subjectId": subject["localId"]},
        environment={"toolchain": "leanprover/lean4:v4.fixture", "digest": check["environmentRef"]},
    )
    seal(value)


def check_row(result, artifact):
    return next(row for row in result["rows"] if row["artifactId"] == artifact["artifactId"])


def test_check_run_projects_existing_receipt_with_exact_owner_and_recorded_environment():
    value = manifest()
    artifacts = check_inputs()
    target_owned_by_check(value, artifacts)

    result = inspect_result_manifest(value, artifacts, section="checking")
    row = check_row(result, artifacts[1])

    assert row["artifactId"] == artifacts[1]["artifactId"]
    assert row["operation"] == artifacts[1]["payload"]["operation"]
    assert row["evidenceReceipt"] == stored_check_receipt(
        artifacts[1], environment_artifacts=artifacts[:1]
    )
    assert row["sourceFreshness"] == "not-assessed"
    assert any(binding["targetId"] == value["targets"][0]["id"] for binding in row["targetBindings"])


def test_matching_name_without_canonical_subject_ownership_is_unassociated():
    value = manifest()
    artifacts = check_inputs(candidate=value["targets"][0]["name"])
    # Keep the manifest's target subjectRef absent: a name match carries no ownership.

    result = inspect_result_manifest(value, artifacts, section="checking")
    row = check_row(result, artifacts[1])

    assert row["targetBindings"]
    assert all(binding["status"] == "unassociated" for binding in row["targetBindings"])


def test_exact_owner_with_stale_manifest_scope_is_reported_historical_or_mismatched():
    value = manifest()
    artifacts = check_inputs()
    target_owned_by_check(value, artifacts)
    value["targets"][0]["source"]["digest"] = "sha256:" + "0" * 64
    value["targets"][0]["typeText"] = "False"
    value["targets"][0]["environment"]["digest"] = "sha256:" + "1" * 64
    seal(value)

    result = inspect_result_manifest(value, artifacts, section="checking")
    row = check_row(result, artifacts[1])

    assert any(binding["status"] == "historical-or-mismatched" for binding in row["targetBindings"])


def test_same_name_check_with_different_artifact_owner_does_not_borrow_binding():
    value = manifest()
    owner = check_inputs("owner", candidate="Example.injective_surjective")
    other = check_inputs("other", candidate="Example.injective_surjective")
    target_owned_by_check(value, owner)

    result = inspect_result_manifest(value, owner + [other[1]], section="checking")
    other_row = check_row(result, other[1])

    assert other_row["targetBindings"]
    assert all(binding["status"] == "unassociated" for binding in other_row["targetBindings"])


def test_invalid_stored_receipt_fails_even_when_check_section_is_not_selected():
    value = manifest()
    artifacts = check_inputs()
    check = artifacts[1]
    check["extensions"]["ladon.process-observation/v1"]["evidenceReceipt"]["checkRunRef"] = "check:wrong-owner"
    check["artifactId"] = detached_content_id(check)

    with pytest.raises(ResultManifestError, match="receipt|owner|canonical"):
        inspect_result_manifest(value, artifacts, section="claims")


@pytest.mark.parametrize("operation", ["build", "replay"])
def test_absent_receipt_preserves_the_stored_check_payload_without_fresh_check_claim(operation):
    value = manifest()
    artifacts = check_inputs()
    target_owned_by_check(value, artifacts)
    check = artifacts[1]
    check["payload"]["operation"] = operation
    expected_payload = copy.deepcopy(check["payload"])
    check["extensions"]["ladon.process-observation/v1"].pop("evidenceReceipt")
    check["artifactId"] = detached_content_id(check)
    value["targets"][0]["subjectRef"]["artifactId"] = check["artifactId"]
    seal(value)

    result = inspect_result_manifest(value, artifacts, section="checking")
    row = check_row(result, check)

    assert row["evidenceReceipt"] is None
    assert row["operation"] == expected_payload["operation"]
    assert row["results"] == expected_payload["results"]
    assert row["guarantee"] == expected_payload["guarantee"]
    assert row["sourceFreshness"] == "not-assessed"


def test_accepted_zero_residual_application_remains_a_candidate_operation():
    value = manifest()
    artifacts, _registry, _receipt = semantic_evidence("zero-residual", status="accepted")
    artifacts, _receipt = with_execution_context(artifacts, "explicit")
    target_owned_by_check(value, artifacts)

    result = inspect_result_manifest(value, artifacts, section="checking")
    row = check_row(result, artifacts[1])

    assert row["operation"] == "exact-candidate-elaboration"
    assert row["evidenceReceipt"]["operationOutcome"] == "accepted"
    assert row["targetBindings"]
    assert not any("theorem replay" in str(binding).lower() for binding in row["targetBindings"])
