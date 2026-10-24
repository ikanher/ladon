"""Default RSS observations remain part of self-verifying replay receipts."""
from pathlib import Path

from ladon.process_supervisor import ProcessResult
from ladon.theorem_capsule_models import artifact_identity, replay_receipt
from ladon.theorem_capsule_replay import _process_stage_row


def test_sampled_peak_changes_receipt_identity_without_losing_measurements():
    receipts = []
    for peak in (1024**3, 2 * 1024**3):
        process = ProcessResult(("lean",), 0, "", "", 0.1, peak_rss_bytes=peak)
        row = _process_stage_row("build", ("lean",), process, Path("/tmp/replay"), 12 * 1024**3)
        receipt = replay_receipt({"status": "verified", "stages": [row]})
        body = {key: value for key, value in receipt.items() if key != "receiptIdentity"}
        assert receipt["receiptIdentity"] == artifact_identity("replay", body)
        assert receipt["stages"][0]["peakRssBytes"] == peak
        receipts.append(receipt)
    assert receipts[0]["receiptIdentity"] != receipts[1]["receiptIdentity"]
