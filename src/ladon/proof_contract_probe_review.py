"""Sanitized, source-bound reviewer projection for application-probe attempts."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from ._proof_contract_probe_pair import resolve_pair
from ._proof_contract_route_context_evidence import load_goal_evidence
from .proof_contract_probe_cli import inspect_application_probe

MAX_ATTEMPTS = 64
MAX_REVIEW_BYTES = 32 * 1024**2
_EXECUTION_OBSERVATIONS = {
    "planned": "prepared-only",
    "checked-local-implication": "checks-completed",
    "checked-local-nonimplication": "checks-completed",
    "unresolved": "checks-unresolved",
    "incomplete": "execution-incomplete",
    "unsupported": "template-unsupported",
    "rejected": "input-rejected",
}
_CHECK_OBSERVATIONS = {
    "open", "checked-support", "unresolved", "failed", "unsupported",
    "incomplete", "rejected", "timed_out", "memory_limited", "output_limited",
}
_STAGE_OBSERVATIONS = {
    "prepared", "completed", "incomplete", "rejected", "unsupported",
    "timed_out", "memory_limited", "output_limited", "failed",
}


def review_application_probe(artifact, context, attempts, repo_root):
    """Return only original subjects, generated goals, and ordered check evidence.

    This projection deliberately drops Ladon's proposed semantic outcome and
    authority labels.  Attempt order and duplicates are retained.  Raw goal
    evidence is loaded from the trusted local Ladon evidence store; this does
    not authenticate who wrote that store.
    """
    from ._proof_contract_planned_source_inputs import _planned_input_size

    if (not isinstance(attempts, list) or len(attempts) > MAX_ATTEMPTS
            or _planned_input_size([artifact, context, attempts]) > MAX_REVIEW_BYTES):
        raise ValueError("probe review input exceeds bounded attempt or byte limits")
    replayed = inspect_application_probe(artifact, context)
    if replayed != artifact:
        raise ValueError("probe artifact failed exact native semantic inspection")

    payload = artifact["payload"]
    refs = list(zip(payload["contractRefs"], payload["correspondenceRefs"], strict=True))
    sides = [{"contractRef": contract, "correspondenceRef": correspondence}
             for contract, correspondence in refs]
    pair = resolve_pair(context["artifacts"], *sides)
    root = Path(repo_root).resolve(strict=True)
    sources = [_source_reading(side, context["artifacts"], root) for side in pair]
    planned_goals = payload["result"]["goals"]
    rows = [_attempt_row(attempt, artifact, planned_goals, root) for attempt in attempts]
    reviewer_input = {
        "schema": "ladon-application-probe-reviewer-input-v1",
        "subject": {
            "analysisId": payload["analysisId"],
            "artifactId": artifact["artifactId"],
            "contractRefs": copy.deepcopy(payload["contractRefs"]),
            "correspondenceRefs": copy.deepcopy(payload["correspondenceRefs"]),
        },
        "template": copy.deepcopy(payload["template"]),
        "sourceReadings": sources,
        "goals": copy.deepcopy(planned_goals),
        "planningResiduals": copy.deepcopy(payload["residuals"]),
        "attempts": rows,
        "reviewInstruction": (
            "Independently assess the original readings and the evidence for the exact goals. "
            "The packet contains no Ladon semantic conclusion or authority assessment."
        ),
        "evidenceTrust": (
            "Raw checker receipts are reproduced from the repository-local Ladon evidence store. "
            "Content hashes detect mutation but do not authenticate the writer."
        ),
    }
    if _planned_input_size(reviewer_input) > MAX_REVIEW_BYTES:
        raise ValueError("probe reviewer input exceeds 32 MiB")
    return reviewer_input


def _source_reading(side, artifacts, root):
    from .correspondence_interpretation import validate_interpretation

    reading = side["reading"]
    contract = side["contract"]
    correspondence = side["correspondence"]
    # Validate the quote against the original source file before exporting it.
    record = validate_interpretation(reading["payload"]["record"], root)
    source_map_ref = reading["payload"]["sourceRef"]
    source_maps = [a for a in artifacts
                   if a.get("artifactKind") == "proofir.source-map"
                   and a.get("artifactId") == source_map_ref["artifactRef"]]
    if len(source_maps) != 1 or source_maps[0]["payload"]["sourceMapId"] != source_map_ref["localId"]:
        raise ValueError("probe source map has no unique exact owner")
    native_source_map = source_maps[0]
    return {
        "contractRef": {"artifactRef": contract["artifactId"], "kind": "contract",
                         "localId": contract["payload"]["contractId"]},
        "correspondenceRef": {"artifactRef": correspondence["artifactId"],
                               "kind": "correspondence",
                               "localId": correspondence["payload"]["correspondenceId"]},
        "interpretationRef": {"artifactRef": reading["artifactId"], "kind": "interpretation",
                              "localId": reading["payload"]["interpretationId"]},
        "sourceRef": copy.deepcopy(source_map_ref),
        "quote": record["source"]["quote"],
        "source": copy.deepcopy(record["source"]),
        "interpretation": copy.deepcopy(record),
        "contract": copy.deepcopy(contract["payload"]["record"]),
        "formalContext": {
            "slice": copy.deepcopy(correspondence["payload"]["slice"]),
            "objectMap": copy.deepcopy(correspondence["payload"]["objectMap"]),
        },
        "anchors": copy.deepcopy(native_source_map["payload"]["anchors"]),
    }


def _attempt_row(attempt, artifact, planned_goals, root):
    if not isinstance(attempt, dict) or attempt.get("schema") != "ladon-application-probe-v1":
        raise ValueError("probe review attempts must be complete Ladon result envelopes")
    attempt_bytes = _canonical(attempt)
    if len(attempt_bytes) > MAX_REVIEW_BYTES:
        raise ValueError("probe review attempt exceeds byte limit")
    observed = attempt.get("status")
    artifact_bound = attempt.get("artifact") == artifact
    planned_by_id = {row["goalId"]: row for row in planned_goals}
    raw_goals = attempt.get("goals", [])
    goals = _goal_attempts(raw_goals, planned_by_id, artifact_bound, root)

    preparation = _preparation_observation(attempt.get("preparation"))
    complete_goal_coverage = _complete_goal_coverage(raw_goals, planned_by_id)
    execution = _execution_observation(observed, attempt, goals, complete_goal_coverage)
    if not artifact_bound:
        binding = "unbound-attempt"
    elif not complete_goal_coverage:
        binding = "native-artifact-partial-goals"
    else:
        binding = "exact-native-artifact"
    row = {
        "attemptId": "sha256:" + hashlib.sha256(attempt_bytes).hexdigest(),
        "sourcePlanBinding": binding,
        "executionObservation": execution,
        "preparation": preparation,
        "goals": goals,
    }
    diagnostic = _execution_diagnostic(attempt.get("diagnostic"))
    if diagnostic is not None:
        row["executionDiagnostic"] = diagnostic
    return row


def _complete_goal_coverage(rows, planned_by_id):
    """Require one exact row for each generated goal before claiming checks ran."""
    if not isinstance(rows, list) or len(rows) != len(planned_by_id):
        return False
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            return False
        goal_id = row.get("goalId")
        planned = planned_by_id.get(goal_id)
        if (planned is None or goal_id in seen
                or row.get("goal") != planned["goal"]
                or row.get("goalDigest") != planned["goalDigest"]):
            return False
        seen.add(goal_id)
    return seen == set(planned_by_id)


def _execution_observation(observed, attempt, goals, complete_goal_coverage):
    if observed in {"checked-local-implication", "checked-local-nonimplication"}:
        if not complete_goal_coverage:
            return "partial-check-evidence"
        if not _complete_checker_evidence(goals):
            return "unverified-check-evidence"
    if observed == "unresolved" and not complete_goal_coverage:
        return "partial-check-evidence"
    if observed == "incomplete":
        return _incomplete_stage_observation(attempt)
    return _EXECUTION_OBSERVATIONS.get(observed, "execution-outcome-unavailable")


def _complete_checker_evidence(goals):
    if not isinstance(goals, list) or not goals:
        return False
    return all(_goal_has_completed_receipt(goal) for goal in goals)


def _goal_has_completed_receipt(goal):
    if not isinstance(goal, dict) or goal.get("status") != "checked-support":
        return False
    if not isinstance(goal.get("term"), str) or not goal["term"]:
        return False
    if goal.get("receiptLoad") != "loaded-from-content-addressed-store":
        return False
    if not _raw_receipt_supports_goal(goal.get("rawReceipt"), goal["term"]):
        return False
    execution = goal.get("executionReceipt")
    return isinstance(execution, dict) and execution.get("status") == "completed"


def _raw_receipt_supports_goal(receipt, term):
    if not isinstance(receipt, dict) or receipt.get("status") != "supported":
        return False
    completion = receipt.get("completion")
    if not isinstance(completion, dict) or completion.get("status") != "completed":
        return False
    if completion.get("termDigest") != "sha256:" + hashlib.sha256(term.encode()).hexdigest():
        return False
    replay, trust = completion.get("replay"), completion.get("trust")
    return (isinstance(replay, dict) and replay.get("status") == "accepted"
            and isinstance(trust, dict) and trust.get("accepted") is True)


def _incomplete_stage_observation(attempt):
    preparation = attempt.get("preparation")
    if _stage_stopped(preparation):
        return "preparation-stopped"
    if (isinstance(preparation, dict) and preparation.get("status") == "completed"
            and _checker_stopped(attempt.get("goals"))):
        return "checker-stopped"
    return "execution-incomplete"


def _stage_stopped(stage):
    return isinstance(stage, dict) and stage.get("status") in {
        "timed_out", "memory_limited", "output_limited", "incomplete"
    }


def _checker_stopped(goals):
    if not isinstance(goals, list):
        return False
    stop_statuses = {"timed_out", "memory_limited", "output_limited"}
    for goal in goals:
        if not isinstance(goal, dict):
            continue
        if goal.get("status") in stop_statuses:
            return True
        supervision = goal.get("supervision")
        if isinstance(supervision, dict) and supervision.get("status") in stop_statuses:
            return True
    return False


def _goal_attempts(rows, planned_by_id, artifact_bound, root):
    if not isinstance(rows, list) or len(rows) > 2:
        raise ValueError("probe attempt has an invalid goal-attempt list")
    return [_goal_attempt(row, planned_by_id, artifact_bound, root) for row in rows]


def _goal_attempt(row, planned_by_id, artifact_bound, root):
    if not isinstance(row, dict):
        raise TypeError("probe review goal attempt must be an object")
    planned = planned_by_id.get(row.get("goalId"))
    bound = _goal_is_bound(row, planned, artifact_bound)
    projected = {key: copy.deepcopy(row[key]) for key in (
        "goalId", "goalDigest", "goal", "kind", "term", "result"
    ) if key in row}
    projected["status"] = _safe_observation(row.get("status"), _CHECK_OBSERVATIONS)
    if "supervision" in row:
        projected["executionReceipt"] = _supervision_observation(row["supervision"])
    projected["sourceGoalBinding"] = "exact-native-goal" if bound else "unbound-attempt"
    _attach_raw_receipt(projected, row.get("result"), bound, root)
    return projected


def _goal_is_bound(row, planned, artifact_bound):
    return (artifact_bound and planned is not None
            and row.get("goal") == planned["goal"]
            and row.get("goalDigest") == planned["goalDigest"])


def _attach_raw_receipt(projected, compact, bound, root):
    if not isinstance(compact, dict) or not isinstance(compact.get("evidenceRef"), dict):
        return
    if not bound:
        projected["receiptLoad"] = "unbound-reference-not-loaded"
        return
    try:
        receipt = load_goal_evidence(root, compact)
    except (ValueError, TypeError, KeyError, OSError, RecursionError):
        projected["receiptLoad"] = "unavailable-or-changed"
    else:
        projected["rawReceipt"] = receipt
        projected["receiptLoad"] = "loaded-from-content-addressed-store"


def _execution_diagnostic(diagnostic):
    if not isinstance(diagnostic, dict):
        return None
    code = diagnostic.get("code")
    safe_codes = {"timeout", "memory-limit", "output-limit", "unresolved-proof",
                  "invalid-application-probe", "probe-preparation-rejected",
                  "probe-preparation-incomplete"}
    return {"code": code if isinstance(code, str) and code in safe_codes
            else "other-execution-failure"}


def _preparation_observation(value):
    if not isinstance(value, dict):
        return None
    projected = _stage_projection(value)
    if isinstance(value.get("processReceipt"), dict):
        projected["processReceipt"] = _process_receipt(value["processReceipt"])
    diagnostic = _execution_diagnostic(value.get("diagnostic"))
    if diagnostic is not None:
        projected["diagnostic"] = diagnostic
    return projected


def _supervision_observation(value):
    if not isinstance(value, dict):
        return None
    projected = _stage_projection(value)
    if isinstance(value.get("processReceipt"), dict):
        projected["processReceipt"] = _process_receipt(value["processReceipt"])
    diagnostic = _execution_diagnostic(value.get("diagnostic"))
    if diagnostic is not None:
        projected["diagnostic"] = diagnostic
    return projected


def _stage_projection(value):
    projected = {key: copy.deepcopy(value[key]) for key in (
        "bounds", "workerInputDigest"
    ) if key in value}
    if value.get("schema") == "ladon-supervised-obligation-planner-v1":
        projected["schema"] = value["schema"]
    projected["status"] = _safe_observation(value.get("status"), _STAGE_OBSERVATIONS)
    return projected


def _safe_observation(value, allowed):
    if isinstance(value, str) and value in allowed:
        return value
    return "unrecognized-execution-observation"


def _process_receipt(value):
    allowed = ("elapsedSeconds", "peakRssBytes", "requestedMaxOutputBytes",
               "requestedMaxRssBytes", "requestedTimeoutSeconds", "returnCode",
               "memoryLimited", "outputLimited", "timedOut", "inputDigest",
               "workerInputDigest", "stdoutDigest", "stderrDigest")
    return {key: copy.deepcopy(value[key]) for key in allowed if key in value}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
