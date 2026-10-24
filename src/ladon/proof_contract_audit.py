"""Bounded, immutable orchestration for existing proof-contract operations."""
from __future__ import annotations

import math
import os
import time
from pathlib import Path

from ._proof_contract_audit_plan import (
    MAX_STAGES,
    _compact_bytes,
    _load_plan,
    _resolve_refs,
    _root,
    _runtime_identity,
    _sha,
    _source_path,
    _validate_operation_request,
    _validate_plan,
)
from ._proof_contract_audit_store import (
    INPUT_NAME,
    MAX_PLAN_BYTES,
    MAX_STAGE_BYTES,
    PLAN_NAME,
    RUN_NAME,
    _create_run,
    _input_header,
    _json_bytes,
    _optional_json,
    _publish_no_clobber,
    _read_bytes,
    _read_json,
    _reject_symlink_ancestors,
    _run_report,
    _stage_envelope,
    _store_stage,
    _verified_prefix,
    _verify_header,
    _verify_run_receipt,
)
from .proof_contract_obligation_supervision import _execute_job
from .proof_contract_payloads import closed


# Public entry point keeps admission separate from stage execution.
def run_contract_audit(plan, output_dir, *, resume=None, max_stages=64, runner=None):
    """Execute or resume an audit into a previously unused directory."""
    if type(max_stages) is not int or not 1 <= max_stages <= MAX_STAGES:
        raise ValueError("max_stages must be between 1 and 64")
    session = _prepare_session(plan, output_dir, resume, runner)
    if session.get("status") == "stopped":
        return session
    report = _continue_session(session, max_stages, runner)
    _publish_no_clobber(session["out"] / RUN_NAME, _json_bytes(report), MAX_STAGE_BYTES)
    return report

# Freeze manifest bytes before any worker can observe a request.
def _prepare_session(plan, output_dir, resume, runner):
    value, plan_bytes = _load_plan(plan)
    normalized = _validate_plan(value)
    root = _root(normalized["repoRoot"])
    if root is not None:
        for name in normalized["sourceFiles"]:
            _source_path(root, name)
    runtime = _runtime_identity()
    out = Path(output_dir).absolute()
    prior_info = None
    if resume is not None:
        prior_info = _precheck_resume(Path(resume), out, plan_bytes, normalized, runtime)
        clock = _read_json(Path(resume) / INPUT_NAME, MAX_PLAN_BYTES)["clock"]
    else:
        _reject_symlink_ancestors(out)
        if out.exists():
            raise FileExistsError("output directory already exists")
        clock = _new_clock(normalized["limits"]["timeout_seconds"])
    try:
        source_binding = _capture_source_binding(root, normalized["sourceFiles"],
                                                 normalized["limits"], clock, runner)
    except _SourceBindingResourceStop as stop:
        return _publish_binding_stop(out, plan_bytes, normalized, runtime,
                                     clock, prior_info, stop.checked)
    if resume is None:
        _create_run(out, plan_bytes, value, clock, runtime, source_binding, normalized["limits"])
        return _session(out, normalized, runtime, source_binding, clock, [], root, plan_bytes)
    return _resume_session(Path(resume), out, plan_bytes, value, normalized, root,
                           runtime, source_binding)

# Resume paths are inspected without mutating their immutable evidence.
def _precheck_resume(prior, out, plan_bytes, normalized, runtime):
    _reject_symlink_ancestors(prior)
    if prior.is_symlink():
        raise ValueError("resume directory may not be a symlink")
    prior = prior.resolve(strict=True)
    if not prior.is_dir():
        raise ValueError("resume path must be a directory")
    _reject_symlink_ancestors(out)
    if out.exists() or out.resolve() == prior:
        raise FileExistsError("resume output must be a new directory")
    return _inspect_prior_run(prior, plan_bytes, normalized, runtime)


# Header and saved clock checks precede all source-binding processes.
def _inspect_prior_run(prior, plan_bytes, normalized, runtime):
    header = _read_json(prior / INPUT_NAME, MAX_PLAN_BYTES)
    closed(header, {"schema", "planDigest", "clock", "runtimeIdentity", "sourceBinding", "limits"},
           "audit resume header")
    prior_plan = _read_bytes(prior / PLAN_NAME, MAX_PLAN_BYTES)
    if prior_plan != plan_bytes:
        raise ValueError("audit resume plan changed")
    if (header["schema"] != "ladon-contract-audit-inputs-v1"
            or header["planDigest"] != _sha(plan_bytes)
            or header.get("runtimeIdentity") != runtime
            or header.get("limits") != normalized["limits"]):
        raise ValueError("audit resume plan, runtime or limits changed")
    if isinstance(header["sourceBinding"], dict) and header["sourceBinding"].get("status") == "unverified":
        raise ValueError("audit with unverified source binding cannot be resumed")
    _check_clock(header["clock"])
    prefix, prefix_bytes, checked_rows = _verified_prefix(prior, normalized, header)
    old_run = _optional_json(prior / RUN_NAME, MAX_STAGE_BYTES)
    if old_run is not None:
        _verify_run_receipt(old_run, checked_rows, header, normalized)
        _require_resumable(old_run)
    return header, prefix_bytes, prefix


# This outcome carries the supervisor receipt through a stopped run.
class _SourceBindingResourceStop(Exception):
    def __init__(self, checked):
        self.checked = checked

# Source binding is admission evidence, never a refreshed baseline.
def _capture_source_binding(root, source_files, limits, clock, runner):
    if root is None:
        return None
    request = {"repoRoot": str(root), "sourceFiles": source_files,
               "deadlineMonotonic": clock["deadlineMonotonic"],
               "deadlineUtc": clock["deadlineUtc"], "limits": limits}
    job = {"version": 1, "operation": "audit-source-binding", "request": request,
           "analysisId": "source-binding", "deadlineObservation": None}
    bounds = {"timeout_seconds": min(limits["timeout_seconds"], _remaining(clock)),
              "max_output_bytes": limits["max_output_bytes"],
              "max_rss_bytes": limits["max_rss_bytes"],
              "deadlineMonotonic": clock["deadlineMonotonic"]}
    checked = _execute_job(job, bounds, {"receipt": None, "inputDigest": None, "bounds": None},
                           runner, worker_module="ladon.proof_contract_audit_worker")
    if checked["status"] != "completed" or not isinstance(checked.get("result"), dict):
        diagnostic = checked.get("diagnostic") or {}
        if checked.get("status") == "incomplete" and diagnostic.get("code") in {
                "memory-limit", "timeout", "output-limit"}:
            raise _SourceBindingResourceStop(checked)
        raise ValueError(diagnostic.get("message", "bounded source identity capture did not complete"))
    return checked["result"]


# A failed admission is persisted as stopped and cannot be resumed.
def _publish_binding_stop(out, plan_bytes, plan, runtime, clock, prior_info, checked):
    receipt = {"status": "unverified", "processReceipt": checked.get("processReceipt"),
               "workerInputDigest": checked.get("workerInputDigest"),
               "diagnostic": checked.get("diagnostic")}
    if prior_info is None:
        source_binding = {"status": "unverified", "reason": "source-binding-resource-stop"}
        prefix_bytes, rows = {}, []
    else:
        header, prefix_bytes, rows = prior_info
        source_binding = header["sourceBinding"]
    _create_run(out, plan_bytes, plan, clock, runtime, source_binding,
                plan["limits"], copied_prefix=prefix_bytes)
    report = _run_report(plan, clock, runtime, source_binding, rows,
                         _sha(plan_bytes), "stopped",
                         (checked.get("diagnostic") or {}).get("code", "resource-stop"),
                         (checked.get("diagnostic") or {}).get("message", "Source identity admission stopped."),
                         binding_admission=receipt)
    _publish_no_clobber(out / RUN_NAME, _json_bytes(report), MAX_STAGE_BYTES)
    return report

# Reuse only the prefix validated against the prior immutable header.
def _resume_session(prior, out, plan_bytes, value, normalized, root, runtime, source_binding):
    prefix, prefix_bytes, clock = _validate_prior(prior, out, plan_bytes, normalized,
                                                  runtime, source_binding)
    _create_run(out, plan_bytes, value, clock, runtime, source_binding,
                normalized["limits"], copied_prefix=prefix_bytes)
    return _session(out, normalized, runtime, source_binding, clock, prefix, root, plan_bytes)

# Copy stage bytes only after every prior receipt has been checked.
def _validate_prior(prior, out, plan_bytes, normalized, runtime, source_binding):
    _reject_symlink_ancestors(prior)
    _reject_symlink_ancestors(out)
    if prior.is_symlink():
        raise ValueError("resume directory may not be a symlink")
    prior = prior.resolve(strict=True)
    if not prior.is_dir():
        raise ValueError("resume path must be a directory")
    if out.exists() or out.resolve() == prior:
        raise FileExistsError("resume output must be a new directory")
    header = _read_json(prior / INPUT_NAME, MAX_PLAN_BYTES)
    expected = _input_header(plan_bytes, clock=None, runtime=runtime,
                             source_binding=source_binding, limits=normalized["limits"])
    prior_plan_bytes = _read_bytes(prior / PLAN_NAME, MAX_PLAN_BYTES)
    _verify_header(header, expected, plan_bytes, prior_plan_bytes)
    clock = header["clock"]
    _check_clock(clock)
    prefix, prefix_bytes, checked_rows = _verified_prefix(prior, normalized, header)
    old_run = _optional_json(prior / RUN_NAME, MAX_STAGE_BYTES)
    if old_run is not None:
        _verify_run_receipt(old_run, checked_rows, header, normalized)
        _require_resumable(old_run)
    return prefix, prefix_bytes, clock

# Resource stops terminate the run instead of triggering automatic retry.
def _require_resumable(run):
    if run.get("status") == "completed":
        raise ValueError("completed audit cannot be resumed")
    if run.get("status") == "stopped":
        if run.get("code") == "memory-limit":
            raise ValueError("memory-stopped audit cannot be resumed; report the stop to the user")
        raise ValueError("stopped audit cannot be resumed")

# Session state holds the original plan bytes and the captured identity.
def _session(out, plan, runtime, source_binding, clock, prefix, root, plan_bytes):
    return {"out": out, "plan": plan, "runtime": runtime,
            "sourceBinding": source_binding, "clock": clock, "prefix": prefix, "root": root,
            "planBytes": plan_bytes}

# Stage dispatch is serial and bounded by the shared run clock.
def _continue_session(session, max_stages, runner):
    normalized, out = session["plan"], session["out"]
    clock, runtime = session["clock"], session["runtime"]
    source_binding, prefix = session["sourceBinding"], session["prefix"]
    root = session["root"]

    stages = normalized["stages"]
    results = {row["id"]: _read_json(out / "stages" / f"{row['id']}.json", MAX_STAGE_BYTES)["result"]
               for row in prefix}
    records = [{"id": row["id"], "status": "reused", "resultDigest": row["resultDigest"],
                "envelopeDigest": row["envelopeDigest"]}
               for row in prefix]
    start = len(prefix)
    terminal_code = None
    terminal_message = None
    terminal_status = "completed"
    stop_index = min(len(stages), start + max_stages)
    total_bytes = sum(len((out / "stages" / f"{row['id']}.json").read_bytes()) for row in prefix)

    for stage in stages[start:stop_index]:
        if _expired(clock):
            terminal_status, terminal_code = "partial", "timeout"
            terminal_message = "Shared audit deadline expired; completed evidence is retained with no retry."
            break
        outcome = _execute_stage(stage, normalized, root, results, clock, out,
                                 total_bytes, runtime, source_binding, runner)
        records.append(outcome["record"])
        total_bytes += outcome["bytes"]
        if outcome["status"] != "completed":
            terminal_status, terminal_code = outcome["runStatus"], outcome["code"]
            terminal_message = outcome["message"]
            break
        results[stage["id"]] = outcome["result"]

    if terminal_status == "completed" and stop_index < len(stages) and len(records) < len(stages):
        terminal_status, terminal_code = "partial", "stage-checkpoint"
        terminal_message = "Stage checkpoint reached; resume into a new directory to continue."
    plan_digest = _sha(session["planBytes"])
    report = _run_report(normalized, clock, runtime, source_binding, records,
                         plan_digest,
                         terminal_status, terminal_code, terminal_message)
    return report

# Each stage binds both source and runtime identity around dispatch.
def _execute_stage(stage, plan, root, results, clock, out, total_bytes,
                   runtime, source_binding, runner):
    request = _resolve_refs(stage["request"], results)
    _validate_operation_request(stage["operation"], request, plan, root)
    job_request = {"operation": stage["operation"], "request": request,
                   "repoRoot": str(root) if root else None,
                   "sourceFiles": plan["sourceFiles"],
                   "deadlineMonotonic": clock["deadlineMonotonic"],
                   "deadlineUtc": clock["deadlineUtc"], "limits": plan["limits"],
                   "expectedSourceBinding": source_binding}
    job = {"version": 1, "operation": "audit-stage", "request": job_request,
           "analysisId": stage["id"], "deadlineObservation": None}
    bounds = {"timeout_seconds": min(plan["limits"]["timeout_seconds"], _remaining(clock)),
              "max_output_bytes": plan["limits"]["max_output_bytes"],
              "max_rss_bytes": plan["limits"]["max_rss_bytes"],
              "deadlineMonotonic": clock["deadlineMonotonic"]}
    state = {"receipt": None, "inputDigest": None, "bounds": None}
    if _runtime_identity() != runtime:
        checked = _runtime_changed(None, job, bounds)
    else:
        checked = _execute_job(job, bounds, state, runner,
                               worker_module="ladon.proof_contract_audit_worker")
        if _runtime_identity() != runtime:
            checked = _runtime_changed(checked, job, bounds)
    return _store_checked_stage(stage, job_request, checked, out, total_bytes)

# Preserve child evidence while refusing identity-drift completion.
def _runtime_changed(checked, job, bounds):
    return {"status": "incomplete", "result": checked.get("result") if checked else None,
            "diagnostic": {"code": "runtime-identity-changed",
                           "message": "Ladon runtime identity changed during stage dispatch."},
            "processReceipt": checked.get("processReceipt") if checked else None,
            "workerInputDigest": (checked.get("workerInputDigest") if checked
                                  else "sha256:" + _sha(_compact_bytes(job))),
            "bounds": checked.get("bounds") if checked else bounds}

# Partial child results remain available for audit and later review.
def _store_checked_stage(stage, job_request, checked, out, total_bytes):
    child = checked.get("result")
    memory_message = _child_memory_stop(checked, child)
    if memory_message is not None:
        return _publish_stage(stage, job_request, checked, child, "stopped", out, total_bytes,
                              "stopped", "memory-limit", memory_message)
    code = checked.get("diagnostic", {}).get("code")
    if code == "memory-limit":
        message = checked["diagnostic"]["message"]
        return _publish_stage(stage, job_request, checked, None, "stopped", out, total_bytes,
                              "stopped", "memory-limit", message)
    if checked["status"] != "completed":
        message = checked.get("diagnostic", {}).get("message", "Stage did not complete.")
        return _publish_stage(stage, job_request, checked, child, "partial", out, total_bytes,
                              "partial", code or "stage-incomplete", message)
    child = checked.get("result")
    if not isinstance(child, dict):
        raise TypeError("audit worker returned no structured operation result")
    status, code, message = _child_outcome(stage["operation"], job_request["request"], child)
    return _publish_stage(stage, job_request, checked, child, status, out, total_bytes,
                          "completed" if status == "completed" else "partial", code, message)

def _child_memory_stop(checked, child):
    if not isinstance(child, dict):
        return None
    diagnostic = child.get("diagnostic")
    if (child.get("status") == "incomplete" and isinstance(diagnostic, dict)
            and diagnostic.get("code") == "memory-limit"):
        return diagnostic.get("message", "Child process stopped at its memory limit.")
    if (checked["status"] != "completed" and child.get("status") == "incomplete"
            and child.get("code") == "memory-limit"):
        return child.get("message", "Child process stopped at its memory limit.")
    if child.get("status") == "incomplete" and child.get("code") == "memory-limit":
        return child.get("message", "Child process stopped at its memory limit.")
    return _formal_child_memory_stop(child)


def _formal_child_memory_stop(child):
    residuals = child.get("residuals")
    receipts = child.get("processReceipts")
    if not isinstance(residuals, list) or not isinstance(receipts, list):
        return None
    if not any(_memory_receipt(receipt) for receipt in receipts if isinstance(receipt, dict)):
        return None
    for residual in residuals:
        if isinstance(residual, dict) and residual.get("code") in {
                "memory-limit", "lean-memory-limit"}:
            return residual.get("message", "Child process stopped at its memory limit.")
    return None


def _memory_receipt(receipt):
    return receipt.get("memoryLimited") is True or receipt.get("memory_limited") is True

# Checkpoint rows describe only artifacts already stored atomically.
def _publish_stage(stage, request, checked, result, status, out, total_bytes,
                   run_status, code, message):
    envelope = _stage_envelope(stage, request, checked, result, status)
    digest, size, envelope_digest = _store_stage(out, stage["id"], envelope, total_bytes)
    record = {"id": stage["id"], "status": status, "resultDigest": digest,
              "envelopeDigest": envelope_digest}
    return {"record": record, "bytes": size, "status": status, "runStatus": run_status,
            "code": code, "message": message, "result": result}

# Linux boot identity prevents monotonic deadlines crossing a reboot.
def _boot_identity():
    path = Path("/proc/sys/kernel/random/boot_id")
    descriptor = None
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
        raw = os.read(descriptor, 129)
        if len(raw) > 128:
            raise ValueError("audit boot identity exceeds its byte bound")
        value = raw.decode("ascii").strip()
    except OSError as error:
        raise ValueError("audit resume requires a readable Linux boot identity") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if not value:
        raise ValueError("audit boot identity is empty")
    return value

def _new_clock(seconds):
    now_utc = time.time()
    return {"createdUtc": now_utc, "deadlineUtc": now_utc + seconds,
            "deadlineMonotonic": time.monotonic() + seconds,
            "bootIdentity": _boot_identity()}

# Reject malformed clock scalars before doing deadline arithmetic.
def _check_clock(clock):
    closed(clock, {"createdUtc", "deadlineUtc", "deadlineMonotonic", "bootIdentity"}, "audit clock")
    for key in ("createdUtc", "deadlineUtc", "deadlineMonotonic"):
        value = clock[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("audit clock fields must be finite numbers")
    if not isinstance(clock["bootIdentity"], str) or not clock["bootIdentity"]:
        raise ValueError("audit boot identity is malformed")
    if clock["bootIdentity"] != _boot_identity():
        raise ValueError("audit cannot resume across host boots")
    if _remaining(clock) <= 0:
        raise ValueError("original audit deadline has expired")
    if time.time() < clock["createdUtc"]:
        raise ValueError("wall clock moved before original audit creation")

# The wall and monotonic deadlines jointly cap every operation.
def _remaining(clock):
    return min(clock["deadlineMonotonic"] - time.monotonic(), clock["deadlineUtc"] - time.time())

def _expired(clock):
    return _remaining(clock) <= 0

# Only recognized completed child contracts advance the plan.
def _child_outcome(operation, request, result):
    if operation == "refine":
        return "unsupported", "refinement-unavailable", "Refinement child is not implemented; no refinement was executed."
    status = result.get("status")
    if status in {"unsupported", "rejected", "incomplete", "unresolved", "unavailable", "failed", "partial"}:
        return "partial", str(result.get("code") or status), str(result.get("message") or "Child stage did not complete.")
    if result.get("coverage", {}).get("status") == "partial":
        return "partial", "child-partial", "Child operation retained partial coverage."
    if not _known_child_success(operation, request, result):
        return "partial", "child-result-shape", "Child returned no recognized complete result shape."
    return "completed", None, None

def _known_child_success(operation, request, result):
    if operation in {"produce-prose", "produce-formal"}:
        return _known_production_success(operation, result)
    if operation in {"propagate", "obligations"}:
        return _known_graph_success(operation, result)
    if operation == "probe":
        return result.get("schema") == "ladon-application-probe-v1" and result.get("status") == "planned"
    if operation == "check-probe":
        return (result.get("schema") == "ladon-application-probe-v1"
                and result.get("status") in {"checked-local-implication", "checked-local-nonimplication"})
    return operation == "inspect" and _known_inspection_success(request, result)


def _known_production_success(operation, result):
    channel = "prose" if operation == "produce-prose" else "formal"
    return (result.get("schema") == "ladon-contract-production-v1"
            and result.get("channel") == channel and isinstance(result.get("snapshotId"), str)
            and result.get("status") not in {"unavailable", "partial", "rejected"})


def _known_graph_success(operation, result):
    expected_stage = "propagation" if operation == "propagate" else "obligations"
    return (result.get("artifactKind") == "proofir.contract-analysis"
            and result.get("payload", {}).get("stage") == expected_stage
            and result.get("coverage", {}).get("status") == "complete")


def _known_inspection_success(request, result):
    if set(request) == {"snapshot"}:
        return (result.get("schema") == "ladon-contract-production-v1"
                and isinstance(result.get("snapshotId"), str)
                and result.get("channel") in {"prose", "formal"})
    if result.get("schema") == "ladon-application-probe-v1":
        return result.get("status") in {"planned", "checked-local-implication",
                                         "checked-local-nonimplication"}
    return (result.get("artifactKind") == "proofir.contract-analysis"
            and isinstance(result.get("payload"), dict)
            and result.get("coverage", {}).get("status") == "complete")
