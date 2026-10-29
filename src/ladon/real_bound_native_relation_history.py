"""Reconstruct saved relation evidence; this cannot authenticate its origin."""

import hashlib
import json
import math

from ladon.correspondence_check import _generated_prelude
from ladon.proof_contract_payloads import closed
from ladon.proofir_v3 import _digest
from ladon.real_bound_admission_worker import _accepted
from ladon.real_bound_native_evidence import _deep_evidence, _receipts
from ladon.real_bound_native_relation_worker import _relation_goal
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

_MAX_RUN_BYTES = 8 * 1024**2


def _observation(plan):
    return plan["bindingPlan"]["observation"]["statementSnapshot"]


def _same_context(left, right):
    a, b = _observation(left), _observation(right)
    return (a["source"] == b["source"]
            and a["observation"]["module"] == b["observation"]["module"]
            and a["environment"] == b["environment"])


def _check_result(result, productions):
    closed(result, {"schema", "status", "checkerIdentity", "leftPlanId", "rightPlanId",
                    "goal", "term", "compilations", "check", "limitations"},
           "recorded Real relation check")
    left_plan = productions[0]["request"]["plan"]
    right_plan = productions[1]["request"]["plan"]
    expected = {"schema": "ladon-real-bound-relation-check-v1", "status": "checked",
                "leftPlanId": left_plan["planId"], "rightPlanId": right_plan["planId"],
                "term": "by intros; rfl",
                "limitations": ["only-definitional-iff-is-proved", "no-source-theorem-proof",
                                "no-paper-norm-bridge"]}
    if any(result[key] != value for key, value in expected.items()) or not _same_context(left_plan, right_plan):
        raise ValueError("recorded Real relation does not belong to the ordered owners")
    proposition = _relation_goal(left_plan, right_plan)
    digest = "sha256:" + hashlib.sha256(proposition.encode()).hexdigest()
    if result["goal"] != {"proposition": proposition, "sha256": digest}:
        raise ValueError("recorded Real relation goal differs from its exact owners")
    if not _digest(result["checkerIdentity"]):
        raise ValueError("recorded Real relation checker identity is missing")
    _check_native(result, productions, proposition)


def _check_native(result, productions, proposition):
    compilations = result["compilations"]
    if not isinstance(compilations, list) or len(compilations) != 3:
        raise ValueError("recorded Real relation requires all helper compilations")
    _receipts(compilations)
    check = result["check"]
    if not isinstance(check, dict) or not _accepted(check):
        raise ValueError("recorded Real relation is missing accepted native check evidence")
    _deep_evidence({"term": result["term"], "evidence": check})
    source = productions[0]["sourceText"]
    if source != productions[1]["sourceText"]:
        raise ValueError("recorded relation owners have different source text")
    prefix = b"import LadonRealBoundBinding\nimport LadonRealBoundScalars\n"
    generated = (_generated_prelude(None, prefix + source.encode(), {}, proposition)
                 + f"\nexample : {proposition} := by\n  skip\n").encode()
    capture_source = check["capture"]["capture"]["source"]
    expected_digest = "sha256:" + hashlib.sha256(generated).hexdigest()
    if capture_source.get("digest") != expected_digest or capture_source.get("byteLength") != len(generated):
        raise ValueError("recorded relation capture differs from exact copied source and goal")


def _positive(value, maximum):
    return type(value) in (int, float) and math.isfinite(value) and 0 < value <= maximum


def _outer_receipt(run):
    receipt, bounds = run["processReceipt"], run["bounds"]
    closed(bounds, {"deadlineMonotonic", "effectiveTimeoutSeconds", "max_output_bytes",
                    "max_rss_bytes", "timeout_seconds"}, "Real relation bounds")
    if (not _positive(bounds["timeout_seconds"], 600)
            or not _positive(bounds["effectiveTimeoutSeconds"], bounds["timeout_seconds"])
            or not _positive(bounds["deadlineMonotonic"], float("inf"))):
        raise ValueError("invalid Real relation recorded deadline")
    if bounds["max_output_bytes"] != _MAX_RUN_BYTES or bounds["max_rss_bytes"] != DEFAULT_MAX_RSS_BYTES:
        raise ValueError("Real relation resource bounds differ from the checked policy")
    expected = {"inputDigest": run["workerInputDigest"],
                "requestedTimeoutSeconds": bounds["effectiveTimeoutSeconds"],
                "configuredTimeoutSeconds": bounds["timeout_seconds"],
                "requestedMaxOutputBytes": bounds["max_output_bytes"],
                "requestedMaxRssBytes": bounds["max_rss_bytes"]}
    if any(receipt.get(key) != value for key, value in expected.items()):
        raise ValueError("Real relation receipt differs from its worker input or bounds")
    if not all(_digest(receipt.get(key)) for key in ("stdoutDigest", "stderrDigest")):
        raise ValueError("Real relation receipt is missing output digests")
    _receipts([receipt])


def _run_envelope(run):
    size = len(json.dumps(run, ensure_ascii=False, sort_keys=True, allow_nan=False,
                          separators=(",", ":")).encode())
    if size > _MAX_RUN_BYTES:
        raise ValueError("Real relation run exceeds 8 MiB")
    closed(run, {"schema", "status", "result", "diagnostic", "processReceipt",
                 "workerInputDigest", "bounds"}, "Real relation run")
    if run["schema"] != "ladon-supervised-obligation-planner-v1" or not _digest(run["workerInputDigest"]):
        raise ValueError("invalid recorded Real relation run envelope")
    if (run["status"] != "completed" or not isinstance(run["diagnostic"], dict)
            or run["diagnostic"].get("code") != "completed"):
        raise ValueError("Real relation run is not a completed supervised check")
    _outer_receipt(run)


def checked_relation_evidence(productions, run):
    """Validate a saved relation run against two already-admitted exact owners."""
    if not isinstance(productions, list) or len(productions) != 2:
        raise ValueError("Real relation evidence requires two ordered productions")
    try:
        _run_envelope(run)
        _check_result(run["result"], productions)
    except (TypeError, KeyError, IndexError, AttributeError, RecursionError) as error:
        raise ValueError("malformed recorded Real relation evidence") from error
    return run["result"]
