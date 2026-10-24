"""A leftover authored judgment is not a completed legacy review."""

from test_investigation_findings import NOW, legacy

from ladon.investigation import assess


def test_captured_claim_does_not_inherit_reviewed_finding(tmp_path):
    plan = legacy(tmp_path)
    plan["claims"][0]["state"] = "captured"
    status = assess(plan, tmp_path, now=NOW)
    assert status["findings"] == []
    assert status["counts"]["reviewedClaims"] == 0
    assert any(item["kind"] == "write-exact-contract" for item in status["next"])
