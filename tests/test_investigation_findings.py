"""Source-bound findings retain attributed differences without mathematical verdicts."""

import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ladon.investigation import assess, initialize
from ladon.investigation_finalization import progress_receipt, validate_progress_receipt

FIXTURES = Path(__file__).parent / "fixtures/investigation_findings"
NOW = datetime(2026, 10, 17, 19, 1, tzinfo=UTC)


def legacy(tmp_path, version=1):
    plan = json.loads((FIXTURES / "legacy-plan.json").read_text())
    (tmp_path / "source.txt").write_bytes((FIXTURES / "source.txt").read_bytes())
    plan["version"] = version
    return plan


def observation_case(tmp_path, version=3):
    from ladon.investigation_observations import record_observation

    original = legacy(tmp_path)
    plan = initialize(tmp_path / "source.txt", tmp_path, now=NOW - timedelta(minutes=1),
                      correspondence=version == 3, derivations=version == 2)
    plan["units"][0].update(inventory="done", note="Attributed survey, not exhaustive argument review.")
    record = {"schema": "ladon-investigation-observation-v1", "id": "different-bound",
              "source": {**plan["scope"], "quote": original["claims"][0]["quote"]},
              "author": "source-reader", "assertion": "The displayed bound has no extra parameter.",
              "comparison": "A selected formal bound has an extra parameter.",
              "evidence": "No transfer eliminating the parameter was supplied.",
              "formalSources": [], "dependencies": "The original stated assumptions only."}
    captured = record_observation(plan, record, tmp_path)
    return plan, captured


def review_observation(plan, root, classification="mismatch", reviewer="reviewer-a", method="different"):
    from ladon.investigation_observations import challenge_observation, ingest_observation_response

    subject = plan["observations"][0]["observationId"]
    packet = challenge_observation(plan, subject, root)
    response = {"reviewer": reviewer, "subject": subject, "challengeDigest": packet["challengeDigest"],
                "classification": classification, "method": method, "sourceFidelity": "faithful",
                "evidence": "Source and selected formal guarantee were independently compared."}
    return ingest_observation_response(plan, packet, response, root), packet, response


@pytest.mark.parametrize("version", [1, 2])
def test_legacy_findings_survive_status_and_receipt(tmp_path, version):
    plan = legacy(tmp_path, version)
    result = assess(plan, tmp_path, now=NOW)
    finding = next(f for f in result["findings"] if f.get("statementRelation") == "mismatch")
    assert finding["methodRelation"] == "different"
    assert finding["mathematicalFalsity"] == "not-established"
    assert finding["source"]["quote"] == plan["claims"][0]["quote"]
    receipt, saved = progress_receipt(plan, tmp_path, now=NOW)
    assert saved and finding in receipt["findings"]
    assert validate_progress_receipt(receipt, plan, tmp_path) == receipt


def test_same_method_control_and_survey_boundary(tmp_path):
    plan = legacy(tmp_path)
    plan["claims"][0]["judgment"].update(statement="aligned", method="same")
    assert assess(plan, tmp_path, now=NOW)["findings"] == []
    plan["claims"] = []
    coverage = assess(plan, tmp_path, now=NOW)["coverage"]
    assert coverage["surveyedUnits"] == 1
    assert coverage["reviewedClaims"] == 0
    assert coverage["wholePaperCertified"] is False


def test_frozen_historical_receipt_stays_verifiable(tmp_path):
    plan = legacy(tmp_path)
    receipt = json.loads((FIXTURES / "legacy-receipt.json").read_text())
    assert receipt["schema"] == "ladon-investigation-progress-v1"
    assert validate_progress_receipt(receipt, plan, tmp_path) == receipt
    (tmp_path / "source.txt").write_text("Changed source.\n")
    with pytest.raises(ValueError, match="stale"):
        validate_progress_receipt(receipt, plan, tmp_path)


@pytest.mark.parametrize("version", [1, 2, 3])
def test_observation_capture_review_and_formal_gap(tmp_path, version):
    from ladon.investigation_observations import inspect_observations

    original, plan = observation_case(tmp_path, version)
    assert "observations" not in original
    pending = assess(plan, tmp_path, now=NOW)
    assert any(w["kind"] == "independent-observation-review" for w in pending["next"])
    reviewed, packet, _ = review_observation(plan, tmp_path)
    assert "comparison" not in packet and "evidence" not in packet
    assert "responses" not in packet
    assert inspect_observations(reviewed, tmp_path)[0]["record"] == plan["observations"][0]["record"]
    finding = _assert_reviewed_observation(reviewed, tmp_path, version)
    _assert_observation_receipt(reviewed, tmp_path, finding)


def _assert_reviewed_observation(reviewed, tmp_path, version):
    status = assess(reviewed, tmp_path, now=NOW)
    finding = next(f for f in status["findings"] if f.get("kind") == "observation")
    assert finding["statementRelation"] == "mismatch"
    assert finding["formalSupport"] == "not-established"
    assert finding["mathematicalFalsity"] == "not-established"
    if version == 3:
        assert status["formalCorrespondence"] == "incomplete-no-counterpart"
    return finding


def _assert_observation_receipt(reviewed, tmp_path, finding):
    receipt, saved = progress_receipt(reviewed, tmp_path, finalize=True, now=NOW)
    assert saved and receipt["terminal"]
    assert finding in receipt["findings"]


def test_observation_conflict_preserves_firsts_and_correction(tmp_path):
    from ladon.investigation_observations import ingest_observation_response

    _, plan = observation_case(tmp_path)
    first, packet, response = review_observation(plan, tmp_path)
    original = copy.deepcopy(first["observations"][0]["responses"][0])
    conflicted, _, _ = review_observation(first, tmp_path, "aligned", "reviewer-b", "same")
    status = assess(conflicted, tmp_path, now=NOW)
    assert status["next"]
    assert any(f.get("statementRelation") == "conflicted" for f in status["findings"])
    correction = {**response, "classification": "aligned", "method": "same"}
    fixed = ingest_observation_response(conflicted, packet, correction, tmp_path,
                                        first=original["responseId"])
    assert fixed["observations"][0]["responses"][0] == original
    assert fixed["observations"][0]["reconciliations"][0]["firstResponseId"] == original["responseId"]
    with pytest.raises(ValueError, match="reviewer|attribution"):
        ingest_observation_response(conflicted, packet, {**correction, "reviewer": "reviewer-b"},
                                    tmp_path, first=original["responseId"])


def test_stale_or_mutated_observation_rejects(tmp_path):
    from ladon.investigation_observations import inspect_observations

    _, plan = observation_case(tmp_path)
    changed = copy.deepcopy(plan)
    changed["observations"][0]["record"]["comparison"] = "Changed claim."
    with pytest.raises(ValueError):
        inspect_observations(changed, tmp_path)
    (tmp_path / "source.txt").write_text("Changed source.\n")
    with pytest.raises(ValueError, match="stale"):
        assess(plan, tmp_path, now=NOW)


def test_report_preserves_supplementary_observations_and_clock(tmp_path):
    from ladon.investigation_observations import record_observation
    from ladon.investigation_reporting import aggregate_report

    _, first = observation_case(tmp_path)
    reviewed, _, _ = review_observation(first, tmp_path)
    record = copy.deepcopy(first["observations"][0]["record"])
    record.update(id="second-observation", assertion="Another intermediate statement.")
    second = record_observation(reviewed, record, tmp_path)
    report = aggregate_report([reviewed, second, reviewed], tmp_path, now=NOW)
    assert len(report["observations"]) == 2
    assert report["startedAt"] == first["startedAt"]
    assert report["budgetSeconds"] == first["budgetSeconds"]
    assert len(report["planIds"]) == 2
    assert report["mathematicalFalsity"] == "not-established"
    assert report["branches"] and any(b["next"] for b in report["branches"])


@pytest.mark.parametrize("field", ["startedAt", "budgetSeconds", "scope"])
def test_report_rejects_incompatible_branch(tmp_path, field):
    from ladon.investigation_reporting import aggregate_report

    _, plan = observation_case(tmp_path)
    other = copy.deepcopy(plan)
    if field == "startedAt":
        other[field] = (NOW - timedelta(seconds=10)).isoformat()
    elif field == "budgetSeconds":
        other[field] += 1
    else:
        other[field]["endLine"] += 1
    with pytest.raises(ValueError):
        aggregate_report([plan, other], tmp_path, now=NOW)


def test_report_keeps_cross_branch_conflicts(tmp_path):
    from ladon.investigation_reporting import aggregate_report

    _, plan = observation_case(tmp_path)
    a, _, _ = review_observation(plan, tmp_path)
    b, _, _ = review_observation(plan, tmp_path, "aligned", "reviewer-b", "same")
    report = aggregate_report([a, b], tmp_path, now=NOW)
    assert any(f.get("statementRelation") == "conflicted" for f in report["findings"])
    assert len(report["observations"]) == 1


def test_native_first_response_classification_survives(tmp_path):
    from test_correspondence_investigation_v3 import input_bundle, response

    from ladon.investigation_correspondence import (
        attach_bundle,
        challenge_packet_v3,
        ingest_response,
        initialize_v3,
    )

    source, bundle = input_bundle(tmp_path)
    plan = attach_bundle(initialize_v3(source, tmp_path), bundle, tmp_path)
    packet = challenge_packet_v3(plan, plan["correspondenceBundles"][0]["subject"], tmp_path)
    reviewed = ingest_response(plan, packet, response(packet, "mismatch"), tmp_path)
    finding = next(f for f in assess(reviewed, tmp_path)["findings"]
                   if f.get("statementRelation") == "mismatch")
    assert finding["methodRelation"] == "different"
    assert finding["responses"][0]["responseId"] == reviewed["responses"][0]["responseId"]
    assert finding["mathematicalFalsity"] == "not-established"
