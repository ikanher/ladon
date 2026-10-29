"""Check both exact obligations in one private compiled environment."""

import json
import sys
from dataclasses import asdict

from ladon.correspondence_check import _check_goal
from ladon.proof_contract_io import _decode
from ladon.proof_contract_payloads import closed
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_admission_worker import (
    MAX_BYTES,
    _accepted,
    _compile,
    _inventory,
    _verify_inventory,
    _workspace,
)
from ladon.real_bound_binding_check import verify_binding_source
from ladon.real_bound_binding_worker import (
    _compile_binding,
    _compile_derivative,
    _compile_helper,
    _derivative,
    _verify_reserved,
)
from ladon.real_bound_native_check import native_checker_identity
from ladon.real_bound_native_plan import SCALAR_SOURCE, validate_real_plan
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message


def _prepare(job):
    validate_real_plan(job["plan"])
    root, source, context = verify_binding_source(job["root"], job["plan"]["bindingPlan"])
    base_job = {**job, "plan": job["plan"]["bindingPlan"]}
    _verify_reserved(context, base_job)
    if any((library / "LadonRealBoundScalars.olean").exists() for library in context.library_roots):
        raise ValueError("reserved Real scalar helper already exists")
    return root, source, _workspace(base_job, root, context), base_job


def _compile_all(job, base_job, workspace, result):
    steps = [_compile, _compile_binding]
    if _derivative(base_job):
        steps.append(_compile_derivative)
    for step in steps:
        actual = step(workspace, base_job)
        result["compilations"].append(asdict(actual))
        if not actual.succeeded:
            return False
    actual = _compile_helper(workspace, job, SCALAR_SOURCE, "scalarSourceDigest")
    result["compilations"].append(asdict(actual))
    return actual.succeeded


def _check_all(job, source, workspace, base_job, result):
    helper = "LadonRealBoundDerivative" if _derivative(base_job) else "LadonRealBoundBinding"
    prefix = f"import {helper}\nimport LadonRealBoundScalars\n".encode()
    inventory = None
    for goal in job["plan"]["goals"]:
        actual = _check_goal(goal["proposition"], job["terms"][goal["id"]], workspace,
                             prefix + source, {}, pinned_toolchain(workspace),
                             workspace_parent=workspace.parent)
        result["checks"].append({"goal": goal, "term": job["terms"][goal["id"]], "evidence": actual})
        if not _accepted(actual):
            return
        current = _inventory(actual)
        if inventory is not None and current != inventory:
            raise ValueError("compiled inventory changed across Real obligations")
        inventory = current
        _verify_inventory(inventory)
        verify_binding_source(job["root"], job["plan"]["bindingPlan"])
    result["status"] = "checked"


def _compute(job):
    closed(job, {"version", "root", "workspace", "plan", "terms", "deadlineMonotonic",
                 "checkerIdentity"}, "Real admission job")
    if job["version"] != 1 or job["checkerIdentity"] != native_checker_identity():
        raise ValueError("stale Real admission checker")
    root, source, workspace, base_job = _prepare(job)
    result = {"schema": "ladon-real-bound-admission-check-v1", "status": "unresolved",
              "plan": job["plan"], "checkerIdentity": job["checkerIdentity"],
              "compilations": [], "checks": []}
    if _compile_all(job, base_job, workspace, result):
        _check_all(job, source, workspace, base_job, result)
    elif result["compilations"][-1]["memory_limited"]:
        result["diagnostic"] = memory_limit_message(DEFAULT_MAX_RSS_BYTES,
                                                   result["compilations"][-1]["peak_rss_bytes"])
    verify_binding_source(root, job["plan"]["bindingPlan"])
    if job["checkerIdentity"] != native_checker_identity():
        raise ValueError("Real checker changed during execution")
    return result


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Real admission input exceeds 8 MiB")
        result = _compute(_decode(raw))
        encoded = json.dumps({"status": "completed", "result": result, "diagnostic": None})
        if len(encoded.encode()) > MAX_BYTES:
            raise ValueError("Real admission output exceeds 8 MiB")
        print(encoded)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        print(json.dumps({"status": "rejected", "result": None, "diagnostic": str(error)[:500]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
