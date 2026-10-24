"""Fixed serializable adapters for bounded audit stages."""
from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from .proof_contract_io import _decode
from .proof_contract_payloads import closed

MAX_BYTES = 8 * 1024**2

def _compute(job):
    closed(job, {"version", "operation", "request", "analysisId", "deadlineObservation"},
           "audit worker job")
    if job["version"] != 1:
        raise ValueError("unsupported audit worker job")
    if job["operation"] == "audit-source-binding":
        return _capture_source_binding(job["request"])
    if job["operation"] != "audit-stage":
        raise ValueError("unsupported audit worker job")
    owned = job["request"]
    closed(owned, {"operation", "request", "repoRoot", "sourceFiles", "deadlineMonotonic", "deadlineUtc", "limits", "expectedSourceBinding"},
           "audit worker request")
    before = _source_binding(owned)
    if before != owned["expectedSourceBinding"]:
        return {"status": "incomplete", "code": "source-identity-changed",
                "message": "Selected source/toolchain identity differs from the frozen run input."}
    if time.monotonic() >= owned["deadlineMonotonic"] or time.time() >= owned["deadlineUtc"]:
        return {"status": "incomplete", "code": "timeout", "message": "Shared audit deadline expired before stage."}
    result = _run(owned)
    after = _source_binding(owned)
    if after != owned["expectedSourceBinding"]:
        return {"status": "incomplete", "code": "source-changed-during-stage",
                "message": "Selected source/toolchain identity changed during stage; result is not accepted."}
    return result

def _capture_source_binding(request):
    closed(request, {"repoRoot", "sourceFiles", "deadlineMonotonic", "deadlineUtc", "limits"},
           "audit source-binding request")
    if time.monotonic() >= request["deadlineMonotonic"] or time.time() >= request["deadlineUtc"]:
        raise ValueError("shared audit deadline expired before source identity capture")
    binding = _source_binding(request)
    if time.monotonic() >= request["deadlineMonotonic"] or time.time() >= request["deadlineUtc"]:
        raise ValueError("shared audit deadline expired during source identity capture")
    return binding

def _source_binding(owned):
    if owned["repoRoot"] is None:
        return None
    from ._proof_contract_audit_plan import _source_binding
    return _source_binding(Path(owned["repoRoot"]), owned["sourceFiles"])

def _run(owned):
    operation, request = owned["operation"], owned["request"]
    root = Path(owned["repoRoot"]) if owned["repoRoot"] is not None else None
    if operation in {"produce-prose", "produce-formal"}:
        return _produce(operation, request, root, owned)
    if operation in {"propagate", "obligations"}:
        return _graph_stage(operation, request, owned)
    if operation in {"probe", "check-probe"}:
        return _probe_stage(operation, request, root, owned)
    if operation == "inspect":
        return _inspect(request, root, owned)
    if operation == "refine":
        return {"status": "unsupported", "code": "refinement-unavailable",
                "message": "Refinement child is not implemented; no refinement was executed."}
    raise ValueError("unknown audit stage operation")

def _produce(operation, request, root, owned):
    if root is None:
        raise ValueError("source production requires a repository root")
    if operation == "produce-prose":
        from .proof_contract_source import produce_prose_contract
        return produce_prose_contract(root, request["interpretation"], request["contract"],
            request["featureOrigins"], alternative_id=request["alternativeId"],
            environment_ref=request["environmentRef"], author=request["author"])
    from .proof_contract_formal import produce_formal_snapshot
    from .semantic_candidate_limits import MAX_SEMANTIC_TIMEOUT_SECONDS
    return produce_formal_snapshot(root, request["sourceFile"], request["module"],
        request["declaration"], timeout_seconds=min(_remaining(owned), MAX_SEMANTIC_TIMEOUT_SECONDS),
        max_rss_bytes=owned["limits"]["max_rss_bytes"],
        max_output_bytes=owned["limits"]["max_output_bytes"])

def _graph_stage(operation, request, owned):
    if operation == "propagate":
        return _propagate(request, owned)
    from .proof_contract_obligation_artifacts import (
        REQUEST_FIELDS,
        obligations_artifact,
        request_from_payload,
    )
    payload = request["request"]
    closed(payload, set(REQUEST_FIELDS.values()), "obligation request")
    bounded = _deadline_bound(payload, owned)
    request_value = request_from_payload(request["graph"], request["contracts"], bounded)
    return obligations_artifact(request_value, analysis_id=request["analysisId"])

def _propagate(request, owned):
    from .proof_contract_artifacts import propagation_artifact
    payload = request["request"]
    closed(payload, {"goalRef", "ruleBindings", "endpointInterfaces", "scopeBindings", "bounds"},
           "propagation stage request")
    bounded = _deadline_bound(payload, owned)
    return propagation_artifact(request["graph"], request["contracts"],
        analysis_id=request["analysisId"], goal_ref=bounded["goalRef"],
        rule_bindings=bounded["ruleBindings"], endpoint_interfaces=bounded["endpointInterfaces"],
        scope_bindings=bounded.get("scopeBindings", ()), bounds=bounded["bounds"])

def _deadline_bound(payload, owned):
    bounded = dict(payload)
    bounds = dict(payload.get("bounds") or {})
    bounds["deadlineUtc"] = _earlier_deadline(bounds.get("deadlineUtc"), owned["deadlineUtc"])
    bounded["bounds"] = bounds
    return bounded

def _probe_stage(operation, request, root, owned):
    from .proof_contract_probes import check_application_probe, plan_application_probe
    from .semantic_candidate_limits import MAX_SEMANTIC_TIMEOUT_SECONDS
    probe = dict(request if operation == "probe" else request["request"])
    limits = dict(owned["limits"])
    limits["timeout_seconds"] = min(limits["timeout_seconds"], MAX_SEMANTIC_TIMEOUT_SECONDS)
    probe.update(repoRoot=str(root), deadlineMonotonic=owned["deadlineMonotonic"],
                 limits=limits)
    if operation == "probe":
        return plan_application_probe(probe)
    return check_application_probe(probe, request["planId"], request["terms"])

def _inspect(request, root, owned):
    if set(request) == {"snapshot"}:
        return _inspect_snapshot(request["snapshot"], root)
    closed(request, {"artifact", "context"}, "native inspection request")
    artifact, context = request["artifact"], request["context"]
    closed(context, {"artifacts"}, "native replay context")
    if not isinstance(context, dict) or not isinstance(context.get("artifacts"), list):
        raise TypeError("native inspect context requires an artifacts list")
    if not isinstance(artifact, dict):
        raise TypeError("native inspect artifact must be an object")
    from .proofir_v3 import validate_envelope_batch
    validate_envelope_batch([*context["artifacts"], artifact])
    return _inspect_analysis(artifact, context, owned)

def _inspect_snapshot(snapshot, root):
    if not isinstance(snapshot, dict) or root is None:
        raise ValueError("source snapshot inspection requires a snapshot and repoRoot")
    if snapshot.get("channel") == "prose":
        from .proof_contract_source import verify_prose_snapshot
        return verify_prose_snapshot(snapshot, root)
    from .proof_contract_formal import verify_formal_snapshot
    return verify_formal_snapshot(snapshot, root)

def _inspect_analysis(artifact, context, owned):
    stage = artifact.get("payload", {}).get("stage")
    if stage == "probes":
        from ._proof_contract_planned_source_inputs import _planned_input_size
        if _planned_input_size({"artifact": artifact, "context": context}) > MAX_BYTES:
            raise ValueError("probe inspection request exceeds 8 MiB")
        owned_probe = {"deadlineMonotonic": owned["deadlineMonotonic"],
                       "limits": owned["limits"]}
        return _inspect_probe(artifact, context, owned_probe)
    if stage == "obligations":
        return _inspect_obligations(artifact, context, owned)
    return artifact

def _inspect_obligations(artifact, context, owned):
    from .proof_contract_obligation_supervision import run_obligation_validation
    from .semantic_candidate_limits import MAX_SEMANTIC_TIMEOUT_SECONDS
    limits = dict(owned["limits"])
    limits["timeout_seconds"] = min(limits["timeout_seconds"], MAX_SEMANTIC_TIMEOUT_SECONDS)
    checked = run_obligation_validation(artifact, context,
        deadline_monotonic=owned["deadlineMonotonic"], limits=limits)
    if checked["status"] != "completed":
        return {"status": "incomplete", "code": checked["diagnostic"]["code"],
                "message": checked["diagnostic"]["message"], "result": checked.get("result"),
                "processReceipt": checked.get("processReceipt"),
                "workerInputDigest": checked.get("workerInputDigest")}
    return checked["result"]

def _inspect_probe(artifact, context, owned):
    # Preserve probe replay semantics while replacing its default 30-second clock.
    from ._proof_contract_planned_source_inputs import _planned_input_size
    from .proof_contract_probes import _stage
    request = {"artifact": artifact, "context": context}
    if _planned_input_size(request) > MAX_BYTES:
        raise ValueError("probe inspection request exceeds 8 MiB")
    checked = _stage("inspect-probe", request, owned)
    return checked["result"] if checked["status"] == "completed" else {
        "status": "incomplete", "code": checked["diagnostic"]["code"],
        "message": checked["diagnostic"]["message"],
        "processReceipt": checked.get("processReceipt"),
        "workerInputDigest": checked.get("workerInputDigest"),
        "result": checked.get("result")}

def _remaining(owned):
    return max(0.001, min(owned["deadlineMonotonic"] - time.monotonic(),
                          owned["deadlineUtc"] - time.time()))

def _utc(epoch):
    return datetime.fromtimestamp(epoch, UTC).isoformat().replace("+00:00", "Z")

def _earlier_deadline(current, audit_expiry):
    inherited = datetime.fromtimestamp(audit_expiry, UTC)
    if current is None:
        return _utc(audit_expiry)
    parsed = datetime.fromisoformat(current)
    if parsed.tzinfo is None:
        raise ValueError("stage deadlineUtc must include a timezone")
    return (parsed if parsed.astimezone(UTC) <= inherited else inherited).isoformat().replace("+00:00", "Z")

def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("audit worker input exceeds 8 MiB")
        outcome = _compute(_decode(raw))
        body = {"status": "completed", "result": outcome, "diagnostic": None}
    except (ValueError, TypeError, KeyError, OSError, OverflowError, RecursionError) as error:
        body = {"status": "rejected", "result": None, "diagnostic": str(error)[:1000]}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) > MAX_BYTES:
        encoded = json.dumps({"status": "rejected", "result": None,
                              "diagnostic": "audit worker result exceeds 8 MiB"})
    sys.stdout.write(encoded)
    return 0 if body["status"] == "completed" else 2

if __name__ == "__main__":
    raise SystemExit(main())
