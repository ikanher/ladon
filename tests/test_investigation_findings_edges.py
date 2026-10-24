"""Adversarial aggregation, history and source-custody reporting contracts."""

import copy

import pytest
from test_correspondence_investigation_v3 import input_bundle, response
from test_investigation_findings import NOW, observation_case, review_observation

from ladon.investigation import assess
from ladon.investigation_correspondence import (
    attach_bundle,
    challenge_packet_v3,
    ingest_response,
    initialize_v3,
)
from ladon.investigation_reporting import aggregate_report


def native_case(tmp_path, classification="mismatch", reviewer="reviewer-a", method="different"):
    source, bundle = input_bundle(tmp_path)
    plan = attach_bundle(initialize_v3(source, tmp_path), bundle, tmp_path)
    packet = challenge_packet_v3(plan, plan["correspondenceBundles"][0]["subject"], tmp_path)
    first = {**response(packet, classification), "reviewer": reviewer, "method": method}
    return plan, packet, first


def test_native_corrected_difference_remains_in_history(tmp_path):
    plan, packet, first = native_case(tmp_path)
    reviewed = ingest_response(plan, packet, first, tmp_path)
    first_id = reviewed["responses"][0]["responseId"]
    corrected = ingest_response(reviewed, packet, {**first, "classification": "aligned", "method": "same"},
                                tmp_path, first=first_id)
    finding = next(f for f in assess(corrected, tmp_path)["findings"] if f.get("subject") == first["subject"])
    assert finding["statementRelation"] == "aligned"
    assert finding["responses"][0]["classification"] == "mismatch"
    assert finding["formalSupport"] == "not-established"


def test_report_exposes_native_conflicting_reviews_across_branches(tmp_path):
    plan, packet, first = native_case(tmp_path)
    a = ingest_response(plan, packet, first, tmp_path)
    b = ingest_response(plan, packet, {**first, "reviewer": "reviewer-b", "classification": "aligned",
                                     "method": "same"}, tmp_path)
    report = aggregate_report([a, b], tmp_path)
    assert any(f.get("statementRelation") == "conflicted" for f in report["findings"])


def test_report_rejects_native_first_response_fork(tmp_path):
    plan, packet, first = native_case(tmp_path)
    a = ingest_response(plan, packet, first, tmp_path)
    b = ingest_response(plan, packet, {**first, "classification": "aligned"}, tmp_path)
    with pytest.raises(ValueError, match="immutable first"):
        aggregate_report([a, b], tmp_path)


def test_native_correction_cannot_change_reviewer(tmp_path):
    plan, packet, first = native_case(tmp_path)
    reviewed = ingest_response(plan, packet, first, tmp_path)
    with pytest.raises(ValueError, match="reviewer"):
        ingest_response(reviewed, packet, {**first, "reviewer": "new-reviewer"}, tmp_path,
                        first=reviewed["responses"][0]["responseId"])


def test_report_pending_branch_keeps_uncertain_summary(tmp_path):
    _, pending = observation_case(tmp_path)
    reviewed, _, _ = review_observation(pending, tmp_path)
    report = aggregate_report([pending, reviewed], tmp_path, now=NOW)
    finding = report["findings"][0]
    assert finding["statementRelation"] in {"unresolved", "conflicted"}
    assert finding["pendingPlanIds"]


@pytest.mark.parametrize("change", ["quote", "formal-source", "response"])
def test_observation_custody_rejects_tampering(tmp_path, change):
    from ladon.proof_slice import digest

    original, captured = observation_case(tmp_path)
    if change == "response":
        plan, _, _ = review_observation(captured, tmp_path)
        plan["observations"][0]["responses"][0]["evidence"] = "Mutated response."
    else:
        record = copy.deepcopy(captured["observations"][0]["record"])
        if change == "quote":
            record["source"]["quote"] = "Wrong passage."
        else:
            record["formalSources"] = [{**original["scope"], "statement": "Wrong formal statement."}]
        plan = copy.deepcopy(original)
        plan["observations"] = [{"observationId": digest(record), "record": record,
                                 "responses": [], "reconciliations": []}]
    with pytest.raises(ValueError):
        assess(plan, tmp_path, now=NOW)


def test_observation_count_bound(tmp_path):
    _, plan = observation_case(tmp_path)
    plan["observations"] *= 4097
    with pytest.raises(ValueError, match="bound"):
        assess(plan, tmp_path, now=NOW)


def test_report_input_bounds(tmp_path, monkeypatch):
    import ladon.investigation_reporting as reporting

    _, plan = observation_case(tmp_path)
    with pytest.raises(ValueError, match="1..16"):
        aggregate_report([plan] * 17, tmp_path, now=NOW)
    monkeypatch.setattr(reporting, "MAX_REPORT_BYTES", 1)
    with pytest.raises(ValueError, match="128 MiB"):
        aggregate_report([plan], tmp_path, now=NOW)
