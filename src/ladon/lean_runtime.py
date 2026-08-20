"""Bounded batch execution for Ladon's Lean parser helper."""

from __future__ import annotations

import subprocess
import tempfile
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic
from typing import Any

from ladon.ir import LeanModule
from ladon.lean_cache import (
    CACHE_FINGERPRINT_VERSION,
    CacheFingerprint,
    FileHashMemo,
    LeanCacheStore,
    build_cache_fingerprint,
)
from ladon.lean_protocol import (
    HELPER_VERSION,
    PROTOCOL_VERSION,
    BatchFrameCollector,
    BatchOutcome,
    BatchRequest,
    ModuleRequest,
    ProtocolFrameError,
)
from ladon.process_supervisor import (
    ProcessCancelled,
    ProcessResult,
    run_streaming_target_process,
    run_target_process,
)

DEFAULT_LEAN_BATCH_SIZE = 8
DEFAULT_LEAN_BATCH_TIMEOUT_SECONDS = 120.0
LEAN_VERSION_TIMEOUT_SECONDS = 30.0
EXECUTION_SAFETY_WARNING = (
    "Lean-backed extraction loads target environments and may execute imported "
    "initializers; do not use it as safe analysis of an untrusted repository."
)


@dataclass(frozen=True)
class LeanRuntimeConfig:
    """Finite execution controls for inventory helper batches."""

    batch_size: int = DEFAULT_LEAN_BATCH_SIZE
    timeout_seconds: float = DEFAULT_LEAN_BATCH_TIMEOUT_SECONDS
    strict: bool = False
    cancel_event: threading.Event | None = None

    def __post_init__(self) -> None:
        if self.batch_size < 2:
            raise ValueError("Lean inventory batch size must be at least two")
        if self.timeout_seconds <= 0:
            raise ValueError("Lean helper timeout must be greater than zero")


@dataclass(frozen=True)
class RequestedModule:
    """One requested module and its repository-relative source file."""

    module: str
    file: str


@dataclass(frozen=True)
class BatchExecution:
    """One supervised helper invocation and validated outcome."""

    outcome: BatchOutcome
    command: tuple[str, ...]
    elapsed_seconds: float
    timed_out: bool = False
    cancelled: bool = False
    returncode: int | None = None
    stderr: str = ""


@dataclass(frozen=True)
class LeanRuntimeResult:
    """All successful payloads, diagnostics, counters, and provenance."""

    payloads: Mapping[str, Mapping[str, Any]]
    diagnostics: tuple[dict[str, Any], ...]
    counters: Mapping[str, int]
    provenance: Mapping[str, Any]


@dataclass
class RuntimeAccumulator:
    """Mutable run-local assembly hidden behind a stable result."""

    payloads: dict[str, Mapping[str, Any]] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    cache_rows: list[dict[str, Any]] = field(default_factory=list)
    executions: list[BatchExecution] = field(default_factory=list)
    resolved_lean_version: str | None = None


def execute_lean_runtime(
    *,
    repo_root: Path,
    helper_path: Path,
    requested: Sequence[RequestedModule],
    modules: Mapping[str, LeanModule],
    cache_dir: Path | None,
    config: LeanRuntimeConfig,
    build_requested: bool = False,
) -> LeanRuntimeResult:
    """Resolve cache rows, run bounded misses, and preserve partial results."""

    indexed = tuple(
        ModuleRequest(index, row.module, row.file)
        for index, row in enumerate(requested)
    )
    accumulator = RuntimeAccumulator()
    fingerprints: dict[int, CacheFingerprint] = {}
    misses = resolve_cache_rows(
        repo_root=repo_root,
        helper_path=helper_path,
        requests=indexed,
        modules=modules,
        cache_dir=cache_dir,
        config=config,
        accumulator=accumulator,
        fingerprints=fingerprints,
    )
    for batch in plan_batches(misses, config.batch_size):
        if config.cancel_event is not None and config.cancel_event.is_set():
            break
        execution = execute_helper_batch(
            repo_root,
            helper_path,
            batch,
            config,
        )
        accumulator.executions.append(execution)
        accept_batch_outcome(
            execution.outcome,
            accumulator,
            cache_dir,
            fingerprints,
        )
        if execution.cancelled:
            break
    return runtime_result(
        indexed,
        accumulator,
        config,
        build_requested=build_requested,
    )


def plan_batches(
    requests: Sequence[ModuleRequest],
    batch_size: int,
) -> tuple[tuple[ModuleRequest, ...], ...]:
    """Partition requests into at most ``ceil(n / batch_size)`` invocations."""

    if batch_size < 2:
        raise ValueError("Lean inventory batch size must be at least two")
    return tuple(
        tuple(requests[index:index + batch_size])
        for index in range(0, len(requests), batch_size)
    )


def resolve_cache_rows(
    *,
    repo_root: Path,
    helper_path: Path,
    requests: Sequence[ModuleRequest],
    modules: Mapping[str, LeanModule],
    cache_dir: Path | None,
    config: LeanRuntimeConfig,
    accumulator: RuntimeAccumulator,
    fingerprints: dict[int, CacheFingerprint],
) -> tuple[ModuleRequest, ...]:
    """Resolve sound hits and return ordered misses or bypassed rows."""

    if cache_dir is None:
        accumulator.cache_rows.extend(
            cache_row(request, "disabled", "cache_not_configured", None)
            for request in requests
        )
        return tuple(requests)
    lean_version = resolve_lean_version(
        repo_root,
        cancel_event=config.cancel_event,
    )
    accumulator.resolved_lean_version = lean_version or None
    store = LeanCacheStore(cache_dir)
    hashes = FileHashMemo()
    misses: list[ModuleRequest] = []
    for request in requests:
        fingerprint = request_fingerprint(
            repo_root,
            helper_path,
            request,
            modules,
            lean_version,
            config,
            hashes,
        )
        fingerprints[request.request_index] = fingerprint
        lookup = store.lookup(request.module, fingerprint)
        accumulator.cache_rows.append(
            cache_row(
                request,
                lookup.status,
                lookup.invalidation_reason,
                fingerprint,
            )
        )
        if lookup.status == "hit" and lookup.payload is not None:
            accumulator.payloads[request.module] = lookup.payload
        else:
            misses.append(request)
    return tuple(misses)


def request_fingerprint(
    repo_root: Path,
    helper_path: Path,
    request: ModuleRequest,
    modules: Mapping[str, LeanModule],
    lean_version: str,
    config: LeanRuntimeConfig,
    hashes: FileHashMemo,
) -> CacheFingerprint:
    """Build one cache manifest from run options and resolved module state."""

    return build_cache_fingerprint(
        repo_root=repo_root,
        module=request.module,
        source_path=repo_root / request.file,
        helper_path=helper_path,
        modules=modules,
        lean_version=lean_version,
        extraction_options={
            "batchSize": config.batch_size,
            "strict": config.strict,
        },
        hashes=hashes,
    )


def resolve_lean_version(
    repo_root: Path,
    *,
    cancel_event: threading.Event | None = None,
) -> str:
    """Resolve Lean identity with a finite supervised command."""

    result = run_target_process(
        ["lake", "env", "lean", "--version"],
        cwd=repo_root,
        timeout_seconds=LEAN_VERSION_TIMEOUT_SECONDS,
        cancel_event=cancel_event,
    )
    return result.stdout.strip() if result.succeeded else ""


def execute_helper_batch(
    repo_root: Path,
    helper_path: Path,
    requests: Sequence[ModuleRequest],
    config: LeanRuntimeConfig,
) -> BatchExecution:
    """Run one helper batch with live frame validation and group cleanup."""

    collector = BatchFrameCollector(requests)
    command: tuple[str, ...] = ()
    started = monotonic()
    try:
        result = run_batch_process(
            repo_root,
            helper_path,
            requests,
            config,
            collector,
        )
        command = result.command
        outcome = completed_process_outcome(result, collector)
        return BatchExecution(
            outcome,
            command,
            result.elapsed_seconds,
            returncode=result.returncode,
            stderr=result.stderr,
        )
    except subprocess.TimeoutExpired:
        return failed_batch_execution(
            collector,
            command,
            started,
            "Lean helper batch exceeded its configured deadline",
            timed_out=True,
        )
    except ProcessCancelled:
        return failed_batch_execution(
            collector,
            command,
            started,
            "Lean helper batch was cancelled by the caller",
            cancelled=True,
        )
    except (OSError, ProtocolFrameError) as exc:
        return failed_batch_execution(
            collector,
            command,
            started,
            f"Lean helper batch failed: {exc}",
        )


def run_batch_process(
    repo_root: Path,
    helper_path: Path,
    requests: Sequence[ModuleRequest],
    config: LeanRuntimeConfig,
    collector: BatchFrameCollector,
) -> ProcessResult:
    """Materialize a finite request and supervise the packaged helper."""

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".ladon-lean-batch.json",
    ) as request_file:
        request_file.write(BatchRequest(tuple(requests)).to_json())
        request_file.flush()
        command = [
            "lake",
            "env",
            "lean",
            "--run",
            str(helper_path),
            "--",
            "--batch",
            request_file.name,
        ]
        return run_streaming_target_process(
            command,
            cwd=repo_root,
            timeout_seconds=config.timeout_seconds,
            input_text="",
            stdout_line_validator=collector.feed_line,
            cancel_event=config.cancel_event,
        )


def completed_process_outcome(
    result: ProcessResult,
    collector: BatchFrameCollector,
) -> BatchOutcome:
    """Validate terminal state or classify a nonzero helper exit."""

    if result.returncode != 0:
        details = result.stderr.strip() or f"exit status {result.returncode}"
        return collector.partial_outcome(f"Lean helper process failed: {details}")
    return collector.finish()


def failed_batch_execution(
    collector: BatchFrameCollector,
    command: tuple[str, ...],
    started: float,
    reason: str,
    *,
    timed_out: bool = False,
    cancelled: bool = False,
) -> BatchExecution:
    """Preserve validated frames after a supervised operational failure."""

    return BatchExecution(
        collector.partial_outcome(reason),
        command,
        monotonic() - started,
        timed_out=timed_out,
        cancelled=cancelled,
    )


def accept_batch_outcome(
    outcome: BatchOutcome,
    accumulator: RuntimeAccumulator,
    cache_dir: Path | None,
    fingerprints: Mapping[int, CacheFingerprint],
) -> None:
    """Attach ordered records, diagnostics, and sound cache writes."""

    store = LeanCacheStore(cache_dir) if cache_dir is not None else None
    for record in outcome.records:
        if record.status == "ok" and record.payload is not None:
            accumulator.payloads[record.request.module] = record.payload
            fingerprint = fingerprints.get(record.request.request_index)
            if store is not None and fingerprint is not None:
                store.store(record.request.module, fingerprint, record.payload)
        elif record.diagnostic is not None:
            accumulator.diagnostics.append(record.diagnostic.to_dict())
    accumulator.diagnostics.extend(
        diagnostic.to_dict() for diagnostic in outcome.diagnostics
    )


def runtime_result(
    requests: Sequence[ModuleRequest],
    accumulator: RuntimeAccumulator,
    config: LeanRuntimeConfig,
    *,
    build_requested: bool,
) -> LeanRuntimeResult:
    """Finalize counters and ordinary report-v2 phase data."""

    counters = runtime_counters(requests, accumulator, config)
    provenance = runtime_provenance(
        requests,
        accumulator,
        config,
        build_requested=build_requested,
    )
    return LeanRuntimeResult(
        dict(sorted(accumulator.payloads.items())),
        tuple(accumulator.diagnostics),
        counters,
        provenance,
    )


def runtime_counters(
    requests: Sequence[ModuleRequest],
    accumulator: RuntimeAccumulator,
    config: LeanRuntimeConfig,
) -> dict[str, int]:
    """Count cache, invocation, result, timeout, and strict states."""

    failed = len(requests) - len(accumulator.payloads)
    cache_counts = {
        status: sum(row["status"] == status for row in accumulator.cache_rows)
        for status in ("hit", "miss", "bypassed", "disabled")
    }
    return {
        "lean_cache_hits": cache_counts["hit"],
        "lean_cache_misses": cache_counts["miss"] + cache_counts["disabled"],
        "lean_cache_bypassed": cache_counts["bypassed"],
        "helper_invocations": len(accumulator.executions),
        "requested": len(requests),
        "completed": len(accumulator.payloads),
        "failed": failed,
        "timed_out_batches": sum(row.timed_out for row in accumulator.executions),
        "cancelled_batches": sum(row.cancelled for row in accumulator.executions),
        "strict_rejected": int(config.strict and failed > 0),
    }


def runtime_provenance(
    requests: Sequence[ModuleRequest],
    accumulator: RuntimeAccumulator,
    config: LeanRuntimeConfig,
    *,
    build_requested: bool,
) -> dict[str, Any]:
    """Build report-facing versions, command, cache, and safety evidence."""

    failed = len(requests) - len(accumulator.payloads)
    summaries = [
        execution.outcome.summary
        for execution in accumulator.executions
        if execution.outcome.summary is not None
    ]
    helper_version = summaries[0].helper_version if summaries else HELPER_VERSION
    lean_version = (
        summaries[0].lean_version
        if summaries
        else accumulator.resolved_lean_version
    )
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "helperVersion": helper_version,
        "leanVersion": lean_version,
        "commandShape": helper_command_shape(),
        "batchSize": config.batch_size,
        "timeoutSeconds": config.timeout_seconds,
        "helperElapsedSeconds": sum(
            row.elapsed_seconds for row in accumulator.executions
        ),
        "requested": len(requests),
        "completed": len(accumulator.payloads),
        "failed": failed,
        "timedOut": any(row.timed_out for row in accumulator.executions),
        "cancelled": any(row.cancelled for row in accumulator.executions),
        "strict": config.strict,
        "strictRejected": bool(config.strict and failed > 0),
        "cacheFingerprintVersion": CACHE_FINGERPRINT_VERSION,
        "cache": accumulator.cache_rows,
        "buildRequested": build_requested,
        "buildInvokedByExtraction": False,
        "executionSafetyWarning": EXECUTION_SAFETY_WARNING,
    }


def helper_command_shape() -> list[str]:
    """Return a redacted but replay-informative helper command shape."""

    return [
        "lake",
        "env",
        "lean",
        "--run",
        "<packaged-helper>",
        "--",
        "--batch",
        "<request-json>",
    ]


def cache_row(
    request: ModuleRequest,
    status: str,
    reason: str | None,
    fingerprint: CacheFingerprint | None,
) -> dict[str, Any]:
    """Build one stable per-module cache provenance row."""

    return {
        "module": request.module,
        "status": status,
        "invalidationReason": reason,
        "fingerprintVersion": (
            CACHE_FINGERPRINT_VERSION if fingerprint is not None else None
        ),
        "fingerprint": fingerprint.digest if fingerprint is not None else None,
        "cacheSafety": (
            fingerprint.manifest["cacheSafety"]
            if fingerprint is not None
            else {"status": "disabled", "reason": reason}
        ),
    }
