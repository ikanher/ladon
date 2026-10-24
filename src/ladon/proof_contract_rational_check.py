"""Regenerated and source-completed checks for finite rational branches."""
from __future__ import annotations

import copy
import hashlib
import json
import time
from importlib import resources

from ladon._proof_contract_context_goals import ContextOutputLimit
from ladon._proof_contract_source_obligations_inputs import bounded_json_size
from ladon.proof_contract_source_obligations import MAX_INPUT_BYTES, _limits
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

_CACHE_SCHEMA = "ladon-rational-branch-check-cache-v1"
_CHECKER = {"name": "ladon-rational-branch-source-completion", "version": "1"}
_DIGEST_PREFIX = "sha256:"


def check_rational_branch_probe(request, plan_id, terms, *, cached_result=None,
                                plan, execute_job):
    """Regenerate, check and independently replay exact branch propositions."""
    started = time.monotonic()
    from ladon.proof_contract_rational_probes import _own_request
    owned, _plan_limits = _own_request(request)
    limits = _check_limits(request["limits"])
    try:
        prepared = _regenerate_check(request, plan_id, terms, cached_result,
                                     owned, plan)
        if isinstance(prepared, dict):
            return prepared
        current, goals, goal_ids = prepared
        checked = _check_goals(current, goals, goal_ids, terms, owned, limits,
                               plan, execute_job)
        if checked[0] is not None:
            return checked[0]
        completed, call_receipts, checker = checked[1], checked[2], checked[3]
        return _finish_check(request, current, completed, call_receipts, owned,
                             limits, plan, started, checker)
    except ContextOutputLimit as error:
        return _stopped("incomplete", "output-limit", str(error))
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError,
            RecursionError) as error:
        return _stopped("rejected", "invalid-rational-branch-check", str(error))


def _regenerate_check(request, plan_id, terms, cached_result, owned, plan):
    if bounded_json_size({"request": request, "terms": terms,
                          "cachedResult": cached_result}, MAX_INPUT_BYTES) > MAX_INPUT_BYTES:
        raise ValueError("rational branch check input exceeds 8 MiB")
    if type(plan_id) is not str or type(terms) is not dict:
        raise ValueError("rational branch check requires a plan ID and goal-term object")
    if owned["deadlineMonotonic"] <= time.monotonic():
        return _stopped("incomplete", "timeout", "Shared rational-branch deadline expired before regeneration.")
    current = plan(request)
    if current.get("status") != "planned":
        return _propagate_stop(current)
    if current.get("planId") != plan_id:
        return _stopped("stale-input", "plan-id-mismatch",
                        "The supplied plan ID differs from the regenerated branch plan.")
    goals = current["goals"]
    goal_ids = [row["goalId"] for row in goals]
    if not _valid_goal_terms(terms, goal_ids):
        return _stopped("rejected", "goal-terms-mismatch",
                        "Terms must provide one bounded nonempty proof for every regenerated goal ID.")
    return current, goals, goal_ids


def _valid_goal_terms(terms, goal_ids):
    return (set(terms) == set(goal_ids)
            and all(type(terms[goal_id]) is str and terms[goal_id].strip()
                    and len(terms[goal_id].encode("utf-8")) <= 256 * 1024
                    for goal_id in goal_ids))


def _check_goals(current, goals, goal_ids, terms, owned, limits, plan, execute_job):
    completed, call_receipts = [], []
    checker = _proof_checker_identity()
    for goal in goals:
        if owned["deadlineMonotonic"] <= time.monotonic():
            return (_stopped("incomplete", "timeout",
                             "Shared rational-branch deadline expired during checking.",
                             current, completed, call_receipts), completed, call_receipts, checker)
        term = terms[goal["goalId"]]
        binding = _goal_binding(current, goal, term, checker)
        job = _goal_job(current, goal, goal_ids, term, binding, owned, limits)
        bounds = {**limits, "deadlineMonotonic": owned["deadlineMonotonic"]}
        state = {"receipt": None, "inputDigest": None, "bounds": None}
        checked = execute_job(job, bounds, state, None,
                              worker_module="ladon.proof_contract_rational_worker")
        call_receipts.append(checked.get("processReceipt"))
        stop = _worker_stop(checked, goal, term, binding, current,
                            completed, call_receipts)
        if stop is not None:
            return stop, completed, call_receipts, checker
        completed.append({"goal": copy.deepcopy(goal), "term": term,
                          "termDigest": _digest_text(term), "result": checked["result"],
                          "reused": False, "binding": binding,
                          "supervision": checked.get("processReceipt")})
    return None, completed, call_receipts, checker


def _goal_job(current, goal, goal_ids, term, binding, owned, limits):
    return {
        "version": 1, "operation": "check-rational-branch-goal",
        "workspaceRoot": owned["workspaceRoot"],
        "workspaceIdentity": current["workspaceIdentity"],
        "goalId": goal["goalId"], "goal": goal["leanProposition"],
        "goalDigest": current["goalDigests"][goal_ids.index(goal["goalId"])],
        "term": term, "binding": binding,
        "deadlineMonotonic": owned["deadlineMonotonic"],
        "limits": limits,
    }


def _worker_stop(checked, goal, term, binding, current, completed, call_receipts):
    if checked.get("status") != "completed":
        status = "incomplete" if checked.get("status") == "incomplete" else "rejected"
        diagnostic = checked.get("diagnostic") or {}
        return _stopped(status, diagnostic.get("code", "rational-check-worker"),
                        diagnostic.get("message", "Bounded rational check did not complete."),
                        current, completed, call_receipts)
    raw = checked.get("result")
    status = raw.get("status") if isinstance(raw, dict) else None
    if status in {"timeout", "memory-limit", "output-limit", "incomplete"}:
        return _stopped("incomplete", raw.get("reason", status),
                        raw.get("diagnostic", "Bounded Lean check stopped before completion."),
                        current, completed, call_receipts)
    if status == "unsupported":
        return _stopped("unsupported", raw.get("reason", "lean-check-unsupported"),
                        raw.get("diagnostic", "Selected Lean context cannot complete this check."),
                        current, completed, call_receipts)
    if status == "stale":
        return _stopped("stale-input", raw.get("reason", "lean-context-stale"),
                        raw.get("diagnostic", "Selected Lean context changed during this check."),
                        current, completed, call_receipts)
    if not _accepted_result(raw, goal, term, binding):
        return _stopped("unresolved", "proof-not-accepted",
                        "Lean completion, independent replay, or trust validation did not accept this exact proof.",
                        current, completed, call_receipts)
    return None


def _finish_check(request, current, completed, call_receipts, owned, limits, plan, started, checker):
    stopped = _inventory_stop(request, current, completed, call_receipts, owned, plan)
    if stopped is not None:
        return stopped
    inventory_digests = {
        row["goal"]["goalId"]: _compiled_inventory_digest(row["result"])
        for row in completed
    }
    artifacts = [_check_run_artifact(current, row, checker, limits)
                 for row in completed]
    if any(artifact is None for artifact in artifacts):
        return _stopped("rejected", "missing-check-run-evidence",
                        "An accepted goal lacks the bounded process evidence required for its ProofIR check-run artifact.",
                        current, completed, call_receipts)
    receipt = _receipt(current, completed, checker, artifacts, inventory_digests)
    checked_artifact = _checked_analysis_artifact(current, artifacts, receipt)
    from ladon.proofir_v3 import validate_envelope_batch
    validate_envelope_batch([current["artifact"], *artifacts, checked_artifact])
    result = _checked_result(current, completed, receipt, artifacts,
                             checked_artifact, time.monotonic() - started)
    return _bounded_result(result, limits["max_output_bytes"])


def _inventory_stop(request, current, completed, call_receipts, owned, plan):
    if owned["deadlineMonotonic"] <= time.monotonic():
        return _stopped("incomplete", "timeout",
                        "Shared rational-branch deadline expired before source revalidation.",
                        current, completed, call_receipts)
    digests = [_compiled_inventory_digest(row["result"]) for row in completed]
    if any(value is None for value in digests):
        return _stopped("rejected", "missing-compiled-inventory",
                        "An accepted goal lacks its captured compiled-module inventory.",
                        current, completed, call_receipts)
    if len(set(digests)) != 1:
        return _stopped("stale-input", "compiled-inventory-changed-during-check",
                        "The compiled import inventory changed between generated-goal checks.",
                        current, completed, call_receipts)
    latest = plan(request)
    if latest.get("status") != "planned" or latest.get("planId") != current["planId"]:
        return _stopped("stale-input", "source-changed-during-check",
                        "Branch, source spans, generated goals, checker, or workspace changed during checking.",
                        current, completed, call_receipts)
    return None


def _checked_result(current, completed, receipt, artifacts, checked_artifact, elapsed):
    return {
        "schema": "ladon-rational-branch-check-v1",
        "status": "checked-rational-branch", "planId": current["planId"],
        "goals": [_goal_result(row) for row in completed],
        "receipt": receipt, "cache": _result_cache(current, completed),
        "artifacts": artifacts, "checkedArtifact": checked_artifact,
        "sourceFormulaFidelity": "unverified",
        "originalClaimRefuted": False,
        "checkedSupport": {"scope": "finite-assignment-generated-goals",
                           "goalCount": len(completed)},
        "diagnostic": None, "elapsedSeconds": elapsed,
    }


def _goal_binding(plan, goal, term, checker):
    return {
        "planId": plan["planId"], "branchId": plan["branchId"],
        "branchKind": plan["branchKind"],
        "sourceSpanIdentities": copy.deepcopy(plan["sourceSpanIdentities"]),
        "baseGoalSha256": plan["baseGoalSha256"],
        "derivedGoalSha256": plan["derivedGoalSha256"],
        "assignment": copy.deepcopy(plan["assignment"]),
        "goalId": goal["goalId"], "goalDigest": _digest_text(goal["leanProposition"]),
        "generatedProposition": goal["leanProposition"],
        "checkerIdentity": copy.deepcopy(plan["checkerIdentity"]),
        "proofCheckerIdentity": checker,
        "workspaceIdentity": plan["workspaceIdentity"],
        "termDigest": _digest_text(term),
    }


def _check_limits(supplied):
    configured = _limits({
        "timeout_seconds": 30, "max_output_bytes": MAX_INPUT_BYTES,
        "max_rss_bytes": DEFAULT_MAX_RSS_BYTES,
    } | supplied)
    return {
        **configured,
        "timeout_seconds": min(120.0, configured["timeout_seconds"]),
        "max_rss_bytes": min(DEFAULT_MAX_RSS_BYTES, configured["max_rss_bytes"]),
    }


def _accepted_result(raw, goal, term, binding):
    if not isinstance(raw, dict):
        return False
    return (_accepted_identity(raw, goal, binding)
            and _accepted_completion(raw, term)
            and _accepted_replay(raw)
            and _accepted_trust(raw))


def _accepted_identity(raw, goal, binding):
    return (raw.get("status") == "accepted"
            and raw.get("generatedProposition") == goal["leanProposition"]
            and raw.get("binding") == binding)


def _accepted_completion(raw, term):
    completion = raw.get("completion")
    return (isinstance(completion, dict)
            and completion.get("status") == "completed"
            and _digest_matches(completion.get("termDigest"), _digest_text(term)))


def _accepted_replay(raw):
    return isinstance(raw.get("replay"), dict) and raw["replay"].get("status") == "replayed"


def _accepted_trust(raw):
    return isinstance(raw.get("trust"), dict) and raw["trust"].get("status") == "trusted"


def _result_cache(plan, completed):
    return {
        "schema": _CACHE_SCHEMA, "planId": plan["planId"],
        "reusePolicy": "fresh-lean-replay-required",
        "goals": [{
            "goalId": row["goal"]["goalId"],
            "goalDigest": _digest_text(row["goal"]["leanProposition"]),
            "proposition": row["goal"]["leanProposition"], "term": row["term"],
            "termDigest": row["termDigest"], "status": "checked-support",
            "binding": row["binding"], "result": _result_summary(row["result"]),
        } for row in completed],
    }


def _receipt(plan, completed, checker, artifacts, inventory_digests):
    return {
        "schema": "ladon-rational-branch-check-receipt-v1",
        "planId": plan["planId"], "branchId": plan["branchId"],
        "originalFindingId": plan["originalFindingId"],
        "branchKind": plan["branchKind"],
        "sourceSpanIdentities": copy.deepcopy(plan["sourceSpanIdentities"]),
        "baseGoalSha256": plan["baseGoalSha256"],
        "derivedGoalSha256": plan["derivedGoalSha256"],
        "assignment": copy.deepcopy(plan["assignment"]),
        "goalDigests": copy.deepcopy(plan["goalDigests"]),
        "checkerIdentity": copy.deepcopy(plan["checkerIdentity"]),
        "proofCheckerIdentity": checker,
        "workspaceIdentity": plan["workspaceIdentity"],
        "compiledInventoryDigest": next(iter(inventory_digests.values())),
        "compiledInventoryDigestsByGoal": inventory_digests,
        "termDigests": {row["goal"]["goalId"]: row["termDigest"] for row in completed},
        "checkRunRefs": [
            {"artifactRef": artifact["artifactId"],
             "kind": "check-run",
             "localId": artifact["payload"]["checkRunId"]}
            for artifact in artifacts
        ],
        "checkerAuthority": "exact-generated-goals-only",
        "sourceFormulaFidelity": "unverified", "originalClaimRefuted": False,
        "cacheTrust": "trusted-local-ladon-output-not-authenticated",
    }


def _checked_analysis_artifact(plan, check_runs, receipt):
    from ladon.proof_contract_rational_probes import RATIONAL_BRANCH_PROFILE_DIGEST
    from ladon.proofir_v3 import make_envelope

    analysis_id = _digest_text({"planId": plan["planId"], "receipt": receipt})
    plan_artifact = plan["artifact"]
    check_run_refs = copy.deepcopy(receipt["checkRunRefs"])
    limitations = [
        {"id": "source-formula-fidelity-unverified",
         "message": "Checked branch predicates have not been shown faithful to the cited prose."},
        {"id": "finite-assignment-only",
         "message": "The checks concern generated goals for one supplied rational assignment."},
        {"id": "original-claim-not-refuted",
         "message": "This checked result does not prove or refute the original theorem."},
    ]
    return make_envelope(
        artifact_kind="proofir.contract-analysis",
        producer={"name": "ladon-rational-branch-check", "version": "1"},
        environment_ref=plan["workspaceIdentity"],
        subject_refs=[{"kind": "contract-analysis", "localId": analysis_id}],
        coverage={"status": "complete", "observed": len(check_runs)},
        payload={
            "analysisId": analysis_id,
            "profileDigest": RATIONAL_BRANCH_PROFILE_DIGEST,
            "stage": "rational-branch-check",
            "planRef": {"artifactRef": plan_artifact["artifactId"],
                        "kind": "contract-analysis",
                        "localId": plan["planId"]},
            "branchId": plan["branchId"],
            "result": copy.deepcopy(receipt),
            "checkRunRefs": check_run_refs,
            "residuals": [],
        },
        limitations=limitations,
    ).to_dict()


def _goal_result(row):
    return {
        "goalId": row["goal"]["goalId"],
        "goalDigest": _digest_text(row["goal"]["leanProposition"]),
        "proposition": row["goal"]["leanProposition"], "term": row["term"],
        "termDigest": row["termDigest"], "status": "checked-support",
        "reused": row["reused"], "binding": copy.deepcopy(row["binding"]),
        "result": _result_summary(row["result"]),
    }


def _result_summary(result):
    evidence = result.get("evidence", {}) if isinstance(result, dict) else {}
    completion = evidence.get("completion", {})
    capture = evidence.get("capture", {}).get("capture", {})
    trust = completion.get("trust", {})
    replay = completion.get("replay", {})
    return {
        "status": result.get("status"),
        "generatedProposition": result.get("generatedProposition"),
        "binding": copy.deepcopy(result.get("binding")),
        "completion": copy.deepcopy(result.get("completion", {})),
        "replay": copy.deepcopy(result.get("replay", {})),
        "trust": copy.deepcopy(result.get("trust", {})),
        "captureId": capture.get("captureId"),
        "sourceDigest": evidence.get("sourceDigest"),
        "executionContextIdentity": evidence.get("executionContextIdentity"),
        "leanExecutableDigest": evidence.get("leanExecutableDigest"),
        "observedAxioms": copy.deepcopy(trust.get("observedAxioms")),
        "trustPolicy": trust.get("policy"),
        "replaySourceDigest": replay.get("sourceDigest"),
        "evidenceDigest": _digest_text(evidence) if evidence else None,
    }


def _proof_checker_identity():
    helper = resources.files("ladon").joinpath(
        "lean", "ladon_source_goal_completion_helper.lean").read_bytes()
    return {**_CHECKER, "helperDigest": _digest_bytes(helper),
            "completionPolicy": "independent-replay-no-placeholders-v1"}


def _compiled_inventory_digest(result):
    evidence = result.get("evidence", {}) if isinstance(result, dict) else {}
    capture = evidence.get("capture", {}).get("capture", {})
    environment = capture.get("environment", {})
    inventory = environment.get("compiledInventory")
    if (not isinstance(inventory, (dict, list))
            or (isinstance(inventory, dict)
                and not isinstance(inventory.get("modules"), list))):
        return None
    return _digest_text(inventory)


def _check_run_artifact(plan, row, checker, limits):
    evidence = row["result"].get("evidence")
    if not isinstance(evidence, dict):
        # Unit tests replace the worker boundary. No native checker artifact is
        # emitted unless the real worker supplied process and replay evidence.
        return None
    from ladon.proofir_v3 import make_envelope

    goal = row["goal"]
    token = _digest_text({"planId": plan["planId"], "goalId": goal["goalId"],
                          "termDigest": row["termDigest"]})[7:]
    statement_ref = {"kind": "statement", "localId": "rational-goal:" + token}
    check_ref = {"kind": "check-run", "localId": "rational-check:" + token}
    process_receipts = evidence.get("processReceipts", [])
    if not process_receipts:
        return None
    last = process_receipts[-1]
    executable_digest = evidence.get("leanExecutableDigest")
    if not _is_digest(executable_digest):
        return None
    payload = {
        "checkRunId": check_ref["localId"],
        "checker": {
            "name": checker["name"], "version": checker["version"],
            "implementationDigest": checker["helperDigest"],
            "executableDigest": executable_digest,
        },
        "operation": "rational-branch-generated-goal-completion-and-replay",
        "inputs": {"environmentRef": plan["workspaceIdentity"],
                   "subjectRefs": [statement_ref],
                   "artifactRefs": [plan["artifact"]["artifactId"]]},
        "results": [{"subjectRef": statement_ref, "result": "accepted", "diagnostics": []}],
        "outputs": {"stdoutDigest": last["stdoutDigest"],
                    "stderrDigest": last["stderrDigest"]},
        "bounds": {"timeoutMs": max(1, int(limits["timeout_seconds"] * 1000)),
                   "maxOutputBytes": limits["max_output_bytes"]},
        "guarantee": {
            "scope": "declaration-value",
            "statement": "The exact generated finite-assignment goal passed Lean completion, independent replay, and the no-placeholder trust policy.",
            "authorityBasis": "kernel-check",
        },
    }
    capture = evidence.get("capture", {}).get("capture", {})
    completion = evidence.get("completion", {})
    trust = completion.get("trust", {})
    if trust.get("coverage") != "complete" or trust.get("accepted") is not True:
        return None
    receipt = {
        "status": "accepted",
        "rationalBranchBinding": copy.deepcopy(row["binding"]),
        "resultDigest": _digest_text(row["result"]),
        "evidenceDigest": _digest_text(evidence),
        "capture": {
            "captureId": capture.get("captureId"),
            "sourceDigest": capture.get("source", {}).get("digest"),
            "goalStructuralDigest": _digest_text(
                capture.get("goal", {}).get("typeStructural", "")),
            "executionContextIdentity": capture.get("environment", {}).get("executionContextRef"),
            "compiledInventoryDigest": _digest_text(
                capture.get("environment", {}).get("compiledInventory", [])),
            "compiledModuleCount": _compiled_module_count(
                capture.get("environment", {}).get("compiledInventory", [])),
        },
        "completion": {
            "status": completion.get("status"),
            "termDigest": completion.get("termDigest"),
            "replayStatus": completion.get("replay", {}).get("status"),
            "replaySourceDigest": completion.get("replay", {}).get("sourceDigest"),
            "trustPolicy": "lean-standard-no-placeholders-v1",
            "trustCoverage": trust.get("coverage"),
            "observedAxioms": trust.get("observedAxioms"),
            "trustAccepted": trust.get("accepted"),
        },
        "leanExecutableDigest": executable_digest,
        "executionContextIdentity": evidence.get("executionContextIdentity"),
        "processReceipts": [{key: process.get(key) for key in (
            "command", "returnCode", "peakRssBytes",
            "timedOut", "memoryLimited", "outputLimited", "inputDigest",
            "stdoutDigest", "stderrDigest", "stdoutBytes", "stderrBytes",
        )} | {"elapsedMilliseconds": round(process.get("elapsedSeconds", 0) * 1000)}
            for process in process_receipts],
    }
    return make_envelope(
        artifact_kind="proofir.check-run",
        producer={"name": "ladon-rational-branch-check", "version": "1"},
        environment_ref=plan["workspaceIdentity"],
        subject_refs=[statement_ref, check_ref],
        payload=payload,
        coverage={"status": "complete", "population": {"kind": "artifact-subjects", "selector": {}},
                  "universeKnown": True, "expected": 2, "discovered": 2, "decoded": 2,
                  "valid": 2, "projected": 2, "queryMatched": 2, "omitted": [],
                  "bounds": {"maxSubjects": 16}},
        limitations=[{"id": "generated-goal",
                      "message": "Authority applies only to this generated closed proposition and does not establish source formula fidelity or universal rational validity."}],
        extensions={"ladon.rational-branch-receipt/v1": receipt},
    ).to_dict()


def _compiled_module_count(inventory):
    if isinstance(inventory, dict):
        return len(inventory.get("modules", []))
    if isinstance(inventory, list):
        return len(inventory)
    return 0


def _propagate_stop(plan_result):
    return _stopped(plan_result.get("status", "unsupported"),
                    plan_result.get("reason", "plan-unavailable"),
                    plan_result.get("diagnostic", "Rational branch plan is unavailable."),
                    plan_result)


def _stopped(status, reason, message, plan=None, completed=None, process_receipts=None):
    rows = []
    for row in completed or []:
        rows.append({"goalId": row["goal"]["goalId"], "status": "unresolved",
                     "termDigest": row["termDigest"], "reused": row["reused"]})
    return {
        "schema": "ladon-rational-branch-check-v1", "status": status,
        "reason": reason, "planId": plan.get("planId") if isinstance(plan, dict) else None,
        "goals": rows, "checkedSupport": None, "receipt": None,
        "cache": None, "artifacts": [],
        "sourceFormulaFidelity": "unverified", "originalClaimRefuted": False,
        "diagnostic": str(message)[:1000],
        "processReceipts": process_receipts or [],
    }


def _bounded_result(result, cap):
    from ladon._proof_contract_context_goals import ContextOutputLimit

    if bounded_json_size(result, min(cap, MAX_INPUT_BYTES)) <= min(cap, MAX_INPUT_BYTES):
        return result
    raise ContextOutputLimit("Rational branch check response exceeds its output bound.")


def _digest_text(value):
    if isinstance(value, str):
        raw = value.encode("utf-8")
    else:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return _digest_bytes(raw)


def _digest_bytes(value):
    return _DIGEST_PREFIX + hashlib.sha256(value).hexdigest()


def _is_digest(value):
    return isinstance(value, str) and len(value) == 71 and value.startswith(_DIGEST_PREFIX)


def _digest_matches(actual, expected):
    return _is_digest(actual) and actual == expected
