"""Immutable run storage, checkpoint verification, and receipt helpers."""
from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path

from ._proof_contract_audit_plan import _compact_bytes, _json_bytes, _resolve_refs, _sha
from .proof_contract_payloads import closed

RUN_SCHEMA = "ladon-contract-audit-run-v1"
INPUT_NAME = "run-inputs.json"
PLAN_NAME = "plan.json"
RUN_NAME = "run.json"
MAX_PLAN_BYTES = 8 * 1024**2
MAX_STAGE_BYTES = 8 * 1024**2
MAX_TOTAL_STAGE_BYTES = 32 * 1024**2

def _create_run(out, plan_bytes, plan, clock, runtime, source_binding, limits,
                copied_prefix=None):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir()
    (out / "stages").mkdir()
    header = _input_header(plan_bytes, clock=clock, runtime=runtime,
                           source_binding=source_binding, limits=limits)
    _publish_no_clobber(out / INPUT_NAME, _json_bytes(header), MAX_PLAN_BYTES)
    _publish_no_clobber(out / PLAN_NAME, plan_bytes, MAX_PLAN_BYTES)
    if copied_prefix:
        for identifier, data in copied_prefix.items():
            _publish_no_clobber(out / "stages" / f"{identifier}.json", data, MAX_STAGE_BYTES)

def _input_header(plan_bytes, *, clock, runtime, source_binding, limits):
    return {"schema": "ladon-contract-audit-inputs-v1", "planDigest": _sha(plan_bytes),
            "clock": clock,
            "runtimeIdentity": runtime, "sourceBinding": source_binding, "limits": limits}

def _verify_header(header, expected, plan_bytes, prior_plan_bytes):
    closed(header, {"schema", "planDigest", "clock", "runtimeIdentity",
                    "sourceBinding", "limits"}, "audit resume header")
    if (header["schema"] != "ladon-contract-audit-inputs-v1"
            or header["planDigest"] != _sha(plan_bytes)
            or prior_plan_bytes != plan_bytes
            or header["runtimeIdentity"] != expected["runtimeIdentity"]
            or header["sourceBinding"] != expected["sourceBinding"]
            or header["limits"] != expected["limits"]):
        raise ValueError("audit resume plan, runtime, source binding or limits changed")

def _verified_prefix(prior, plan, header):
    _require_safe_directory(prior / "stages")
    run = _optional_json(prior / RUN_NAME, MAX_STAGE_BYTES)
    rows = _prior_rows(prior, plan, run, header)
    prefix, data_by_id, _results, checked_rows = _collect_prefix(prior, plan, rows, header)
    _reject_noncontiguous_artifacts(prior, plan, len(rows))
    return prefix, data_by_id, checked_rows

def _prior_rows(prior, plan, run, header):
    if run is not None:
        if run.get("schema") != RUN_SCHEMA or run.get("planDigest") != header["planDigest"]:
            raise ValueError("prior run receipt does not match its frozen plan")
        rows = run.get("stages")
        if not isinstance(rows, list) or len(rows) > len(plan["stages"]):
            raise ValueError("prior run stage receipts are malformed")
        return rows
    rows = []
    for stage in plan["stages"]:
        path = prior / "stages" / f"{stage['id']}.json"
        if not path.exists() and not path.is_symlink():
            break
        envelope, data = _read_json_with_bytes(path, MAX_STAGE_BYTES)
        rows.append({"id": stage["id"], "status": envelope.get("status"),
                     "resultDigest": envelope.get("resultDigest"),
                     "envelopeDigest": _sha(data)})
    return rows

def _collect_prefix(prior, plan, rows, header):
    prefix, data_by_id, results, checked_rows = [], {}, {}, []
    total = 0
    failed = False
    for index, record in enumerate(rows):
        if index >= len(plan["stages"]) or record.get("id") != plan["stages"][index]["id"]:
            raise ValueError("prior stage order does not match frozen plan")
        if failed:
            raise ValueError("prior run has a stage after a noncompleted stage")
        stage = plan["stages"][index]
        envelope, data, digest = _verified_stage(prior, stage, record, plan, header, results)
        identifier = stage["id"]
        envelope_digest = _sha(data)
        checked_rows.append({"id": identifier, "status": envelope["status"],
                             "resultDigest": digest, "envelopeDigest": envelope_digest})
        if envelope["status"] == "completed":
            results[identifier] = envelope["result"]
            prefix.append({"id": identifier, "status": "completed", "resultDigest": digest,
                           "envelopeDigest": envelope_digest})
            data_by_id[identifier] = data
        else:
            failed = True
        total += len(data)
        if total > MAX_TOTAL_STAGE_BYTES:
            raise ValueError("prior stage results exceed 32 MiB")
    return prefix, data_by_id, results, checked_rows

def _verified_stage(prior, stage, record, plan, header, results):
    identifier = stage["id"]
    path = prior / "stages" / f"{identifier}.json"
    envelope, data = _read_json_with_bytes(path, MAX_STAGE_BYTES)
    _validate_saved_stage(envelope, data, record, identifier)
    if envelope["operation"] != stage["operation"]:
        raise ValueError("prior stage operation differs from frozen plan")
    if (envelope.get("status") not in {"completed", "partial", "stopped"}
            or (record.get("status") in {"completed", "reused"}
                and envelope.get("status") != "completed")
            or (record.get("status") in {"partial", "stopped"}
                and record.get("status") != envelope.get("status"))):
        raise ValueError("prior stage terminal status is invalid")
    _validate_saved_request(envelope, stage, plan, header, results, identifier)
    return envelope, data, envelope["resultDigest"]

def _validate_saved_stage(envelope, data, record, identifier):
    closed(envelope, {"schema", "id", "operation", "status", "request", "workerInputDigest",
                      "processReceipt", "result", "resultDigest", "diagnostic"},
           "prior stage envelope")
    if envelope["schema"] != "ladon-contract-audit-stage-v1":
        raise ValueError("prior stage envelope schema changed")
    _validate_stage_process_receipt(envelope)
    _validate_stage_digests(envelope, data, record, identifier)

def _validate_stage_process_receipt(envelope):
    receipt = envelope["processReceipt"]
    if receipt is None:
        return
    fields = {"command", "returnCode", "elapsedSeconds", "timedOut", "memoryLimited",
              "outputLimited", "peakRssBytes", "inputDigest", "requestedMaxRssBytes",
              "requestedMaxOutputBytes", "requestedTimeoutSeconds", "configuredTimeoutSeconds",
              "stdoutDigest", "stderrDigest"}
    closed(receipt, fields, "prior stage process receipt")
    if receipt["inputDigest"] != envelope["workerInputDigest"]:
        raise ValueError("prior process receipt input digest changed")

def _validate_stage_digests(envelope, data, record, identifier):
    digest = envelope.get("resultDigest")
    if envelope.get("id") != identifier or (record.get("resultDigest") is not None
            and digest != record.get("resultDigest")):
        raise ValueError("prior stage result or digest changed")
    expected = _sha(_json_bytes(envelope["result"])) if envelope.get("result") is not None else None
    if expected != digest:
        raise ValueError("prior stage result or digest changed")
    if record.get("envelopeDigest") is not None and record["envelopeDigest"] != _sha(data):
        raise ValueError("prior stage envelope bytes changed")

def _validate_saved_request(envelope, stage, plan, header, results, identifier):
    request = _resolve_refs(stage["request"], results)
    expected = {"operation": stage["operation"], "request": request,
                "repoRoot": plan["repoRoot"], "sourceFiles": plan["sourceFiles"],
                "deadlineMonotonic": header["clock"]["deadlineMonotonic"],
                "deadlineUtc": header["clock"]["deadlineUtc"], "limits": plan["limits"],
                "expectedSourceBinding": header["sourceBinding"]}
    if envelope.get("request") != expected:
        raise ValueError("prior stage request differs from the frozen plan and parent results")
    job = {"version": 1, "operation": "audit-stage", "request": expected,
           "analysisId": identifier, "deadlineObservation": None}
    if envelope.get("workerInputDigest") != "sha256:" + _sha(_compact_bytes(job)):
        raise ValueError("prior stage worker input digest changed")

def _reject_noncontiguous_artifacts(prior, plan, row_count):
    allowed = {f"{stage['id']}.json" for stage in plan["stages"]}
    for path in (prior / "stages").iterdir():
        if path.name.endswith(".json") and path.name not in allowed:
            raise ValueError("prior run has an unknown stage artifact")
    for stage in plan["stages"][row_count:]:
        path = prior / "stages" / f"{stage['id']}.json"
        if os.path.lexists(path):
            raise ValueError("prior run has a stage artifact after a missing prefix entry")

def _verify_run_receipt(run, checked_rows, header, plan):
    closed(run, {"schema", "status", "code", "message", "planDigest", "stages", "clock",
                 "bounds", "runtimeIdentity", "sourceBinding", "remainingWork",
                 "stagePopulation", "unresolvedStages", "dimensions", "authority",
                 "bindingAdmission"}, "audit run receipt")
    _validate_run_identity(run, header)
    _validate_run_population(run, checked_rows, plan)
    _validate_run_binding(run, header)
    _validate_run_stage_receipts(run, checked_rows)

def _validate_run_identity(run, header):
    if (run["schema"] != RUN_SCHEMA or run["planDigest"] != header["planDigest"]
            or run["status"] not in {"completed", "partial", "stopped"}
            or type(run["remainingWork"]) is not int or run["remainingWork"] < 0):
        raise ValueError("prior audit run receipt has an invalid status or plan identity")

def _validate_run_population(run, checked_rows, plan):
    closed(run["stagePopulation"], {"expected", "attempted", "completed", "remaining"},
           "audit stage population")
    completed = sum(row["status"] == "completed" for row in checked_rows)
    expected_population = {"expected": len(plan["stages"]), "attempted": len(checked_rows),
                          "completed": completed, "remaining": len(plan["stages"]) - completed}
    if run["stagePopulation"] != expected_population or run["remainingWork"] != expected_population["remaining"]:
        raise ValueError("prior run stage population disagrees with its stage receipts")
    _validate_unresolved_population(run, checked_rows, plan, expected_population)

def _validate_unresolved_population(run, checked_rows, plan, population):
    completed_ids = {row["id"] for row in checked_rows if row["status"] == "completed"}
    unresolved = [row["id"] for row in plan["stages"] if row["id"] not in completed_ids]
    if run["unresolvedStages"] != unresolved:
        raise ValueError("prior unresolved stage queue disagrees with its stage receipts")
    if run["status"] == "completed" and population["remaining"] != 0:
        raise ValueError("completed audit receipt has unresolved stages")

def _validate_run_binding(run, header):
    if (run.get("clock") != header["clock"] or run.get("runtimeIdentity") != header["runtimeIdentity"]
            or run.get("sourceBinding") != header["sourceBinding"] or run.get("bounds") != header["limits"]):
        raise ValueError("prior run receipt clock or identities differ from frozen inputs")

def _validate_run_stage_receipts(run, checked_rows):
    actual = run.get("stages", [])
    if not isinstance(actual, list):
        raise TypeError("prior audit stage receipts must be a list")
    for row in actual:
        closed(row, {"id", "status", "resultDigest", "envelopeDigest"},
               "audit stage receipt")
    if len(actual) != len(checked_rows) or any(
            not _stage_receipts_match(actual[index], checked_rows[index])
            for index in range(len(checked_rows))):
        raise ValueError("prior run receipt and immutable stage files disagree")

def _stage_receipts_match(actual, checked):
    if (actual.get("id") != checked["id"]
            or actual.get("resultDigest") != checked["resultDigest"]
            or actual.get("envelopeDigest") != checked["envelopeDigest"]
            or actual.get("status") not in {"completed", "reused", "partial", "stopped"}):
        return False
    if checked["status"] == "completed":
        return actual.get("status") in {"completed", "reused"}
    return actual.get("status") == checked["status"]

def _stage_envelope(stage, request, checked, result, status):
    digest = _sha(_json_bytes(result)) if result is not None else None
    return {"schema": "ladon-contract-audit-stage-v1", "id": stage["id"],
            "operation": stage["operation"], "status": status,
            "request": request, "workerInputDigest": checked.get("workerInputDigest"),
            "processReceipt": checked.get("processReceipt"), "result": result,
            "resultDigest": digest, "diagnostic": checked.get("diagnostic")}

def _store_stage(out, identifier, envelope, total):
    data = _json_bytes(envelope)
    if len(data) > MAX_STAGE_BYTES:
        raise ValueError("stored audit stage envelope exceeds 8 MiB")
    if total + len(data) > MAX_TOTAL_STAGE_BYTES:
        raise ValueError("stored audit stage results exceed 32 MiB")
    _publish_no_clobber(out / "stages" / f"{identifier}.json", data, MAX_STAGE_BYTES)
    return envelope["resultDigest"], len(data), _sha(data)

def _run_report(plan, clock, runtime, source_binding, stages, plan_digest,
                status, code, message, binding_admission=None):
    completed = sum(row.get("status") in {"completed", "reused"} for row in stages)
    remaining = len(plan["stages"]) - completed
    completed_ids = {row["id"] for row in stages if row.get("status") in {"completed", "reused"}}
    unresolved = [row["id"] for row in plan["stages"] if row["id"] not in completed_ids]
    return {"schema": RUN_SCHEMA, "status": status, "code": code, "message": message,
            "planDigest": plan_digest, "stages": stages,
            "clock": clock, "bounds": plan["limits"], "runtimeIdentity": runtime,
            "sourceBinding": source_binding, "remainingWork": remaining,
            "bindingAdmission": binding_admission,
            "stagePopulation": {"expected": len(plan["stages"]), "attempted": len(stages),
                                "completed": completed, "remaining": remaining},
            "unresolvedStages": unresolved,
            "dimensions": {"sourceFidelity": "not-certified", "extractionCompleteness": "not-certified",
                           "routeSupport": "not-inferred", "methodCorrespondence": "not-inferred",
                           "mathematicalFalsity": "not-claimed", "exploredPopulation": "not-claimed"},
            "authority": "bounded orchestration only; stage result authority is unchanged"}

def _optional_json(path, maximum):
    if not os.path.lexists(path):
        return None
    return _read_json(path, maximum)

def _read_json(path, maximum):
    return _read_json_with_bytes(path, maximum)[0]

def _read_json_with_bytes(path, maximum):
    raw = _read_bytes(path, maximum)
    if len(raw) > maximum:
        raise ValueError("audit JSON file exceeds its byte limit")
    return _decode_json(raw), raw

def _read_bytes(path, maximum):
    path = Path(path).absolute()
    _reject_symlink_ancestors(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("audit run files must be regular files")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(maximum + 1)
    finally:
        os.close(descriptor)
    return raw

def _require_safe_directory(path):
    path = Path(path).absolute()
    _reject_symlink_ancestors(path)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError("audit run directories must be real directories")

def _decode_json(raw):
    from .proof_contract_io import _decode
    return _decode(raw)

def _reject_symlink_ancestors(path):
    path = Path(os.path.abspath(path))
    chain = [path, *path.parents]
    for index, current in enumerate(chain):
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise ValueError("audit path may not traverse symlinks")
        if index and not stat.S_ISDIR(info.st_mode):
            raise ValueError("audit path ancestors must be directories")

def _publish_no_clobber(path, data, maximum):
    if len(data) > maximum:
        raise ValueError("audit artifact exceeds its byte limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp",
                                                  dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path, follow_symlinks=False)
        temporary.unlink()
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
