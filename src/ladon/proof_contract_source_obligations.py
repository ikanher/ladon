"""Source-bound, conditional construction of one atomic premise goal."""
from __future__ import annotations

import copy
import math
import time
from dataclasses import fields, is_dataclass
from datetime import UTC, datetime
from pathlib import Path

from ladon.proof_contract_formal import produce_formal_snapshot, verify_formal_snapshot
from ladon.proof_contract_obligations import transform_backward_sufficient
from ladon.proof_slice import pinned_toolchain
from ladon.resource_limits import memory_limit_message
from ladon.semantic_candidate_limits import validate_semantic_bounds
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import complete_source_goal

from ._proof_contract_obligations_validation import _parse_deadline
from ._proof_contract_source_obligations_codec import _validate_captured_requirement
from ._proof_contract_source_obligations_formula import _formula_symbols
from ._proof_contract_source_obligations_inputs import bounded_json_size
from ._proof_contract_source_obligations_prefix import check_generated_prefix
from ._proof_contract_source_obligations_roles import (
    _require_supported_symbol_transport,
    _requirement_symbols,
)
from ._proof_contract_source_obligations_staging import CONSTRUCTION_POLICY, _stage_source

MAX_INPUT_BYTES = 8 * 1024**2
_REQUEST_KEYS = {"repoRoot", "parentSnapshot", "providerSnapshot", "parentReadingId",
    "providerReadingId", "desiredReadingId", "backwardRequest", "backwardResult",
    "branchIndex", "premiseOrdinal", "deadlineMonotonic", "limits"}


class SourceResourceLimit(RuntimeError):
    """A shared deadline or supervised resource stop ended construction."""


class SourceIncomplete(ValueError):
    """A verified source uses a feature outside the supported atomic fragment."""


def instantiate_source_bound_premise(request: dict[str, object]) -> dict[str, object]:
    started = time.monotonic()
    try:
        owned = _own_request(request)
        deadline = _effective_deadline(owned)
        _check_deadline(deadline)
        root = Path(owned["repoRoot"]).resolve(strict=True)
        limits = _limits(owned["limits"])
        parent = verify_formal_snapshot(owned["parentSnapshot"], root)
        provider = verify_formal_snapshot(owned["providerSnapshot"], root)
        selected = _select_verified_requirement(owned["backwardRequest"],
            owned["backwardResult"], owned["branchIndex"], owned["premiseOrdinal"])
        _validate_readings(owned, parent)
        _validate_parent_provider_contracts(parent, provider, _btr_request(owned["backwardRequest"]), selected)
        parent_fresh = _fresh_formal_observation(parent, root, _runner(deadline), limits)
        _require_fresh_snapshot_match(parent, parent_fresh)
        _check_deadline(deadline)
        provider_fresh = _fresh_formal_observation(provider, root, _runner(deadline), limits)
        _require_fresh_snapshot_match(provider, provider_fresh)
        _check_deadline(deadline)
        try:
            parent_symbols = _formula_symbols(parent_fresh["observation"]["normalizedTypeExpr"])
            provider_symbols = _formula_symbols(provider_fresh["observation"]["normalizedTypeExpr"])
        except ValueError as error:
            raise SourceIncomplete(str(error)) from error
        requirement_symbols = _requirement_symbols(selected)
        try:
            _require_supported_symbol_transport(parent_symbols, provider_symbols, requirement_symbols)
        except ValueError as error:
            raise SourceIncomplete(str(error)) from error
        expected = {"kind": "forallNat2", **provider_symbols,
                    "offset": selected["contractRecord"]["features"]["regularity"]["offset"]}
        staged = _stage_source(root, parent, provider, expected, owned, deadline)
        (request_digest, source_path, line, column, prefix_digest,
         generated_digest, _generated, prefix_subject) = staged
        context = pinned_toolchain(root)
        if context.context_identity != parent["environment"]:
            raise ValueError("staged source context differs from snapshot environment")
        _check_deadline(deadline)
        prefix_check = check_generated_prefix(
            root, prefix_subject, context.context_identity, limits, _runner(deadline),
        )
        _check_deadline(deadline)
        capture_request = SourceGoalCaptureRequest(repo_root=root, source_path=source_path,
            module="Probe", line=line, column=column, toolchain=context,
            expected_source_digest="sha256:" + generated_digest,
            timeout_seconds=_remaining(deadline, limits["timeout_seconds"]),
            max_output_bytes=limits["max_output_bytes"], max_rss_bytes=limits["max_rss_bytes"])
        captured = capture_source_goal(capture_request, runner=_runner(deadline))
        _check_stage_result(captured)
        _check_capture_binding(captured, source_path, generated_digest, context.context_identity,
                               parent["selection"]["module"], expected, _generated)
        return _result("candidate-goal", "captured-closed-goal", "Candidate source-bound goal captured; no proof was attempted.",
            owned, selected, parent, provider, prefix_digest, generated_digest, captured,
            request_digest=request_digest,
            prefix_check=prefix_check,
            parent_fresh=parent_fresh, provider_fresh=provider_fresh,
            elapsed=time.monotonic()-started)
    except SourceResourceLimit as error:
        return _result("incomplete", "resource-limit", str(error), request, elapsed=time.monotonic()-started)
    except SourceIncomplete as error:
        return _result("incomplete", "unsupported-source-fragment", str(error), request,
                       elapsed=time.monotonic()-started)
    except (TimeoutError, OSError) as error:
        return _result("incomplete", "resource-limit-or-io", str(error), request, elapsed=time.monotonic()-started)
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as error:
        return _result("rejected", "source-bound-validation", str(error), request, elapsed=time.monotonic()-started)


def _own_request(request):
    if not isinstance(request, dict) or set(request) != _REQUEST_KEYS:
        raise TypeError("source-bound request must use the closed mapping schema")
    if bounded_json_size(request, MAX_INPUT_BYTES) > MAX_INPUT_BYTES:
        raise ValueError("source-bound request exceeds the 8 MiB limit")
    copied = copy.deepcopy(request)
    copied["deadlineMonotonic"] = float(copied["deadlineMonotonic"])
    if not math.isfinite(copied["deadlineMonotonic"]):
        raise ValueError("deadlineMonotonic must be finite")
    return copied


def _plain(value):
    if is_dataclass(value):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _limits(limits):
    if not isinstance(limits, dict) or set(limits) != {"timeout_seconds", "max_output_bytes", "max_rss_bytes"}:
        raise ValueError("limits mapping is invalid")
    timeout, output, rss = limits["timeout_seconds"], limits["max_output_bytes"], limits["max_rss_bytes"]
    validate_semantic_bounds(timeout, output, rss)
    if output > MAX_INPUT_BYTES:
        raise ValueError("source-bound observation output exceeds the 8 MiB profile cap")
    return {"timeout_seconds": float(timeout), "max_output_bytes": output,
            "max_rss_bytes": rss}


def _check_deadline(deadline):
    if time.monotonic() >= deadline:
        raise SourceResourceLimit("shared absolute deadline expired")


def _effective_deadline(request):
    outer = request["deadlineMonotonic"]
    backward = _btr_request(request["backwardRequest"])
    bounds = backward.bounds
    if bounds is None:
        return outer
    if not isinstance(bounds, dict):
        raise TypeError("backward bounds must be a mapping")
    inherited = _parse_deadline(bounds.get("deadlineUtc"))
    if inherited is None:
        return outer
    remaining = (inherited - datetime.now(UTC)).total_seconds()
    return min(outer, time.monotonic() + remaining)


def _remaining(deadline, ceiling):
    _check_deadline(deadline)
    return max(0.001, min(ceiling, deadline-time.monotonic()))


def _runner(deadline):
    from ladon.process_supervisor import run_bounded_target_process

    def run(command, *, timeout_seconds, **kwargs):
        remaining = _remaining(deadline, timeout_seconds)
        process = run_bounded_target_process(command, timeout_seconds=remaining, **kwargs)
        _require_process_resources(process, kwargs.get("max_rss_bytes"))
        _check_deadline(deadline)
        return process
    run._ladon_deadline_check = lambda: _check_deadline(deadline)
    return run


def _require_process_resources(process, memory_cap):
    if process.memory_limited:
        raise SourceResourceLimit(memory_limit_message(memory_cap, process.peak_rss_bytes))
    if process.timed_out:
        raise SourceResourceLimit("supervised formal stage timeout")
    if process.output_limited:
        raise SourceResourceLimit("supervised formal stage output limit")


def _select_verified_requirement(request, result, branch_index, premise_ordinal):
    request = _btr_request(request)
    fresh = transform_backward_sufficient(request)
    if _plain(fresh) != _plain(result):
        raise ValueError("backward result differs from exact recomputation")
    if type(branch_index) is not int or type(premise_ordinal) is not int or branch_index < 0 or premise_ordinal < 0:
        raise ValueError("selected branch and premise ordinal must be nonnegative integers")
    try:
        return copy.deepcopy(fresh["branches"][branch_index]["requirements"][premise_ordinal])
    except (IndexError, KeyError, TypeError) as error:
        raise ValueError("selected branch or premise occurrence is absent") from error


def _stable_snapshot_projection(snapshot):
    observation = snapshot.get("observation") or {}
    observed_keys = ("version", "helperVersion", "protocolVersion", "module", "file", "target",
        "status", "leanVersion", "sourceModuleOwned", "declarationRange", "typeExpr",
        "normalizedTypeExpr", "typeFingerprint", "normalizedTypeFingerprint")
    return ({key: snapshot.get(key) for key in ("schema", "channel", "status", "profileDigest", "fidelity")}
    | {"source": snapshot.get("source"), "selection": snapshot.get("selection"),
       "environment": snapshot.get("environment"), "helper": snapshot.get("helper"),
       "observation": {key: observation.get(key) for key in observed_keys},
       "contract": snapshot.get("contract"), "featureOrigins": snapshot.get("featureOrigins"),
       "coverage": snapshot.get("coverage"), "residuals": snapshot.get("residuals"),
       "artifacts": snapshot.get("artifacts")})


def _require_fresh_snapshot_match(supplied, fresh):
    if _stable_snapshot_projection(supplied) != _stable_snapshot_projection(fresh):
        raise ValueError("fresh formal observation differs from supplied snapshot")


def _fresh_formal_observation(snapshot, root, runner, limits):
    _check_deadline_from_runner(runner)
    fresh = produce_formal_snapshot(root, snapshot["source"]["path"],
        snapshot["selection"]["module"], snapshot["selection"]["declaration"],
        timeout_seconds=limits["timeout_seconds"], max_rss_bytes=limits["max_rss_bytes"],
        max_output_bytes=limits["max_output_bytes"], runner=runner)
    if fresh.get("status") != "extracted":
        raise SourceResourceLimit("fresh formal observation unavailable: " + str(fresh.get("status")))
    return fresh


def _check_deadline_from_runner(runner):
    checker = getattr(runner, "_ladon_deadline_check", None)
    if checker:
        checker()


def _validate_readings(request, parent):
    for key in ("parentReadingId", "providerReadingId", "desiredReadingId"):
        if not isinstance(request[key], str) or not request[key] or len(request[key]) > 256:
            raise ValueError("reading identities must be nonempty attributed strings")
    if parent.get("contract") is None:
        raise ValueError("parent snapshot has no recognized contract")


def _validate_parent_provider_contracts(parent, provider, backward_request, selected):
    if backward_request.desired_contract != parent["contract"]:
        raise ValueError("backward desired contract differs from observed parent contract")
    if parent["contract"]["assumptions"] or provider["contract"]["assumptions"]:
        raise ValueError("assumption-bearing source contracts are unsupported")
    target = selected["contractRecord"]
    if target["telescope"] != parent["contract"]["telescope"]:
        raise ValueError("selected requirement changes the parent's quantified context")
    base = copy.deepcopy(provider["contract"])
    base["features"]["regularity"]["offset"] = target["features"]["regularity"]["offset"]
    if base != target:
        raise ValueError("selected requirement changes provider contract beyond the permitted offset")
    if parent["selection"]["module"] != provider["selection"]["module"] or parent["source"] != provider["source"]:
        raise ValueError("parent and provider must be observations in one exact source module")
    parent_start = parent["observation"]["declarationRange"]["startLine"]
    provider_end = provider["observation"]["declarationRange"]["endLine"]
    if provider_end >= parent_start:
        raise ValueError("provider declaration is not wholly before parent declaration")


def _btr_request(request):
    from ladon.proof_contract_obligations import BackwardTransformRequest

    if isinstance(request, BackwardTransformRequest):
        return request
    if not isinstance(request, dict):
        raise TypeError("backward request must be a mapping or BackwardTransformRequest")
    aliases = {"desiredContract": "desired_contract", "ruleEvidence": "rule_evidence",
        "premiseInterfaces": "premise_interfaces", "outputInterface": "output_interface",
        "parameters": "parameters", "choices": "choices", "bounds": "bounds"}
    payload = {aliases.get(key, key): value for key, value in request.items()}
    return BackwardTransformRequest(**payload)


def _check_stage_result(result):
    if result.get("status") == "captured" and isinstance(result.get("capture"), dict):
        return
    diagnostic = result.get("diagnostic", {})
    if result.get("status") in {"timeout", "memory-limit", "output-limit", "process-failed"}:
        raise SourceResourceLimit(str(diagnostic.get("message", result.get("status"))))
    raise ValueError("source capture did not produce a goal")


def _check_capture_binding(result, path, digest, context_id, original_module, expected, generated):
    capture = result["capture"]
    source = capture.get("source", {})
    _check_capture_source(source, path, digest, generated)
    _check_capture_environment(capture, context_id, original_module)
    _validate_captured_requirement(capture, expected)


def _check_capture_source(source, path, digest, generated):
    if source.get("path") != path or source.get("digest") != "sha256:" + digest:
        raise ValueError("capture source differs from generated bytes")
    syntax = source.get("syntaxRange", {})
    start, end = syntax.get("startByte"), syntax.get("endByte")
    if (not isinstance(start, int) or not isinstance(end, int) or end-start != 4
            or generated[start:end] != b"skip"):
        raise ValueError(f"capture syntax range is not the exact generated skip token: {start}:{end}={generated[start:end]!r}")


def _check_capture_environment(capture, context_id, original_module):
    environment = capture.get("environment", {})
    if environment.get("executionContextRef") != context_id:
        raise ValueError("capture context differs from verified source context")
    if capture.get("helper", {}).get("observation", {}).get("useAfter") is not False:
        raise ValueError("in-tactic source guard was not observed before selected goal")
    modules = {row.get("module") for row in environment.get("compiledInventory", {}).get("modules", [])}
    if original_module in modules:
        raise ValueError("original source module is present in generated environment")


def _result(status, code, message, request, selected=None, parent=None, provider=None,
            prefix_digest=None, generated_digest=None, capture=None, *,
            parent_fresh=None, provider_fresh=None, request_digest=None, prefix_check=None,
            elapsed=0.0):
    safe = request if isinstance(request, dict) else {}
    body = {"schema": "ladon-source-bound-premise-v1", "status": status,
        "authority": "conditional-template", "sourceFidelity": "attributed-unreviewed",
        "wholeMethodAuthority": "none", "mathematicalFalsity": "not-established",
        "constructionPolicy": CONSTRUCTION_POLICY,
        "goalOrigin": "generated-backward-requirement",
        "diagnostic": {"code": code, "message": str(message)[:500]},
        "capture": capture.get("capture") if isinstance(capture, dict) else capture,
        "selectedRequirement": _plain(selected) if selected else None,
        "prefixCheck": prefix_check,
        "parentReadingId": _small(safe.get("parentReadingId")),
        "providerReadingId": _small(safe.get("providerReadingId")),
        "desiredReadingId": _small(safe.get("desiredReadingId")),
        "prefixDigest": prefix_digest, "generatedSourceDigest": generated_digest,
        "branchIndex": _ordinal(safe.get("branchIndex")),
        "premiseOrdinal": _ordinal(safe.get("premiseOrdinal")),
        "elapsedSeconds": elapsed, "completionApi": complete_source_goal.__module__}
    body.update(_snapshot_bindings(parent, provider, parent_fresh, provider_fresh))
    body.update(_transform_bindings(safe))
    body["processReceipts"] = _process_receipts(parent_fresh, provider_fresh, prefix_check, capture)
    # Invalid/preflight requests never get recursively serialized again here.
    # Successful requests carry a digest made after their bounded owned copy.
    body["requestDigest"] = request_digest
    return _bounded_result(body)


def _snapshot_bindings(parent, provider, parent_fresh, provider_fresh):
    pairs = (("parentSnapshotId", parent), ("providerSnapshotId", provider),
             ("freshParentSnapshotId", parent_fresh), ("freshProviderSnapshotId", provider_fresh))
    return {key: snapshot.get("snapshotId") if snapshot else None for key, snapshot in pairs}


def _transform_bindings(request):
    result = request.get("backwardResult")
    result = result if isinstance(result, dict) else {}
    return {"backwardRequestDigest": _small(result.get("requestDigest")),
            "backwardResultDigest": _small(result.get("resultDigest"))}


def _process_receipts(parent, provider, prefix_check, captured):
    prefix = prefix_check["snapshot"] if prefix_check else None
    stages = (("parent-statement", parent), ("provider-statement", provider),
              ("generated-prefix", prefix), ("generated-goal", captured))
    return [{**receipt, "operationStage": stage}
            for stage, observed in stages if observed
            for receipt in observed.get("processReceipts", [])]


def _bounded_result(body):
    if bounded_json_size(body, MAX_INPUT_BYTES) <= MAX_INPUT_BYTES:
        return body
    return {"schema": body["schema"], "status": "incomplete", "capture": None,
            "authority": "conditional-template", "sourceFidelity": "attributed-unreviewed",
            "wholeMethodAuthority": "none", "mathematicalFalsity": "not-established",
            "requestDigest": body["requestDigest"], "diagnostic": {
                "code": "result-output-limit", "message": "source-bound result exceeds 8 MiB"}}


def _ordinal(value):
    return value if type(value) is int and 0 <= value < 2**63 else None


def _small(value):
    if isinstance(value, str):
        bounded = value[:256]
        try:
            bounded.encode("utf-8")
        except UnicodeError:
            return None
        return bounded
    if type(value) is int and abs(value) < 2**63:
        return value
    return None




def instantiate_planned_source_leaf_requirement(request: dict[str, object]) -> dict[str, object]:
    """Materialize one exact source leaf from a freshly recomputed route plan."""
    from .proof_contract_planned_source import (
        instantiate_planned_source_leaf_requirement as operation,
    )
    return operation(request)


def _select_verified_plan_requirement(plan_request, plan_result, route_index,
                                     requirement_index, selected_identity):
    from ._proof_contract_planned_source_trace import _select_verified_plan_requirement as select
    return select(plan_request, plan_result, route_index, requirement_index, selected_identity)
