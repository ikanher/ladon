"""Explicit original-goal completion with independent compiler and trust evidence."""
from __future__ import annotations

import json
import secrets
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from time import monotonic
from typing import Any

from ladon._source_goal_completion_inputs import capture_request_fields, own_capture
from ladon._source_goal_completion_replay import replay_source
from ladon._source_goal_helpers import stage_helper, verify_helper
from ladon._source_goal_inventory import capture_inventory, verify_inventory
from ladon.execution_posture import require_target_execution_policy
from ladon.lean_toolchain import (
    LeanToolchainContext,
    LeanToolchainError,
    verify_toolchain_identities,
)
from ladon.process_supervisor import run_bounded_target_process
from ladon.semantic_candidate_limits import validate_semantic_bounds
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_association_io import _AssociationError, _digest, _read_regular
from ladon.source_goal_capture import (
    MAX_HELPER_BYTES,
    ProcessRunner,
    SourceGoalCaptureRequest,
    _accounting,
    _diagnostic_text,
    _prepare_source,
    _process_status,
    _receipt,
    _unsupported_diagnostic,
    _verify_bytes,
    _verify_source_files,
    capture_source_goal,
)

RESULT_SCHEMA = "ladon-source-goal-completion-result-v1"
ALLOWED_AXIOMS = ("Classical.choice", "Quot.sound", "propext")


@dataclass(frozen=True)
class SourceGoalCompletionRequest:
    repo_root: Path
    capture: Mapping[str, Any]
    term: str
    toolchain: LeanToolchainContext
    timeout_seconds: float = 60.0
    max_output_bytes: int = 8 * 1024**2
    max_rss_bytes: int = 32 * 1024**3
    require_isolation: bool = False

    def __post_init__(self) -> None:
        require_target_execution_policy(require_isolation=self.require_isolation)
        if not isinstance(self.repo_root, Path) or not isinstance(self.toolchain, LeanToolchainContext):
            raise TypeError("completion requires a repository and pinned toolchain")
        if not isinstance(self.capture, Mapping) or not isinstance(self.term, str) or not self.term.strip():
            raise ValueError("completion requires a source capture and nonempty full term")
        validate_semantic_bounds(self.timeout_seconds, self.max_output_bytes, self.max_rss_bytes)


def complete_source_goal(
    request: SourceGoalCompletionRequest, *, runner: ProcessRunner = run_bounded_target_process,
) -> dict[str, Any]:
    started = monotonic()
    result = _initial_result(request)
    receipts = result["processReceipts"]
    try:
        capture = own_capture(request.capture)
        result["captureId"] = capture["captureId"]
        captured_request = _capture_request(request, capture)
        fresh = capture_source_goal(captured_request, runner=runner)
        receipts.extend(fresh["processReceipts"])
        _require_fresh_capture(fresh, capture)
        _complete(request, captured_request, capture, runner, result)
    except _AssociationError as error:
        result["status"] = error.status
        result["diagnostic"] = {"code": error.code, "message": str(error)[:500]}
    except (OSError, ValueError, TypeError, KeyError, LeanToolchainError) as error:
        result["status"] = "unavailable"
        result["diagnostic"] = {"code": "completion-input-or-protocol", "message": str(error)[:500]}
    result["resourceAccounting"] = {
        **_accounting(started, receipts), "elapsedScope": "complete-original-goal-operation",
        "peakRssScope": "supervised-lean-process-tree",
    }
    return result


def _capture_request(request, capture):
    return SourceGoalCaptureRequest(
        repo_root=request.repo_root, toolchain=request.toolchain,
        **capture_request_fields(capture), timeout_seconds=request.timeout_seconds,
        max_output_bytes=request.max_output_bytes, max_rss_bytes=request.max_rss_bytes,
        require_isolation=request.require_isolation,
    )


def _require_fresh_capture(fresh, capture) -> None:
    if fresh["status"] != "captured":
        failure = fresh["diagnostic"]
        status = fresh["status"] if fresh["status"] in {"stale", "timeout", "memory-limit", "output-limit", "process-failed"} else "unavailable"
        raise _AssociationError(status, failure["code"], failure["message"])
    if fresh["capture"] != capture:
        raise _AssociationError("stale", "capture-observation-changed", "fresh goal/context/environment differs from the supplied capture")


def _complete(request, captured_request, capture, runner, result) -> None:
    from ladon._source_goal_completion_protocol import decode_completion, validate_completion

    root, source_path, source = _prepare_source(captured_request)
    helper = Path(str(resources.files("ladon").joinpath("lean", "ladon_source_goal_completion_helper.lean")))
    execution = prepare_direct_lean_execution(root, None, request.toolchain, require_compiled_module=False)
    with tempfile.TemporaryDirectory(prefix="ladon-source-completion-") as directory:
        original_helper = helper
        helper, helper_digest = stage_helper(original_helper, Path(directory))
        snapshot = Path(directory) / source_path.name
        snapshot.write_bytes(source)
        body = _helper_request(capture, snapshot, request.term)
        payload = ("LADON_COMPLETION_REQUEST " + json.dumps(body, sort_keys=True) + "\n").encode()
        process = _run(request, execution, runner, ["--run", str(helper)], payload, result)
        _require_process(process, "application")
        _verify_source_files(source_path, snapshot, source)
        _verify_bytes(helper, helper_digest, MAX_HELPER_BYTES, "completion-helper")
        verify_toolchain_identities(request.toolchain)
        verify_helper(original_helper, helper_digest)
        frame = decode_completion(process.stdout)
        validate_completion(frame, body, capture, request.toolchain, source)
        files, environment, inventory = capture_inventory(request.toolchain, frame)
        if inventory != capture["environment"]["compiledInventory"]:
            raise _AssociationError("stale", "completion-imports-changed", "completion loaded a different compiled closure")
        result["application"] = _application(frame, helper_digest)
        if frame["status"] != "accepted":
            result["status"] = "unavailable" if frame["status"] == "unsupported" else frame["status"]
            result["diagnostic"] = frame["diagnostic"]
            return
        _replay(request, runner, result, execution, Path(directory), frame, body)
        _verify_source_files(source_path, snapshot, source)
        _verify_bytes(helper, helper_digest, MAX_HELPER_BYTES, "completion-helper")
        verify_helper(original_helper, helper_digest)
        verify_inventory(files, environment, inventory)
        verify_toolchain_identities(request.toolchain)


def _helper_request(capture, snapshot, term):
    source = capture["source"]
    return {
        "protocolVersion": "ladon-lean-source-completion-v1/check",
        "contextRef": capture["environment"]["executionContextRef"],
        "module": source["module"], "filename": source["path"],
        "sourceDigest": source["digest"], "snapshotPath": str(snapshot),
        "line": source["position"]["line"], "column": source["position"]["column"],
        "requestId": secrets.token_hex(16), "captureId": capture["captureId"],
        "term": term, "termDigest": _digest(term.encode()), "goalOrdinal": capture["goal"]["ordinal"],
    }


def _run(request, execution, runner, arguments, payload, result):
    process = runner(
        [*execution.command, *arguments], cwd=request.repo_root,
        env=dict(execution.environment), timeout_seconds=request.timeout_seconds,
        max_output_bytes=request.max_output_bytes, max_rss_bytes=request.max_rss_bytes,
        input_bytes=payload,
    )
    result["processReceipts"].append(_receipt(process, payload))
    return process


def _require_process(process, phase):
    if not process.succeeded:
        status = _process_status(process)
        if phase == "application" and status == "process-failed":
            observed, code, message = _unsupported_diagnostic(process.stderr)
            if observed != "process-failed":
                raise _AssociationError("unavailable", code, message)
        detail = json.dumps({"stdout": _diagnostic_text(process.stdout), "stderr": _diagnostic_text(process.stderr)})
        raise _AssociationError(status, phase + "-" + status, detail)


def _application(frame, helper_digest):
    goal = frame["selectedGoal"]
    return {
        "status": frame["status"], "originalGoal": goal,
        "goalId": goal["goalId"] if goal else None,
        "goalTypeStructural": goal["typeStructural"] if goal else None,
        "termDisplay": frame["termDisplay"], "termStructural": frame["termStructural"],
        "residualGoals": frame["residualGoals"],
        "helper": {"version": frame["helperVersion"], "digest": helper_digest},
    }


def _replay(request, runner, result, execution, directory, frame, body):
    from ladon._source_goal_completion_protocol import decode_replay, validate_replay

    context_path = directory / (frame["sourceContextModule"] + ".olean")
    if context_path.stat().st_size > request.max_output_bytes:
        raise _AssociationError("output-limit", "replay-context-size", "private replay context exceeds the declared output bound")
    context_bytes = _read_regular(context_path, request.max_output_bytes)
    context_digest = _digest(context_bytes)
    source, expected = replay_source(frame, body, context_digest)
    path = directory / "LadonCompletion.lean"
    path.write_bytes(source)
    result["replay"] = {
        "status": "not-run", "generatedSource": source.decode(),
        "sourceDigest": _digest(source), "declarationBodyDigest": expected["sourceDigest"],
        "declaration": expected["declaration"], "coverage": "unavailable",
        "sourceContext": {"module": frame["sourceContextModule"], "digest": context_digest,
                          "bytes": len(context_bytes), "basis": "selected-source-environment"},
    }
    from ladon.semantic_lean_execution import DirectLeanExecution

    replay_environment = dict(execution.environment)
    replay_environment["LEAN_PATH"] = str(directory) + ":" + replay_environment.get("LEAN_PATH", "")
    replay_execution = DirectLeanExecution(execution.command, replay_environment, execution.library_roots)
    process = _run(request, replay_execution, runner, [str(path)], b"", result)
    _verify_bytes(context_path, context_digest, request.max_output_bytes, "replay-context")
    result["replay"]["status"] = "process-succeeded" if process.succeeded else _process_status(process)
    _verify_bytes(path, _digest(source), len(source), "replay-source")
    _require_process(process, "replay")
    observed = decode_replay(process.stdout)
    validate_replay(observed, expected)
    if observed["coverage"] != "complete":
        raise _AssociationError("unavailable", "replay-coverage-unavailable", "compiler axiom coverage is unavailable")
    result["replay"].update({"status": "accepted", "coverage": observed["coverage"], "observation": observed})
    axioms = observed["observedAxioms"]
    accepted = set(axioms).issubset(ALLOWED_AXIOMS)
    result["trust"].update({"observedAxioms": axioms, "coverage": "complete", "accepted": accepted})
    result["status"] = "completed" if accepted else "trust-rejected"
    result["diagnostic"] = None if accepted else {"code": "disallowed-axiom-dependency", "message": "compiled application depends on an axiom outside the declared policy"}


def _initial_result(request):
    return {
        "schema": RESULT_SCHEMA, "operation": "complete-source-goal", "status": "unavailable",
        "captureId": None, "termDigest": _digest(request.term.encode()), "application": None,
        "replay": {"status": "not-run", "coverage": "unavailable"},
        "trust": {"policy": "lean-standard-no-placeholders-v1", "allowedAxioms": list(ALLOWED_AXIOMS),
                  "observedAxioms": None, "forbiddenPlaceholders": ["sorryAx"], "coverage": "unavailable", "accepted": False},
        "diagnostic": None, "resourceAccounting": None, "processReceipts": [],
    }
