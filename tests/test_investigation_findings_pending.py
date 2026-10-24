"""Report pending provenance follows the actual queue across every review dimension."""

import pytest
from test_investigation_findings import NOW, observation_case, review_observation

from ladon.investigation import assess
from ladon.investigation_observations import ingest_observation_response
from ladon.investigation_reporting import aggregate_report


@pytest.mark.parametrize("change", ["method", "sourceFidelity", "classification"])
def test_pending_review_dimension_is_not_hidden(tmp_path, change):
    _, captured = observation_case(tmp_path)
    resolved, packet, response = review_observation(captured, tmp_path, "aligned", "reviewer-a", "same")
    unresolved = {**response, "reviewer": "reviewer-b", change: "unresolved"}
    pending = ingest_observation_response(captured, packet, unresolved, tmp_path)
    assert assess(pending, tmp_path, now=NOW)["next"]
    report = aggregate_report([pending, resolved], tmp_path, now=NOW)
    finding = report["findings"][0]
    assert len(finding["pendingPlanIds"]) == 1
    assert finding["pendingPlanIds"][0] == report["branches"][0]["planId"]
