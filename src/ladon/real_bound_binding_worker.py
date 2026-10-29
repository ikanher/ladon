"""Derive laws in Lean from the actual source expression and replay the proof."""

import hashlib
import json
import sys
import time
from dataclasses import asdict

from ladon.correspondence_check import _check_goal
from ladon.derivative_prefix import DERIVATIVE_SOURCE
from ladon.process_supervisor import run_bounded_target_process
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
from ladon.real_bound_binding import BINDING_SOURCE
from ladon.real_bound_binding_check import binding_identity, verify_binding_source
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message
from ladon.semantic_lean_execution import prepare_direct_lean_execution


def _derivative(job):
    return job["plan"]["schema"] == "ladon-derivative-prefix-plan-v1"


def _compile_helper(workspace, job, path, digest_key):
    source = path.read_bytes()
    if "sha256:" + hashlib.sha256(source).hexdigest() != job["plan"][digest_key]:
        raise ValueError("stale bound admission helper")
    (workspace / path.name).write_bytes(source)
    remaining = job["deadlineMonotonic"] - time.monotonic()
    if remaining <= 0:
        raise ValueError("shared bound binding deadline expired")
    execution = prepare_direct_lean_execution(workspace, None, pinned_toolchain(workspace),
                                              require_compiled_module=False)
    return run_bounded_target_process(
        [*execution.command, "-o", f".lake/build/lib/lean/{path.stem}.olean", path.name],
        cwd=workspace, env=execution.environment, timeout_seconds=min(60, remaining),
        max_output_bytes=MAX_BYTES, max_rss_bytes=DEFAULT_MAX_RSS_BYTES)


def _compile_binding(workspace, job):
    return _compile_helper(workspace, job, BINDING_SOURCE, "bindingSourceDigest")


def _compile_derivative(workspace, job):
    return _compile_helper(workspace, job, DERIVATIVE_SOURCE, "derivativeSourceDigest")


def _run_check(job, workspace, source, result):
    goal = job["plan"]["goals"][0]
    helper = "LadonRealBoundDerivative" if _derivative(job) else "LadonRealBoundBinding"
    actual = _check_goal(goal["proposition"], job["term"], workspace,
                         f"import {helper}\n".encode() + source, {}, pinned_toolchain(workspace))
    result["check"] = {"goal": goal, "term": job["term"], "evidence": actual}
    if _accepted(actual):
        _verify_inventory(_inventory(actual))
        result.update(status="checked-binding", predicateAdmission="checked")
        if _derivative(job):
            result["derivativeAdmission"] = "checked"


def _verify_reserved(context, job):
    reserved = ["LadonRealBoundBinding"]
    if _derivative(job):
        reserved.append("LadonRealBoundDerivative")
    if any((library / f"{name}.olean").exists() for library in context.library_roots for name in reserved):
        raise ValueError("selected workspace contains a reserved bound helper module")


def _initial_result(job):
    result = {"schema": "ladon-bound-prefix-check-v1", "status": "unresolved",
              "predicateAdmission": "unresolved", "admission": "unresolved", "contract": None,
              "plan": job["plan"], "checkerIdentity": job["checkerIdentity"],
              "compilations": [], "check": None,
              "limitations": ["historical-receipts-require-fresh-check",
                              "no-scalar-composition-or-paper-norm-interpretation"]}
    steps = [_compile, _compile_binding]
    if _derivative(job):
        result.update(schema="ladon-derivative-prefix-check-v1",
                      derivativeProfile=job["plan"]["derivativeProfile"],
                      derivativeAdmission="unresolved", paperNormBridge="unresolved",
                      limitations=job["plan"]["limitations"][1:] + ["historical-receipts-require-fresh-check"])
        steps.append(_compile_derivative)
    return result, steps


def _compute(job):
    closed(job, {"version", "root", "workspace", "plan", "term", "deadlineMonotonic",
                 "checkerIdentity"}, "bound-prefix job")
    if job["version"] != 1 or job["checkerIdentity"] != binding_identity():
        raise ValueError("stale or unsupported bound-prefix checker")
    root, source, context = verify_binding_source(job["root"], job["plan"])
    _verify_reserved(context, job)
    workspace = _workspace(job, root, context)
    result, steps = _initial_result(job)
    for compile_step in steps:
        compiled = compile_step(workspace, job)
        result["compilations"].append(asdict(compiled))
        if not compiled.succeeded:
            if compiled.memory_limited:
                result["diagnostic"] = memory_limit_message(DEFAULT_MAX_RSS_BYTES, compiled.peak_rss_bytes)
            return result
    _run_check(job, workspace, source, result)
    verify_binding_source(root, job["plan"])
    if job["checkerIdentity"] != binding_identity():
        raise ValueError("bound-prefix checker changed during execution")
    return result


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("bound-prefix input exceeds 8 MiB")
        result = _compute(_decode(raw))
        encoded = json.dumps({"status": "completed", "result": result, "diagnostic": None})
        if len(encoded.encode()) > MAX_BYTES:
            raise ValueError("bound-prefix evidence exceeds 8 MiB")
        print(encoded)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        print(json.dumps({"status": "rejected", "result": None, "diagnostic": str(error)[:500]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
