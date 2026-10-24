"""Public CLI wiring for the sanitized application-probe review export."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from ladon.proof_contract_cli import contract_main

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/CONSTANT-UNIFORMITY-20261019"


def test_review_probe_cli_exports_ordered_sanitized_attempts(tmp_path):
    request = EVIDENCE / "uniformity-checked-request.json"
    checked = EVIDENCE / "uniformity-checked-result.json"
    failed = EVIDENCE / "failed-term-result.json"
    attempt = json.loads(checked.read_text())
    artifact = tmp_path / "probe-artifact.json"
    artifact.write_text(json.dumps(attempt["artifact"]))
    output = tmp_path / "reviewer-input.json"

    assert contract_main([
        "review-probe", "--input", str(request), "--artifact", str(artifact),
        "--attempt", str(checked), "--attempt", str(failed), "--output", str(output),
    ]) == 0

    packet = json.loads(output.read_text())
    assert packet["schema"] == "ladon-application-probe-reviewer-input-v1"
    assert len(packet["attempts"]) == 2
    assert packet["attempts"][0]["executionObservation"] == "checks-completed"
    assert packet["attempts"][1]["executionObservation"] == "checks-unresolved"
    assert "checkerAuthority" not in packet
    assert "mathematicalFalsity" not in packet
    assert "checked-local-nonimplication" not in output.read_text()


def test_review_probe_cli_rejects_tampered_source_without_publishing(tmp_path):
    request = json.loads((EVIDENCE / "uniformity-checked-request.json").read_text())
    checked = EVIDENCE / "uniformity-checked-result.json"
    result = json.loads(checked.read_text())
    changed = next(a for a in request["context"]["artifacts"]
                   if a["artifactKind"] == "proofir.interpretation")
    changed["payload"]["record"]["source"]["quote"] += " changed"
    request_path = tmp_path / "request.json"
    artifact_path = tmp_path / "artifact.json"
    request_path.write_text(json.dumps(request))
    artifact_path.write_text(json.dumps(result["artifact"]))
    output = tmp_path / "must-not-exist.json"

    assert contract_main([
        "review-probe", "--input", str(request_path), "--artifact", str(artifact_path),
        "--attempt", str(checked), "--output", str(output),
    ]) == 2
    assert not output.exists()


def test_review_projection_preserves_duplicate_order_and_marks_cross_plan_attempt_unbound():
    from ladon.proof_contract_probe_review import review_application_probe

    request = json.loads((EVIDENCE / "uniformity-checked-request.json").read_text())
    checked = json.loads((EVIDENCE / "uniformity-checked-result.json").read_text())
    foreign = copy.deepcopy(checked)
    foreign["artifact"] = copy.deepcopy(checked["artifact"])
    foreign["artifact"]["artifactId"] = "sha256:" + "0" * 64
    foreign["status"] = "incomplete"

    packet = review_application_probe(
        checked["artifact"], request["context"], [checked, checked, foreign], request["repoRoot"]
    )

    attempts = packet["attempts"]
    assert len(attempts) == 3
    assert attempts[0]["attemptId"] == attempts[1]["attemptId"]
    assert attempts[0]["executionObservation"] == attempts[1]["executionObservation"]
    assert attempts[2]["sourcePlanBinding"] == "unbound-attempt"
    assert all(row["sourceGoalBinding"] == "unbound-attempt" for row in attempts[2]["goals"])
    assert all("rawReceipt" not in row for row in attempts[2]["goals"])


def test_historical_real_unsupported_and_expired_attempts_stay_visible():
    from ladon.proof_contract_probe_review import review_application_probe

    unsupported_request = json.loads(
        (EVIDENCE / "unsupported-witness-dependence-request.json").read_text()
    )
    unsupported = json.loads(
        (EVIDENCE / "unsupported-witness-dependence-result.json").read_text()
    )
    unsupported_packet = review_application_probe(
        unsupported["artifact"], unsupported_request["context"],
        [unsupported], unsupported_request["repoRoot"],
    )
    assert unsupported_packet["attempts"][0]["executionObservation"] == "template-unsupported"
    assert unsupported_packet["planningResiduals"]

    request = json.loads((EVIDENCE / "expired-request.json").read_text())
    expired = json.loads((EVIDENCE / "expired-result.json").read_text())
    checked = json.loads((EVIDENCE / "uniformity-checked-result.json").read_text())
    expired_packet = review_application_probe(
        checked["artifact"], request["context"], [expired], request["repoRoot"],
    )
    assert expired_packet["attempts"][0]["executionObservation"] == "preparation-stopped"
    assert expired_packet["attempts"][0]["sourcePlanBinding"] == "unbound-attempt"


def test_candidate_labels_in_nested_attempt_status_and_diagnostic_are_redacted():
    from ladon.proof_contract_probe_review import review_application_probe

    request = json.loads((EVIDENCE / "uniformity-checked-request.json").read_text())
    checked = json.loads((EVIDENCE / "uniformity-checked-result.json").read_text())
    injected = copy.deepcopy(checked)
    injected["goals"][0]["status"] = "checked-local-nonimplication"
    injected["preparation"]["status"] = "checked-local-implication"
    injected["diagnostic"] = {
        "code": "checked-local-nonimplication",
        "message": "candidateConclusion: the right-to-left implication fails",
    }

    packet = review_application_probe(
        checked["artifact"], request["context"], [injected], request["repoRoot"]
    )

    attempt = packet["attempts"][0]
    assert attempt["goals"][0]["status"] == "unrecognized-execution-observation"
    assert attempt["preparation"]["status"] == "unrecognized-execution-observation"
    serialized = json.dumps(packet, sort_keys=True).lower()
    assert "checked-local-nonimplication" not in serialized
    assert "checked-local-implication" not in serialized
    assert "candidateconclusion" not in serialized
    assert "the right-to-left implication fails" not in serialized


def test_incomplete_goal_coverage_cannot_be_reported_as_completed_checks():
    from ladon.proof_contract_probe_review import review_application_probe

    request = json.loads((EVIDENCE / "uniformity-checked-request.json").read_text())
    checked = json.loads((EVIDENCE / "uniformity-checked-result.json").read_text())
    for goals in ([], checked["goals"][:1]):
        partial = copy.deepcopy(checked)
        partial["goals"] = copy.deepcopy(goals)
        packet = review_application_probe(
            checked["artifact"], request["context"], [partial], request["repoRoot"]
        )
        row = packet["attempts"][0]
        assert row["executionObservation"] == "partial-check-evidence"
        assert row["sourcePlanBinding"] == "native-artifact-partial-goals"


def test_incomplete_checker_timeout_is_attributed_to_checker_stage():
    from ladon.proof_contract_probe_review import review_application_probe

    request = json.loads((EVIDENCE / "uniformity-checked-request.json").read_text())
    checked = json.loads((EVIDENCE / "uniformity-checked-result.json").read_text())
    stopped = copy.deepcopy(checked)
    stopped["status"] = "incomplete"
    stopped["goals"][0]["status"] = "timed_out"
    stopped["goals"][0]["supervision"]["status"] = "timed_out"
    packet = review_application_probe(
        checked["artifact"], request["context"], [stopped], request["repoRoot"]
    )
    assert packet["attempts"][0]["executionObservation"] == "checker-stopped"


def test_incomplete_preparation_timeout_is_attributed_to_preparation_stage():
    from ladon.proof_contract_probe_review import review_application_probe

    request = json.loads((EVIDENCE / "uniformity-checked-request.json").read_text())
    checked = json.loads((EVIDENCE / "uniformity-checked-result.json").read_text())
    stopped = json.loads((EVIDENCE / "expired-result.json").read_text())
    packet = review_application_probe(
        checked["artifact"], request["context"], [stopped], request["repoRoot"]
    )
    assert packet["attempts"][0]["executionObservation"] == "preparation-stopped"


def test_checked_status_without_goal_checker_receipts_is_unverified():
    from ladon.proof_contract_probe_review import review_application_probe

    request = json.loads((EVIDENCE / "uniformity-checked-request.json").read_text())
    checked = json.loads((EVIDENCE / "uniformity-checked-result.json").read_text())
    malformed = copy.deepcopy(checked)
    malformed["preparation"] = {"status": "completed"}
    malformed["goals"] = [
        {key: goal[key] for key in ("goalId", "goal", "goalDigest")}
        | {"status": "open"}
        for goal in checked["goals"]
    ]

    packet = review_application_probe(
        checked["artifact"], request["context"], [malformed], request["repoRoot"]
    )
    assert packet["attempts"][0]["executionObservation"] == "unverified-check-evidence"
    assert all("rawReceipt" not in goal for goal in packet["attempts"][0]["goals"])
