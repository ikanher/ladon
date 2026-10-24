"""Scratch contract tests for native contract evidence on investigation findings.

The native fixture is a real propagation artifact and closed ProofIR batch; it is
conditional child evidence, not a source-fidelity or mathematical-truth claim.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from test_investigation_findings import (
    NOW,
    observation_case,
    review_observation,
)

EVIDENCE = (Path(__file__).resolve().parents[1] / "openspec/changes/"
            "ladon-proof-contract-analysis-umbrella/evidence/finding-projection-20261020")


def _native_attachment():
    from test_proof_contract_propagation_native import artifact, inputs

    graph, contracts, request = inputs()
    analysis = artifact(graph, contracts, request)
    return {"artifact": analysis, "context": {"artifacts": [graph, *contracts, analysis]}}


def _contract_observation(tmp_path, attachment=None):
    from ladon.investigation_observations import record_observation

    _, base = observation_case(tmp_path)
    record = copy.deepcopy(base["observations"][0]["record"])
    record["schema"] = "ladon-investigation-observation-v2"
    record["contractAnalysis"] = copy.deepcopy(attachment or _native_attachment())
    base.pop("observations")
    return record_observation(base, record, tmp_path)


def test_native_attachment_projects_through_status_inspection_report_and_final_receipt(tmp_path, capsys):
    from ladon.investigation import assess
    from ladon.investigation_finalization import progress_receipt, validate_progress_receipt
    from ladon.investigation_observations import inspect_observations
    from ladon.investigation_reporting import aggregate_report

    pending = _contract_observation(tmp_path)
    reviewed, packet, _ = review_observation(pending, tmp_path)
    attachment = pending["observations"][0]["record"]["contractAnalysis"]
    _assert_challenge_and_inspection(packet, reviewed, attachment, tmp_path, inspect_observations)
    _assert_inspection_cli_v2(reviewed, attachment, tmp_path, capsys)

    status = assess(reviewed, tmp_path, now=NOW)
    finding = next(row for row in status["findings"] if row.get("projectionSchema") ==
                   "ladon-investigation-contract-finding-v1")
    _assert_reviewed_finding(finding, attachment)

    report = aggregate_report([reviewed], tmp_path, now=NOW)
    _assert_contract_report(report, reviewed, finding, attachment)

    receipt, saved = progress_receipt(reviewed, tmp_path, finalize=True, now=NOW)
    _assert_contract_receipt(receipt, saved, reviewed, attachment, tmp_path,
                             validate_progress_receipt)


def _assert_inspection_cli_v2(reviewed, attachment, root, capsys):
    from ladon.investigation_cli import investigation_main

    plan_path = root / "contract-observation-plan.json"
    plan_path.write_text(json.dumps(reviewed, sort_keys=True) + "\n")
    code = investigation_main(["inspect-observations", "--plan", str(plan_path),
                               "--root", str(root)])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["schema"] == "ladon-investigation-observations-v2"
    assert payload["observations"][0]["record"]["contractAnalysis"] == attachment


def _assert_challenge_and_inspection(packet, reviewed, attachment, root, inspect):
    assert packet["schema"] == "ladon-investigation-observation-challenge-v2"
    assert packet["contractAnalysis"] == attachment
    assert "comparison" not in packet and "evidence" not in packet and "responses" not in packet
    assert packet["challengeDigest"]
    assert inspect(reviewed, root)[0]["record"]["contractAnalysis"] == attachment


def _assert_reviewed_finding(finding, attachment):
    _assert_contract_dimensions(finding, attachment)
    assert finding["statementRelation"] == "mismatch"
    assert finding["methodRelation"] == "different"
    assert finding["formalSupport"] == "not-established"
    assert finding["mathematicalFalsity"] == "not-established"


def _assert_contract_report(report, reviewed, finding, attachment):
    from ladon.proof_slice import digest

    assert report["schema"] == "ladon-investigation-report-v2"
    assert digest(reviewed) in report["planIds"]
    assert report["branches"][0]["planId"] == digest(reviewed)
    projected = next(row for row in report["findings"] if row["findingId"] == finding["findingId"])
    _assert_contract_dimensions(projected, attachment)
    _assert_report_boundary(report)


def _assert_report_boundary(report):
    assert report["mathematicalFalsity"] == "not-established"
    assert report["wholePaperCertified"] is False
    assert "bounded native" in report["authority"].lower()
    nonclaims = " ".join(report["nonclaims"]).lower()
    assert "whole-paper" in nonclaims and "source interpretation" in nonclaims
    assert "no semantic comparison" not in report["authority"].lower()


def _assert_contract_receipt(receipt, saved, reviewed, attachment, root, validate):
    from ladon.proof_slice import digest

    assert saved and receipt["schema"] == "ladon-investigation-progress-v3"
    assert receipt["planId"] == digest(reviewed)
    projected = next(row for row in receipt["findings"] if row.get("projectionSchema") ==
                     "ladon-investigation-contract-finding-v1")
    _assert_contract_dimensions(projected, attachment)
    assert validate(receipt, reviewed, root) == receipt


def _assert_contract_dimensions(finding, attachment):
    dims = finding["contractDimensions"]
    assert set(dims) == {"sourceFidelity", "extractionCompleteness", "routeSupport",
                         "mathematicalFalsity", "methodCorrespondence", "exploredPopulation"}
    assert dims["sourceFidelity"] == "faithful"
    assert dims["extractionCompleteness"] == "not-established"
    assert dims["routeSupport"] == "not-established"
    assert dims["mathematicalFalsity"] == "not-established"
    assert dims["methodCorrespondence"] == "different"
    assert dims["exploredPopulation"] == {
        "coverage": attachment["artifact"]["coverage"],
        "authority": "declared-child-coverage-only",
    }
    assert finding["contractAnalysis"] == attachment


def test_challenge_omission_or_mutation_of_attachment_is_rejected(tmp_path):
    from ladon.investigation_observations import ingest_observation_response

    pending = _contract_observation(tmp_path)
    reviewed, packet, response = review_observation(pending, tmp_path)
    omitted = copy.deepcopy(packet)
    omitted.pop("contractAnalysis")
    with pytest.raises(ValueError, match="challenge|binding|altered"):
        ingest_observation_response(pending, omitted, response, tmp_path)

    changed = copy.deepcopy(packet)
    changed["contractAnalysis"]["artifact"]["payload"]["analysisId"] = "changed"
    with pytest.raises(ValueError, match="challenge|binding|altered"):
        ingest_observation_response(pending, changed, response, tmp_path)
    assert reviewed["observations"][0]["record"]["contractAnalysis"] == \
        pending["observations"][0]["record"]["contractAnalysis"]


@pytest.mark.parametrize("mutation", ["wrong-kind", "dangling-context", "altered-identity", "altered-record"])
def test_invalid_or_non_closed_contract_analysis_is_rejected(tmp_path, mutation):
    from ladon.investigation_observations import inspect_observations
    from ladon.proof_slice import digest

    plan = _contract_observation(tmp_path)
    entry = plan["observations"][0]
    if mutation == "wrong-kind":
        entry["record"]["contractAnalysis"]["artifact"]["artifactKind"] = "proofir.derivation"
    elif mutation == "dangling-context":
        entry["record"]["contractAnalysis"]["context"]["artifacts"] = [
            entry["record"]["contractAnalysis"]["artifact"]]
    elif mutation == "altered-identity":
        entry["record"]["contractAnalysis"]["artifact"]["artifactId"] = "sha256:" + "0" * 64
    else:
        entry["record"]["comparison"] = "Altered after observation capture."
    # Rebind only invalid-artifact cases so native batch validation, rather than
    # the immutable observation digest, is the rejection point.
    if mutation != "altered-record":
        entry["observationId"] = digest(entry["record"])
    with pytest.raises((ValueError, TypeError)):
        inspect_observations(plan, tmp_path)


def test_stale_source_rejects_native_attachment_status_and_report(tmp_path):
    from ladon.investigation import assess
    from ladon.investigation_reporting import aggregate_report

    plan = _contract_observation(tmp_path)
    reviewed, _, _ = review_observation(plan, tmp_path)
    (tmp_path / "source.txt").write_text("Changed source bytes.\n")
    with pytest.raises(ValueError, match="stale"):
        assess(reviewed, tmp_path, now=NOW)
    with pytest.raises(ValueError, match="stale"):
        aggregate_report([reviewed], tmp_path, now=NOW)


def test_effective_reviewer_union_keeps_branch_disagreement_and_pending(tmp_path):
    from ladon.investigation_reporting import aggregate_report

    mismatch, disagreement, pending, attachment = _contract_branches(tmp_path)
    all_reviewed = aggregate_report([mismatch, disagreement], tmp_path, now=NOW)
    reviewed_finding = _contract_finding(all_reviewed)
    _assert_all_reviewed_union(reviewed_finding)

    report = aggregate_report([mismatch, disagreement, pending], tmp_path, now=NOW)
    _assert_pending_union(_contract_finding(report), attachment)


def _contract_branches(root):
    from ladon.investigation_observations import record_observation

    _, pending = observation_case(root)
    attachment = _native_attachment()
    record = copy.deepcopy(pending["observations"][0]["record"])
    record.update(schema="ladon-investigation-observation-v2", contractAnalysis=attachment)
    pending.pop("observations")
    pending = record_observation(pending, record, root)
    mismatch, _, _ = review_observation(pending, root, "mismatch", "reviewer-a", "different")
    disagreement, _, _ = review_observation(pending, root, "aligned", "reviewer-b", "same")
    return mismatch, disagreement, pending, attachment


def _contract_finding(report):
    return next(row for row in report["findings"] if row.get("projectionSchema") ==
                "ladon-investigation-contract-finding-v1")


def _assert_all_reviewed_union(finding):
    assert finding["contractDimensions"]["methodCorrespondence"] == "conflicted"
    assert not finding["pendingPlanIds"]
    assert {branch["finding"]["statementRelation"]
            for branch in finding["branchFindings"]} == {"mismatch", "aligned"}


def _assert_pending_union(finding, attachment):
    assert finding["statementRelation"] == "conflicted"
    assert finding["contractDimensions"]["methodCorrespondence"] == "conflicted"
    assert len(finding["branchFindings"]) == 3 and len(finding["planIds"]) == 3
    assert finding["pendingPlanIds"]
    assert {branch["finding"]["statementRelation"] for branch in finding["branchFindings"]} == {
        "mismatch", "aligned", "unresolved"}
    assert finding["contractAnalysis"] == attachment


def test_historical_v2_receipt_remains_byte_exact_and_new_attachment_cannot_downgrade(tmp_path):
    from ladon.investigation_finalization import (
        progress_receipt,
        validate_progress_receipt,
    )

    historical_plan = json.loads((EVIDENCE / "historical-v2-plan.json").read_text())
    historical_receipt = json.loads((EVIDENCE / "historical-v2-receipt.json").read_text())
    historical_root = EVIDENCE / "historical-source"
    assert validate_progress_receipt(historical_receipt, historical_plan, historical_root) == \
        historical_receipt

    plan = _contract_observation(tmp_path)
    reviewed, _, _ = review_observation(plan, tmp_path)
    receipt, saved = progress_receipt(reviewed, tmp_path, finalize=True, now=NOW)
    assert saved and receipt["schema"] == "ladon-investigation-progress-v3"
    from ladon.proof_slice import digest

    downgraded = copy.deepcopy(receipt)
    downgraded["schema"] = "ladon-investigation-progress-v2"
    downgraded["receiptId"] = digest({key: value for key, value in downgraded.items()
                                       if key != "receiptId"})
    with pytest.raises(ValueError, match="unsupported|downgrade|progress|matches"):
        validate_progress_receipt(downgraded, reviewed, tmp_path)


def test_first_response_and_reconciliation_are_preserved_for_contract_observation(tmp_path):
    from ladon.investigation import assess
    from ladon.investigation_observations import ingest_observation_response

    plan = _contract_observation(tmp_path)
    first_plan, packet, first_response = review_observation(plan, tmp_path)
    stored_first = copy.deepcopy(first_plan["observations"][0]["responses"][0])
    conflict, _, _ = review_observation(first_plan, tmp_path, "aligned", "reviewer-b", "same")
    assert any(row.get("statementRelation") == "conflicted"
               for row in assess(conflict, tmp_path, now=NOW)["findings"])

    correction = {**first_response, "classification": "aligned", "method": "same"}
    reconciled = ingest_observation_response(
        conflict, packet, correction, tmp_path, first=stored_first["responseId"])
    entry = reconciled["observations"][0]
    assert entry["responses"][0] == stored_first
    assert entry["reconciliations"][0]["firstResponseId"] == stored_first["responseId"]
    finding = next(row for row in assess(reconciled, tmp_path, now=NOW)["findings"]
                   if row.get("projectionSchema") ==
                   "ladon-investigation-contract-finding-v1")
    assert finding["responses"][0] == stored_first
    assert finding["reconciliations"][0]["firstResponseId"] == stored_first["responseId"]


def test_plain_observation_keeps_the_existing_report_and_finding_shape(tmp_path):
    from ladon.investigation_reporting import aggregate_report

    _, plan = observation_case(tmp_path)
    reviewed, _, _ = review_observation(plan, tmp_path)
    report = aggregate_report([reviewed], tmp_path, now=NOW)
    assert report["schema"] == "ladon-investigation-report-v1"
    finding = next(row for row in report["findings"] if row.get("kind") == "observation")
    assert "projectionSchema" not in finding
    assert "contractAnalysis" not in finding
    assert "contractDimensions" not in finding
