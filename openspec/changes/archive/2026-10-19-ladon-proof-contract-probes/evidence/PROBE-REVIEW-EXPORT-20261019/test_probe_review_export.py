"""Isolated red contract tests for source-bound probe reviewer export."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/CONSTANT-UNIFORMITY-20261019"


def _inputs():
    request = json.loads((EVIDENCE / "uniformity-checked-request.json").read_text())
    checked = json.loads((EVIDENCE / "uniformity-checked-result.json").read_text())
    return checked["artifact"], request["context"], request["repoRoot"], checked


def _attempts(checked):
    failure = json.loads((EVIDENCE / "failed-term-result.json").read_text())
    unresolved = json.loads((EVIDENCE / "missing-terms-result.json").read_text())
    unsupported = copy.deepcopy(unresolved)
    unsupported["status"] = "unsupported"
    unsupported["goals"] = copy.deepcopy(checked["artifact"]["payload"]["result"]["goals"])
    stopped = copy.deepcopy(unresolved)
    stopped["status"] = "incomplete"
    stopped["goals"] = copy.deepcopy(checked["artifact"]["payload"]["result"]["goals"])
    stopped["preparation"]["status"] = "timed_out"
    # These two attempts have the exact generated goals but no checker receipts.
    return [checked, failure, unsupported, stopped]


def _review(artifact=None, context=None, repo_root=None, attempts=None):
    from ladon.proof_contract_probe_review import review_application_probe

    if artifact is None or context is None or repo_root is None:
        artifact, context, repo_root, checked = _inputs()
        attempts = _attempts(checked) if attempts is None else attempts
    return review_application_probe(artifact, context, attempts, repo_root)


def test_review_export_preserves_original_readings_source_anchors_and_attempt_order():
    artifact, context, repo_root, checked = _inputs()
    attempts = _attempts(checked)
    packet = _review(artifact, context, repo_root, attempts)

    evidence = packet
    assert evidence["template"] == artifact["payload"]["template"]
    assert evidence["goals"] == artifact["payload"]["result"]["goals"]
    assert len(evidence["attempts"]) == len(attempts)
    assert [row["executionObservation"] for row in evidence["attempts"]] == [
        "checks-completed", "checks-unresolved", "template-unsupported", "preparation-stopped"
    ]
    assert evidence["attempts"][0]["goals"][0]["result"]["evidenceRef"] == attempts[0]["goals"][0]["result"]["evidenceRef"]
    assert evidence["attempts"][1]["goals"][0]["result"]["evidenceRef"] == attempts[1]["goals"][0]["result"]["evidenceRef"]
    assert evidence["attempts"][2]["goals"][0]["status"] == "open"
    assert evidence["attempts"][3]["goals"][0]["status"] == "open"
    raw_ref = attempts[0]["goals"][0]["result"]["evidenceRef"]
    raw_path = Path(repo_root) / raw_ref["path"]
    raw = json.loads(raw_path.read_text())
    assert json.dumps(raw["completion"], sort_keys=True) in json.dumps(evidence, sort_keys=True)

    readings = evidence["sourceReadings"]
    assert len(readings) == 2
    expected_quotes = {
        a["payload"]["record"]["source"]["quote"]
        for a in context["artifacts"]
        if a["artifactKind"] == "proofir.interpretation"
    }
    assert {row["quote"] for row in readings} == expected_quotes
    assert all(row["sourceRef"]["kind"] == "source-map" for row in readings)
    assert all(row["anchors"] for row in readings)


def test_reviewer_projection_keeps_attempt_outcomes_but_omits_candidate_conclusions():
    packet = _review()
    evidence = packet
    assert [row["executionObservation"] for row in evidence["attempts"]] == [
        "checks-completed", "checks-unresolved", "template-unsupported", "preparation-stopped"
    ]
    assert evidence["attempts"][0]["goals"][0]["status"] == "checked-support"
    assert evidence["attempts"][1]["goals"][1]["status"] == "unresolved"
    assert evidence["attempts"][3]["preparation"]["status"] == "timed_out"
    assert "status" not in evidence
    serialized = json.dumps(evidence, sort_keys=True).lower()
    for forbidden in (
        "candidateverdict", "proposedverdict", "proposedconclusion",
        "checkerauthority", "wholemethodauthority", "mathematicalfalsity",
        "sourcefidelity", "candidateconclusion", "checked-local-nonimplication",
        "checked-local-implication", "unsupported-template",
    ):
        assert forbidden not in serialized


def test_review_export_is_deterministic_and_source_tampering_is_rejected():
    artifact, context, repo_root, checked = _inputs()
    attempts = _attempts(checked)
    first = _review(artifact, context, repo_root, attempts)
    second = _review(artifact, context, repo_root, attempts)
    assert first == second
    changed = copy.deepcopy(context)
    reading = next(a for a in changed["artifacts"] if a["artifactKind"] == "proofir.interpretation")
    reading["payload"]["record"]["source"]["quote"] += " altered"
    with pytest.raises((ValueError, TypeError)):
        _review(artifact, changed, repo_root, attempts)
