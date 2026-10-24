"""Frozen regression: a checked top-level label needs exact checker receipts."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from ladon.proof_contract_probe_review import review_application_probe

ROOT = Path(__file__).resolve().parents[5]
INPUTS = ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/CONSTANT-UNIFORMITY-20261019"


def test_checked_label_without_checker_receipts_is_unverified():
    request = json.loads((INPUTS / "uniformity-checked-request.json").read_text())
    result = json.loads((INPUTS / "uniformity-checked-result.json").read_text())
    malformed = copy.deepcopy(result)
    malformed["preparation"] = {"status": "completed"}
    malformed["goals"] = [
        {key: goal[key] for key in ("goalId", "goal", "goalDigest")}
        | {"status": "open"}
        for goal in result["goals"]
    ]

    packet = review_application_probe(
        result["artifact"], request["context"], [malformed], request["repoRoot"]
    )

    assert packet["attempts"][0]["executionObservation"] == "unverified-check-evidence"
    assert all("rawReceipt" not in goal for goal in packet["attempts"][0]["goals"])
