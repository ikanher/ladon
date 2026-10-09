"""Pinned, read-only source-goal observation; this operation does not check a proof."""
from __future__ import annotations

import json
import re
import secrets
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from time import monotonic
from typing import Any

from ladon._source_goal_helpers import stage_helper, verify_helper
from ladon._source_goal_inventory import capture_inventory, verify_inventory
from ladon._source_goal_protocol import (
    HELPER_VERSION,
    PROTOCOL,
    decode_observation,
    observation_identity,
    source_offset,
    validate_observation,
)
from ladon.execution_posture import require_target_execution_policy
from ladon.lean_toolchain import LeanToolchainContext, verify_toolchain_identities
from ladon.process_supervisor import ProcessResult, run_bounded_target_process
from ladon.semantic_candidate_limits import validate_semantic_bounds
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_association_io import (
    _MODULE,
    _AssociationError,
    _digest,
    _read_regular,
    _source_path,
)

RESULT_SCHEMA = "ladon-source-goal-capture-result-v1"
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_HELPER_BYTES = 1024 * 1024
ProcessRunner = Callable[..., ProcessResult]


@dataclass(frozen=True)
class SourceGoalCaptureRequest:
    """A scalar-column position in an exact file, with an explicit pinned environment."""

    repo_root: Path
    source_path: str
    module: str
    line: int
    column: int
    toolchain: LeanToolchainContext
    goal_ordinal: int | None = None
    expected_source_digest: str | None = None
    timeout_seconds: float = 60.0
    max_output_bytes: int = 8 * 1024**2
    max_rss_bytes: int = 32 * 1024**3
    require_isolation: bool = False

    def __post_init__(self) -> None:
        require_target_execution_policy(require_isolation=self.require_isolation)
        _validate_request_identity(self)
        _validate_selection(self.line, self.column, self.goal_ordinal)
        _validate_digest(self.expected_source_digest)
        validate_semantic_bounds(self.timeout_seconds, self.max_output_bytes, self.max_rss_bytes)


def _validate_request_identity(request: SourceGoalCaptureRequest) -> None:
    if not isinstance(request.repo_root, Path) or not isinstance(request.toolchain, LeanToolchainContext):
        raise TypeError("source capture requires a repository and pinned Lean context")
    if not isinstance(request.source_path, str) or not isinstance(request.module, str):
        raise TypeError("source path and module must be strings")
    if not _MODULE.fullmatch(request.module):
        raise ValueError("source capture supports ordinary qualified module names")


def _validate_selection(line: int, column: int, ordinal: int | None) -> None:
    if type(line) is not int or type(column) is not int:
        raise TypeError("source line and column must be integers")
    if line < 1 or column < 0:
        raise ValueError("source position requires a positive line and nonnegative column")
    if ordinal is not None and (type(ordinal) is not int or ordinal < 0):
        raise ValueError("goal ordinal must be a nonnegative integer")


def _validate_digest(digest: str | None) -> None:
    if digest is not None and (
        not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None
    ):
        raise ValueError("expected source digest must be a lowercase sha256 digest")


def capture_source_goal(
    request: SourceGoalCaptureRequest, *, runner: ProcessRunner = run_bounded_target_process,
    helper_path: Path | None = None,
) -> dict[str, Any]:
    """Observe one selected goal after validating source and imported-file stability."""
    started = monotonic()
    receipts: list[dict[str, Any]] = []
    try:
        root, source_path, source = _prepare_source(request)
        source_offset(source, request.line, request.column)
        helper = helper_path or Path(str(resources.files("ladon").joinpath(
            "lean", "ladon_source_goal_helper.lean",
        )))
        verify_toolchain_identities(request.toolchain)
        execution = prepare_direct_lean_execution(
            root, None, request.toolchain, require_compiled_module=False,
        )
        with tempfile.TemporaryDirectory(prefix="ladon-source-goal-") as temporary:
            snapshot = Path(temporary) / source_path.name
            snapshot.write_bytes(source)
            staged, helper_digest = stage_helper(helper, Path(temporary))
            result = _capture_snapshot(
                request, source_path, source, snapshot, staged, helper_digest,
                execution, runner, started, receipts,
            )
            verify_helper(helper, helper_digest)
            return result
    except _AssociationError as error:
        return _result(error.status, error.code, str(error), started, receipts)
    except (OSError, ValueError, TypeError, KeyError) as error:
        return _result("unavailable", "capture-input-or-protocol", str(error), started, receipts)


def _prepare_source(request: SourceGoalCaptureRequest) -> tuple[Path, Path, bytes]:
    root = request.repo_root.resolve(strict=True)
    if request.toolchain.selection_mode != "explicit":
        raise _AssociationError("unavailable", "ambient-toolchain", "source capture requires an explicit pinned toolchain")
    if root != request.toolchain.repo_root:
        raise _AssociationError("unavailable", "toolchain-repository", "repository differs from selected toolchain")
    path = _source_path(root, request.source_path, request.module)
    source = _read_regular(path, MAX_SOURCE_BYTES)
    if request.expected_source_digest is not None and _digest(source) != request.expected_source_digest:
        raise _AssociationError("stale", "source-digest-mismatch", "source differs from expected fingerprint")
    return root, path, source


def _capture_snapshot(
    request, source_path, source, snapshot, helper, helper_digest, execution,
    runner, started, receipts,
) -> dict[str, Any]:
    body = {
        "protocolVersion": PROTOCOL, "contextRef": request.toolchain.context_identity,
        "module": request.module, "filename": request.source_path,
        "sourceDigest": _digest(source), "snapshotPath": str(snapshot),
        "line": request.line, "column": request.column,
    }
    first, process = _observe(request, execution, helper, body, source, runner, receipts)
    if not process.succeeded:
        return _process_failure(process, started, receipts)
    _verify_source_files(source_path, snapshot, source)
    selection = _select_goal(first, request.goal_ordinal)
    files, environment, inventory = capture_inventory(request.toolchain, first)
    second, process = _observe(request, execution, helper, body, source, runner, receipts)
    if not process.succeeded:
        return _process_failure(process, started, receipts)
    _verify_bound_observation(first, second)
    _verify_source_files(source_path, snapshot, source)
    verify_inventory(files, environment, inventory)
    verify_toolchain_identities(request.toolchain)
    _verify_bytes(helper, helper_digest, MAX_HELPER_BYTES, "helper")
    capture = _make_capture(request, source, second, selection, inventory, helper_digest)
    return {
        "schema": RESULT_SCHEMA, "operation": "capture-source-goal", "status": "captured",
        "capture": capture, "diagnostic": None, "resourceAccounting": _accounting(started, receipts),
        "processReceipts": receipts,
    }


def _select_goal(frame: Mapping[str, Any], ordinal: int | None) -> int:
    count = frame["goalCount"]
    if count > 1 and ordinal is None:
        raise _AssociationError("ambiguous", "goal-ordinal-required", "multiple goals require an explicit ordinal")
    selected = 0 if ordinal is None else ordinal
    if selected >= count:
        raise _AssociationError("unavailable", "goal-ordinal-range", "goal ordinal is outside the observed list")
    return selected


def _observe(request, execution, helper, body, source, runner, receipts):
    payload = {**body, "requestId": secrets.token_hex(16)}
    input_bytes = ("LADON_GOAL_REQUEST " + json.dumps(payload, sort_keys=True) + "\n").encode()
    process = runner(
        [*execution.command, "--run", str(helper)], cwd=request.repo_root,
        env=dict(execution.environment), timeout_seconds=request.timeout_seconds,
        max_output_bytes=request.max_output_bytes, max_rss_bytes=request.max_rss_bytes,
        input_bytes=input_bytes,
    )
    receipts.append(_receipt(process, input_bytes))
    receipts[-1]["maxOutputBytes"] = request.max_output_bytes
    if not process.succeeded:
        return {}, process
    frame = decode_observation(process.stdout)
    validate_observation(frame, payload, request.toolchain, source)
    return frame, process


def _verify_source_files(source_path: Path, snapshot: Path, source: bytes) -> None:
    digest = _digest(source)
    _verify_bytes(source_path, digest, MAX_SOURCE_BYTES, "source")
    _verify_bytes(snapshot, digest, MAX_SOURCE_BYTES, "snapshot")


def _verify_bytes(path: Path, digest: str, limit: int, label: str) -> None:
    if _digest(_read_regular(path, limit)) != digest:
        raise _AssociationError("stale", label + "-changed", label + " bytes changed during capture")


def _verify_bound_observation(first: Mapping[str, Any], second: Mapping[str, Any]) -> None:
    if observation_identity(first) != observation_identity(second):
        raise _AssociationError("stale", "observation-changed", "source goal or import closure changed between observations")


def _make_capture(request, source, frame, selection, inventory, helper_digest):
    capture = {
        "source": {
            "path": request.source_path, "module": request.module, "digest": _digest(source),
            "byteLength": len(source),
            "position": {"line": request.line, "column": request.column, "byteOffset": frame["byteOffset"]},
            "syntaxRange": {"startByte": frame["rangeStartByte"], "endByte": frame["rangeEndByte"]},
            "selectionRange": {
                "startByte": frame["rangeStartByte"], "endByteInclusive": frame["selectionEndByte"],
            },
        },
        "environment": {
            "executionContextRef": request.toolchain.context_identity,
            "leanVersion": frame["leanVersion"], "leanCommit": frame["leanCommit"],
            "leanExecutablePath": frame["leanExecutablePath"],
            "executableDigest": request.toolchain.lean_identity, "compiledInventory": inventory,
            "namespace": frame["namespaceName"],
            "openDeclarationsStructural": frame["openDeclarationsStructural"],
            "optionsStructural": frame["optionsStructural"],
            "bindingBasis": "stable-disk-inventory-around-selected-context-observation",
            "setupProfile": "ordinary-nonmodular-default-setup",
        },
        "helper": {"protocolVersion": PROTOCOL, "helperVersion": HELPER_VERSION, "digest": helper_digest,
                   "observation": {"useAfter": frame["useAfter"]}},
        "goal": {**frame["goals"][selection], "ordinal": selection, "goalCount": frame["goalCount"]},
        "scope": "source-goal-elaboration-observation",
        "replay": "not-run",
    }
    capture["captureId"] = _digest(json.dumps(
        capture, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode())
    return capture


def _receipt(process: ProcessResult, input_bytes: bytes) -> dict[str, Any]:
    return {
        "command": list(process.command), "returnCode": process.returncode,
        "elapsedSeconds": process.elapsed_seconds, "peakRssBytes": process.peak_rss_bytes,
        "timedOut": process.timed_out, "memoryLimited": process.memory_limited,
        "outputLimited": process.output_limited, "inputDigest": _digest(input_bytes),
        "stdoutDigest": _digest(process.stdout.encode()), "stderrDigest": _digest(process.stderr.encode()),
        "stdoutBytes": len(process.stdout.encode()), "stderrBytes": len(process.stderr.encode()),
    }


def _accounting(started: float, receipts: list[dict[str, Any]]) -> dict[str, Any]:
    measured = [row["peakRssBytes"] for row in receipts if row["peakRssBytes"] is not None]
    return {
        "elapsedSeconds": monotonic() - started,
        "helperElapsedSeconds": sum(row["elapsedSeconds"] for row in receipts),
        "peakRssBytes": max(measured) if measured else None,
        "peakRssScope": "supervised-helper-process-tree",
        "elapsedScope": "complete-capture-operation",
    }


def _process_failure(process: ProcessResult, started: float, receipts):
    status = _process_status(process)
    code, message = status, "Lean helper process failed within its declared bounds"
    if status == "process-failed":
        status, code, message = _unsupported_diagnostic(process.stderr)
    result = _result(status, code, message, started, receipts)
    if receipts:
        result["diagnostic"]["outputSize"] = {
            key: receipts[-1].get(key)
            for key in ("stdoutBytes", "stderrBytes", "maxOutputBytes")
        }
    result["diagnostic"]["processOutput"] = {
        "stdout": _diagnostic_text(process.stdout),
        "stderr": _diagnostic_text(process.stderr),
        "byteLimitPerStream": 8192,
    }
    return result


def _diagnostic_text(value: str) -> dict[str, Any]:
    raw = value.encode("utf-8")
    return {"text": raw[:8192].decode("utf-8", errors="ignore"), "truncated": len(raw) > 8192}


def _process_status(process: ProcessResult) -> str:
    for failed, status in (
        (process.timed_out, "timeout"), (process.memory_limited, "memory-limit"),
        (process.output_limited, "output-limit"),
    ):
        if failed:
            return status
    return "process-failed"


def _unsupported_diagnostic(stderr: str) -> tuple[str, str, str]:
    profiles = (
        ("modular source unsupported", "unavailable", "unsupported-modular-source"),
        ("ambiguous source observations", "ambiguous", "overlapping-source-observations"),
        ("no goal at selected position", "unavailable", "no-goal-at-position"),
    )
    for message, status, code in profiles:
        if message in stderr:
            return status, code, message
    return "process-failed", "process-failed", "Lean helper failed; inspect bounded diagnostics"


def _result(status: str, code: str, message: str, started: float, receipts):
    return {
        "schema": RESULT_SCHEMA, "operation": "capture-source-goal", "status": status,
        "capture": None, "diagnostic": {"code": code, "message": message[:500]},
        "resourceAccounting": _accounting(started, receipts), "processReceipts": receipts,
    }
