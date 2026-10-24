"""Frozen regression: rejected raw evidence cannot certify a checked goal."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from ladon.proof_contract_probe_review import review_application_probe

ROOT = Path(__file__).resolve().parents[5]
INPUTS = ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/CONSTANT-UNIFORMITY-20261019"


def test_rejected_same_goal_receipt_cannot_certify_checked_result():
    request = json.loads((INPUTS / "uniformity-checked-request.json").read_text())
    checked = json.loads((INPUTS / "uniformity-checked-result.json").read_text())
    failed = json.loads((INPUTS / "failed-term-result.json").read_text())
    malformed = copy.deepcopy(checked)
    checked_goal = next(goal for goal in malformed["goals"] if goal["goalId"] == "probe")
    rejected_goal = next(goal for goal in failed["goals"] if goal["goalId"] == "probe")
    assert checked_goal["goal"] == rejected_goal["goal"]
    assert checked_goal["goalDigest"] == rejected_goal["goalDigest"]
    checked_goal["result"] = copy.deepcopy(rejected_goal["result"])

    packet = review_application_probe(
        checked["artifact"], request["context"], [malformed], request["repoRoot"]
    )

    row = packet["attempts"][0]
    assert row["executionObservation"] == "unverified-check-evidence"
    probe = next(goal for goal in row["goals"] if goal["goalId"] == "probe")
    assert probe["rawReceipt"]["status"] == "unresolved"
    assert probe["rawReceipt"]["completion"]["status"] == "rejected"
