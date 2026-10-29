"""Fresh, source-derived Lean checking for exact Real predicate relations."""

import hashlib
import json
import re
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
from ladon.real_bound_binding import _alpha_expression
from ladon.real_bound_binding_check import verify_binding_source
from ladon.real_bound_binding_worker import _compile_binding, _verify_reserved
from ladon.real_bound_native_check import native_checker_identity
from ladon.real_bound_native_plan import SCALAR_SOURCE, validate_real_plan
from ladon.real_bound_native_worker import _compile_helper
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message

_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*\Z")


def _observation(plan):
    return plan["bindingPlan"]["observation"]["statementSnapshot"]


def _relation_goal(left_plan, right_plan):
    left = _observation(left_plan)
    right = _observation(right_plan)
    left_name = left["selection"]["declaration"]
    right_name = right["selection"]["declaration"]
    if not _NAME.fullmatch(left_name) or not _NAME.fullmatch(right_name):
        raise ValueError("Real relation declaration name is unsupported")
    left_expr = json.dumps(_alpha_expression(left["observation"]["normalizedTypeExpr"]),
                           ensure_ascii=False, separators=(",", ":"))
    right_expr = json.dumps(_alpha_expression(right["observation"]["normalizedTypeExpr"]),
                            ensure_ascii=False, separators=(",", ":"))
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    proposition = ("ladon_real_bound_relation% "
                   f"{quote(left_name)} {quote(left_expr)} "
                   f"{quote(right_name)} {quote(right_expr)}")
    return proposition


def _same_source(left, right):
    left_snapshot = _observation(left)
    right_snapshot = _observation(right)
    return (left_snapshot["source"] == right_snapshot["source"]
            and left_snapshot["observation"]["module"]
            == right_snapshot["observation"]["module"])


def _compute(job):
    closed(job, {"version", "root", "workspace", "leftPlan", "rightPlan",
                 "deadlineMonotonic", "checkerIdentity"}, "Real relation job")
    if job["version"] != 1 or job["checkerIdentity"] != native_checker_identity():
        raise ValueError("stale Real relation checker")
    left_plan = job["leftPlan"]
    right_plan = job["rightPlan"]
    validate_real_plan(left_plan)
    validate_real_plan(right_plan)
    root, left_source, context = verify_binding_source(job["root"], left_plan["bindingPlan"])
    right_root, right_source, right_context = verify_binding_source(
        job["root"], right_plan["bindingPlan"]
    )
    result = {"schema": "ladon-real-bound-relation-check-v1", "status": "unresolved",
              "checkerIdentity": job["checkerIdentity"], "leftPlanId": left_plan["planId"],
              "rightPlanId": right_plan["planId"], "goal": None, "term": "by intros; rfl",
              "compilations": [], "check": None,
              "limitations": ["only-definitional-iff-is-proved", "no-source-theorem-proof",
                              "no-paper-norm-bridge"]}
    if not _same_source(left_plan, right_plan) or left_source != right_source:
        result["residual"] = "real-relation-source-context-mismatch"
        return result
    if root != right_root or context.library_roots != right_context.library_roots:
        result["residual"] = "real-relation-environment-mismatch"
        return result
    if any((library / "LadonRealBoundScalars.olean").exists()
           for library in context.library_roots):
        raise ValueError("selected workspace contains the reserved Real scalar module")

    base_job = {**job, "plan": left_plan["bindingPlan"]}
    _verify_reserved(context, base_job)
    workspace = _workspace(base_job, root, context)
    compile_steps = [_compile, _compile_binding]
    for step in compile_steps:
        actual = step(workspace, base_job)
        result["compilations"].append(asdict(actual))
        if not actual.succeeded:
            if actual.memory_limited:
                result["diagnostic"] = memory_limit_message(
                    DEFAULT_MAX_RSS_BYTES, actual.peak_rss_bytes
                )
            result["residual"] = "real-relation-helper-compilation-failed"
            return result
    scalar_job = {**job, "plan": left_plan}
    actual = _compile_helper(workspace, scalar_job, SCALAR_SOURCE, "scalarSourceDigest")
    result["compilations"].append(asdict(actual))
    if not actual.succeeded:
        if actual.memory_limited:
            result["diagnostic"] = memory_limit_message(
                DEFAULT_MAX_RSS_BYTES, actual.peak_rss_bytes
            )
        result["residual"] = "real-relation-helper-compilation-failed"
        return result

    proposition = _relation_goal(left_plan, right_plan)
    result["goal"] = {"proposition": proposition,
                      "sha256": "sha256:" + hashlib.sha256(proposition.encode()).hexdigest()}
    prefix = b"import LadonRealBoundBinding\nimport LadonRealBoundScalars\n"
    evidence = _check_goal(proposition, "by intros; rfl", workspace, prefix + left_source,
                           {}, pinned_toolchain(workspace))
    result["check"] = evidence
    if _accepted(evidence):
        _verify_inventory(_inventory(evidence))
        result["status"] = "checked"
    else:
        result["residual"] = "real-relation-lean-check-unaccepted"
    verify_binding_source(root, left_plan["bindingPlan"])
    verify_binding_source(root, right_plan["bindingPlan"])
    if job["checkerIdentity"] != native_checker_identity():
        raise ValueError("Real relation checker changed during execution")
    return result


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Real relation input exceeds 8 MiB")
        result = _compute(_decode(raw))
        encoded = json.dumps({"status": "completed", "result": result, "diagnostic": None})
        if len(encoded.encode()) > MAX_BYTES:
            raise ValueError("Real relation output exceeds 8 MiB")
        print(encoded)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        print(json.dumps({"status": "rejected", "result": None,
                          "diagnostic": str(error)[:500]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
