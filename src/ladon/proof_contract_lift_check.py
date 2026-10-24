"""Public owner boundary for bounded Nat/rational lift verification."""
from __future__ import annotations

import hashlib
import json
import math
import re
import secrets
import time
from pathlib import Path

from ._proof_contract_lift_evidence import _validate_native_evidence

MAX_INPUT_BYTES = 1024**2
MAX_OUTPUT_BYTES = 8 * 1024**2
MAX_TERM_BYTES = 256 * 1024
_DEFAULT_LIMITS = {"timeout_seconds": 120, "max_output_bytes": MAX_OUTPUT_BYTES,
                   "max_rss_bytes": 12 * 1024**3}


def check_nat_rational_lift(request, plan_id, term):
    """Regenerate, supervise and independently bind one lift proof attempt."""
    witness = _usable_witness(request)
    try:
        request, plan_id, term, owned, plan, bounds = _owned_plan(request, plan_id, term)
        return _check_owned(owned, plan_id, term, plan, bounds, witness)
    except _StaleInput as error:
        return _result("stale-input", None, witness, str(error), code="stale-input")
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, RecursionError,
            UnicodeError) as error:
        message = str(error)
        code = next((candidate for candidate in ("semantic-goal-mismatch", "proof-rejected", "trust-rejected")
                     if candidate in message), "invalid-lift-request")
        return _result("rejected", None, witness, message, code=code)


def _owned_plan(request, plan_id, term):
    aggregate = _bounded_json({"request": request, "planId": plan_id, "term": term},
                              "lift-check request")
    request, plan_id, term = aggregate["request"], aggregate["planId"], aggregate["term"]
    owned, plan, bounds = _prepare(request, plan_id, term)
    return request, plan_id, term, owned, plan, bounds


def _check_owned(owned, plan_id, term, plan, bounds, witness):
    if plan["status"] == "unsupported":
        return _result("unsupported", plan, witness, "profile is outside the checked Nat/rational fragment")
    if bounds["deadlineMonotonic"] <= time.monotonic():
        return _result("incomplete", plan, witness, "Shared lift-check deadline expired.", code="timeout")
    checker = _checker_identity()
    job = _worker_job(owned, plan_id, term, checker)
    supervised = _run(job, bounds)
    return _project_supervised(supervised, job, plan, owned, checker, witness)


def _worker_job(owned, plan_id, term, checker):
    job = {"version": 1, "operation": "check-nat-rational-lift", "request": owned,
           "expectedPlanId": plan_id, "term": term, "attemptId": secrets.token_hex(16),
           "checkerIdentity": checker}
    data = json.dumps(job, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("aggregate lift-check input exceeds 1 MiB")
    return job


def _project_supervised(supervised, job, plan, owned, checker, witness):
    if supervised["status"] != "completed":
        return _supervisor_failure(supervised, plan, witness)
    native = supervised["result"]
    if native["status"] != "completed":
        return _native_failure(native, plan, witness, supervised)
    _validate_binding(native, job, plan, owned)
    _validate_native_evidence(native, job)
    _freshness(owned, checker, native)
    return _positive_result(native, plan, owned, witness, supervised)


def _positive_result(native, plan, owned, witness, supervised):
    realized = owned["mode"] == "realization"
    status = "lifted-counterexample" if realized else "spurious-countermodel"
    result = _result(status, plan, witness, None, supervision=_supervision(supervised))
    evidence = native["nativeEvidence"]
    result.update({"formalClaimRefuted": realized, "sourceVerified": True,
                   "nativeEvidence": evidence, "binding": native["binding"],
                   "realizationEvidence": evidence if realized else None,
                   "spuriousnessEvidence": None if realized else evidence,
                   "checkId": _digest(json.dumps(native, sort_keys=True, separators=(",", ":"),
                                          ensure_ascii=False).encode("utf-8"))})
    return _bound_result(result, witness, plan)


def _supervisor_failure(supervised, plan, witness):
    diagnostic = supervised.get("diagnostic") or {}
    code = diagnostic.get("code", "worker-rejected")
    status = "incomplete" if supervised["status"] == "incomplete" else "unresolved"
    if code == "stale-input":
        status = "stale-input"
    return _result(status, plan, witness,
                   diagnostic.get("message", "native lift worker rejected its request"),
                   code=code, supervision=_supervision(supervised))


def _native_failure(native, plan, witness, supervised):
    code = native.get("diagnosticCode", "proof-rejected")
    status = "unresolved"
    if native.get("status") == "stale-input" or code == "stale-input":
        status = "stale-input"
    elif (native.get("status") == "incomplete"
          or code in {"timeout", "memory-limit", "output-limit", "resource-limit", "incomplete"}):
        status = "incomplete"
    elif native.get("status") == "unsupported" or code in {
            "unsupported-profile", "unsupported-canonical-goal", "canonical-environment-coverage",
            "unsupported-canonical-environment-coverage"}:
        status = "unsupported"
    elif code in {"semantic-goal-mismatch", "proof-rejected", "trust-rejected"}:
        status = "rejected"
    return _result(status, plan, witness,
                   native.get("diagnostic", "native proof did not establish a checked classification"),
                   code=code, supervision=_supervision(supervised))


def _prepare(request, plan_id, term):
    plan = _regenerate_plan(request)
    _validate_plan_id(plan_id, plan)
    _verified_root(request)
    deadline = _deadline(request)
    bounds = _resource_bounds(request["limits"])
    _validate_term(term, plan)
    owned = _owned_request(request)
    _check_input_size(owned, plan_id, term)
    from .proof_contract_source_obligations import _limits
    return owned, plan, {**_limits(bounds), "deadlineMonotonic": deadline}


def _regenerate_plan(request):
    if not isinstance(request, dict):
        raise TypeError("request must be an object")
    from .proof_contract_payloads import closed
    closed(request, {"repoRoot", "goal", "witness", "interpretation", "mode",
                     "deadlineMonotonic", "limits"}, "lift request")
    from .proof_contract_lift_goals import plan_nat_rational_lift
    return plan_nat_rational_lift(request["goal"], request["witness"],
                                  request["interpretation"], mode=request["mode"])


def _validate_plan_id(plan_id, plan):
    if (type(plan_id) is not str or re.fullmatch(r"sha256:[0-9a-f]{64}", plan_id) is None
            or plan_id != plan["planId"]):
        raise _StaleInput("supplied plan identity differs from regenerated plan")


def _verified_root(request):
    if type(request["repoRoot"]) is not str:
        raise TypeError("repoRoot must be a path string")
    root = Path(request["repoRoot"]).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("repoRoot must be an existing directory")
    _source(root, request["interpretation"]["source"])
    return root


def _deadline(request):
    deadline = request["deadlineMonotonic"]
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("deadlineMonotonic must be one finite absolute deadline")
    return float(deadline)


def _resource_bounds(limits):
    if type(limits) is not dict or set(limits) - set(_DEFAULT_LIMITS):
        raise ValueError("limits contains unsupported resource fields")
    return {**_DEFAULT_LIMITS,
            **{key: _bounded_limit(key, value) for key, value in limits.items()}}


def _bounded_limit(key, value):
    if key == "timeout_seconds":
        valid = type(value) in (int, float) and math.isfinite(value) and value > 0
        if not valid:
            raise ValueError("timeout_seconds must be positive and finite")
    elif type(value) is not int or value <= 0:
        raise ValueError(f"{key} must be a positive integer")
    if key == "max_output_bytes" and value > _DEFAULT_LIMITS[key]:
        raise ValueError("max_output_bytes exceeds the 8 MiB profile cap")
    return min(value, _DEFAULT_LIMITS[key])


def _validate_term(term, plan):
    if plan["status"] == "planned" and _invalid_term(term):
        raise ValueError("planned mode requires a nonempty UTF-8 term of at most 256 KiB")
    if plan["status"] == "unsupported" and term is not None and _invalid_bounded_text(term):
        raise ValueError("unsupported plan term must be null or bounded text")


def _invalid_term(term):
    return not isinstance(term, str) or not term.strip() or len(term.encode("utf-8")) > MAX_TERM_BYTES


def _invalid_bounded_text(term):
    return not isinstance(term, str) or len(term.encode("utf-8")) > MAX_TERM_BYTES


def _owned_request(request):
    return {key: request[key] for key in ("repoRoot", "goal", "witness", "interpretation", "mode",
                                           "deadlineMonotonic", "limits")}


def _check_input_size(owned, plan_id, term):
    data = json.dumps({"owned": owned, "planId": plan_id, "term": term},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("aggregate lift-check input exceeds 1 MiB")


def _run(job, bounds):
    from .proof_contract_obligation_supervision import _execute_job
    state = {"receipt": None, "inputDigest": None, "bounds": None}
    return _execute_job(job, bounds, state, None,
                        worker_module="ladon.proof_contract_lift_worker")


def _bounded_json(value, label):
    from .proof_contract_refinement import _bounded_json as copy_bounded_json
    return copy_bounded_json(value, label)


def _supervision(result):
    return {"processReceipt": result.get("processReceipt"),
            "workerInputDigest": result.get("workerInputDigest"),
            "bounds": result.get("bounds")}


def _validate_binding(native, job, plan, request):
    if not isinstance(native, dict):
        raise TypeError("worker result is not an object")
    binding = native.get("binding")
    expected = {"attemptId": job["attemptId"], "checkerIdentity": job["checkerIdentity"],
                "planId": plan["planId"], "goal": request["goal"],
                "witness": plan["witness"], "interpretation": request["interpretation"],
                "mode": request["mode"], "termDigest": _digest(job["term"].encode()),
                "root": str(Path(request["repoRoot"]).resolve(strict=True)),
                "source": request["interpretation"]["source"]}
    expected["sourceDigest"] = _digest(_source(
        Path(request["repoRoot"]).resolve(strict=True), request["interpretation"]["source"]))
    if type(binding) is not dict or set(binding) != set(expected):
        raise ValueError("worker result binding is not closed")
    if any(binding.get(k) != v for k, v in expected.items()):
        raise ValueError("worker result binding does not match this lift attempt")
    if native.get("planId") != plan["planId"] or native.get("witness") != plan["witness"]:
        raise ValueError("worker plan or witness binding changed")


def _freshness(request, checker, native):
    root = Path(request["repoRoot"]).resolve(strict=True)
    _source(root, request["interpretation"]["source"])
    from .proof_slice import pinned_toolchain
    if native["nativeEvidence"]["environmentRef"] != pinned_toolchain(root).context_identity:
        raise _StaleInput("pinned context changed after worker completion")
    if _checker_identity() != checker:
        raise _StaleInput("checker identity changed after worker completion")


def _source(root, reference):
    from .source_association_io import _read_regular, _safe_repo_file
    path = _safe_repo_file(root, reference["path"])
    data = _read_regular(path, 8 * 1024**2)
    if hashlib.sha256(data).hexdigest() != reference["sha256"]:
        raise _StaleInput("source digest changed after planning")
    data.decode("utf-8")
    return data


class _StaleInput(ValueError):
    """Owned source or execution context no longer matches the checked input."""


def _checker_identity():
    from .proof_contract_lift_worker import _checker_identity as worker_identity
    return worker_identity()


def _usable_witness(request):
    if type(request) is not dict or type(request.get("witness")) is not dict:
        return None
    try:
        from .proof_contract_refinement import _validate_abstract_witness
        return _validate_abstract_witness(request["witness"])
    except (ValueError, TypeError, KeyError, RecursionError, UnicodeError):
        return None


def _result(status, plan, witness, diagnostic, *, code=None, supervision=None):
    witness = plan["witness"] if plan else witness
    return {"schema": "ladon-proof-contract-nat-rational-lift-check-v1", "status": status,
            "planId": plan["planId"] if plan else None, "witness": witness,
            "mode": plan["mode"] if plan else None,
            "evidenceScope": "local-ladon-output",
            "authenticatedExternalCertificate": False,
            "sourceVerified": False, "sourceFormulaFidelity": "unverified",
            "originalClaimRefuted": False, "formalClaimRefuted": False,
            "spuriousnessEvidence": None, "realizationEvidence": None,
            "openObligation": (None if status in {"lifted-counterexample", "spurious-countermodel"}
                               else "checked-realization-or-incompatibility"),
            "diagnostic": None if diagnostic is None else {
                "code": code or status, "message": str(diagnostic)[:1000]},
            "binding": None, "nativeEvidence": None, "supervision": supervision,
            "checkId": None}


def _bound_result(result, witness, plan):
    try:
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode()
    except (ValueError, TypeError, RecursionError, UnicodeError):
        return _result("incomplete", plan, witness, "lift evidence could not be serialized",
                       code="output-limit")
    if len(encoded) <= MAX_OUTPUT_BYTES:
        return result
    return _result("incomplete", plan, witness, "lift evidence exceeded the 8 MiB output cap",
                   code="output-limit")


def _digest(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


