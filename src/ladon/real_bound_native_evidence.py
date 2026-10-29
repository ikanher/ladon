"""Consistency checks for recorded Real receipts; these do not authenticate history."""

from ladon._proof_contract_lift_evidence import _validate_native_evidence
from ladon.proof_contract_payloads import closed
from ladon.real_bound_admission_worker import _accepted, _inventory
from ladon.real_bound_native_history import validate_recorded_plan


def checked_evidence(plan, run, source_bytes):
    validate_recorded_plan(plan)
    if not isinstance(run, dict) or run.get("status") != "completed":
        raise ValueError("Real evidence requires completed supervised checking")
    result = run.get("result")
    closed(result, {"schema", "status", "plan", "checkerIdentity", "compilations", "checks"},
           "recorded Real check")
    if (result["schema"] != "ladon-real-bound-admission-check-v1"
            or result["status"] != "checked" or result["plan"] != plan):
        raise ValueError("Real evidence differs from the exact admission plan")
    checks = result["checks"]
    if not isinstance(checks, list) or len(checks) != 2:
        raise ValueError("Real evidence requires both predicate and scalar checks")
    _check_pair(plan, checks, source_bytes)
    _receipts(result["compilations"])
    _receipts([run["processReceipt"]])
    return result


def _check_pair(plan, checks, source_bytes):
    inventories = []
    for goal, check in zip(plan["goals"], checks, strict=True):
        closed(check, {"goal", "term", "evidence"}, "recorded obligation check")
        if check["goal"] != goal or not _accepted(check["evidence"]):
            raise ValueError("recorded obligation check does not match the required goal")
        _deep_evidence(check)
        _source_capture(check, plan, source_bytes)
        inventories.append(_inventory(check["evidence"]))
    if inventories[0] != inventories[1]:
        raise ValueError("predicate and scalar evidence have different compiled inventories")


def _deep_evidence(check):
    actual = check["evidence"]
    capture = actual["capture"]["capture"]
    environment = capture["environment"]
    subject = actual["typedSubject"]["subject"]["structural"]
    _validate_native_evidence({"nativeEvidence": {
        "canonicalTypedSubject": subject, "actualTypedSubject": subject,
        "capture": capture, "completion": actual["completion"],
        "compiledInventory": environment["compiledInventory"],
        "environmentRef": environment["executionContextRef"],
        "executableIdentity": environment["executableDigest"],
    }}, {"term": check["term"]})
    _receipts(actual["completion"]["processReceipts"])
    _receipts(actual["capture"]["processReceipts"])


def _receipts(receipts):
    if not isinstance(receipts, list) or not receipts:
        raise ValueError("recorded evidence is missing process receipts")
    for receipt in receipts:
        # Compiler receipts use dataclass spelling; source-goal receipts use JSON spelling.
        success = receipt.get("returnCode", receipt.get("returncode")) == 0
        limited = any(receipt.get(key, False) for key in (
            "timedOut", "memoryLimited", "outputLimited", "timed_out", "memory_limited", "output_limited"))
        if not success or limited:
            raise ValueError("recorded evidence contains an unsuccessful or limited process")


def _source_capture(check, plan, source_bytes):
    import hashlib

    from ladon.correspondence_check import _generated_prelude

    derivative = "derivativeProfile" in plan["bindingPlan"]
    helper = "LadonRealBoundDerivative" if derivative else "LadonRealBoundBinding"
    prefix = f"import {helper}\nimport LadonRealBoundScalars\n".encode()
    proposition = check["goal"]["proposition"]
    prelude = _generated_prelude(None, prefix + source_bytes, {}, proposition)
    generated = (prelude + f"\nexample : {proposition} := by\n  skip\n").encode()
    expected = "sha256:" + hashlib.sha256(generated).hexdigest()
    capture_source = check["evidence"]["capture"]["capture"]["source"]
    if capture_source["digest"] != expected or capture_source["byteLength"] != len(generated):
        raise ValueError("recorded capture does not match the exact source and planned goal")
