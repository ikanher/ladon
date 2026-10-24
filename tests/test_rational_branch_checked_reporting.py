"""End-to-end projection for a bounded checked rational-branch attachment."""
from __future__ import annotations

import copy

from test_investigation_contract_findings import (
    _assert_contract_dimensions,
    _assert_report_boundary,
    observation_case,
    review_observation,
)
from test_rational_branch_checked_artifact import _checked_batch


def test_checked_branch_artifact_survives_finding_report_and_receipt(
    monkeypatch, tmp_path
):
    from ladon.investigation import assess
    from ladon.investigation_reporting import aggregate_report

    batch = _checked_batch(monkeypatch)
    attachment = {
        "artifact": copy.deepcopy(batch[-1]),
        "context": {"artifacts": copy.deepcopy(batch[:-1])},
    }
    pending = _observation_with_id(tmp_path, attachment, "receipt-red-finding")
    reviewed, _packet, _response = review_observation(pending, tmp_path)

    status = assess(reviewed, tmp_path)
    finding = next(row for row in status["findings"]
                   if row.get("projectionSchema") == "ladon-investigation-contract-finding-v1")
    _assert_contract_dimensions(finding, attachment)

    report = aggregate_report([reviewed], tmp_path)
    projected = next(row for row in report["findings"]
                     if row["findingId"] == finding["findingId"])
    assert projected["contractAnalysis"] == attachment
    _assert_contract_dimensions(projected, attachment)
    _assert_report_boundary(report)

    _assert_final_receipt(reviewed, tmp_path, attachment)


def _assert_final_receipt(reviewed, tmp_path, attachment):
    from ladon.investigation_finalization import progress_receipt, validate_progress_receipt

    receipt, saved = progress_receipt(reviewed, tmp_path, finalize=True)
    assert saved
    retained = next(row for row in receipt["findings"]
                    if row.get("projectionSchema") == "ladon-investigation-contract-finding-v1")
    assert retained["contractAnalysis"] == attachment
    assert validate_progress_receipt(receipt, reviewed, tmp_path) == receipt


def test_checked_branch_cannot_be_attached_to_a_different_finding_id(
    monkeypatch, tmp_path
):
    import pytest

    batch = _checked_batch(monkeypatch)
    attachment = {
        "artifact": copy.deepcopy(batch[-1]),
        "context": {"artifacts": copy.deepcopy(batch[:-1])},
    }
    with pytest.raises(ValueError, match="different finding identity"):
        _observation_with_id(tmp_path, attachment, "different-bound")


def _observation_with_id(root, attachment, finding_id):
    from ladon.investigation_observations import record_observation

    _, base = observation_case(root)
    record = copy.deepcopy(base["observations"][0]["record"])
    record["schema"] = "ladon-investigation-observation-v2"
    record["id"] = finding_id
    record["contractAnalysis"] = copy.deepcopy(attachment)
    base.pop("observations")
    return record_observation(base, record, root)
