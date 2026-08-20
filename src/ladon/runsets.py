"""Serial, resumable orchestration of ordinary Ladon analyses.

The injected runner remains the owner of analysis and target processes.  This
public facade supplies a cancellation token, compatible reuse handles, atomic
publication, and deterministic bundle state without becoming another analyzer.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ladon.process_supervisor import ProcessCancelled, ProcessSignal
from ladon.runset_contract import (
    BundleEntry,
    EntryValidity,
    RunsetBundle,
    RunsetEntry,
    RunsetManifest,
    RunsetResources,
    require_portable_relative_path,
)
from ladon.runset_reports import (
    record_outcome,
    validate_bundle_reports,
    validated_resume_hit,
)
from ladon.runset_runtime import (
    AnalysisOutcome,
    AnalysisRunner,
    EventSink,
    ReusableArtifact,
    RunsetAnalysisRequest,
    RunsetExecutionResult,
    SharedArtifactPool,
    ValidityResolver,
)
from ladon.runset_storage import (
    RUNSET_STATE_NAME,
    atomic_write_bytes,
    commit_state_entry,
    load_state,
)
from ladon.runset_support import (
    aggregate_exit_code,
    blocked_dependency,
    default_validity,
    emit,
    exception_reason,
    failed_record,
    interrupted_record,
    preflight_destinations,
    resolve_validities,
    resolved_repository,
    reuse_record,
    skipped_record,
    stop_reason,
)

DEFAULT_BUNDLE_NAME = "bundle.json"


@dataclass
class _RunLoop:
    """Mutable serial-loop state kept out of the public entry point."""

    manifest: RunsetManifest
    repository: Path
    destination: Path
    runner: AnalysisRunner
    validities: Mapping[str, EntryValidity]
    fingerprints: Mapping[str, str]
    cancellation: threading.Event
    state: dict[str, Any]
    state_path: Path
    resume: bool
    event_sink: EventSink | None
    pool: SharedArtifactPool = field(default_factory=SharedArtifactPool)
    records: dict[str, BundleEntry] = field(default_factory=dict)
    launches: int = 0
    resume_hits: int = 0
    halted_reason: str | None = None

    def run(self) -> tuple[BundleEntry, ...]:
        """Run and durably record every entry in dependency order."""

        for entry in self.manifest.execution_order:
            record = self._next_record(entry)
            self.records[entry.identifier] = record
            commit_state_entry(
                self.state_path,
                self.state,
                self.manifest,
                record,
            )
            self.halted_reason = self.halted_reason or stop_reason(
                self.manifest,
                record,
            )
        return tuple(
            self.records[entry.identifier] for entry in self.manifest.entries
        )

    def _next_record(self, entry: RunsetEntry) -> BundleEntry:
        validity = self.validities[entry.identifier]
        fingerprint = self.fingerprints[entry.identifier]
        if self.halted_reason is not None:
            return skipped_record(
                entry,
                validity,
                fingerprint,
                self.halted_reason,
            )
        if blocked_dependency(entry, self.records):
            return skipped_record(
                entry,
                validity,
                fingerprint,
                "dependency_not_complete",
            )
        if self.cancellation.is_set():
            self.halted_reason = "runset_cancelled"
            return interrupted_record(
                entry,
                validity,
                fingerprint,
                "cancelled_before_entry_start",
            )
        return self._resume_or_execute(entry, validity, fingerprint)

    def _resume_or_execute(
        self,
        entry: RunsetEntry,
        validity: EntryValidity,
        fingerprint: str,
    ) -> BundleEntry:
        record = (
            validated_resume_hit(
                entry,
                validity,
                fingerprint,
                self.destination,
                self.state,
            )
            if self.resume
            else None
        )
        if record is not None:
            self.resume_hits += 1
            emit(self.event_sink, entry, "resume-hit")
            return record
        self.launches += 1
        return _execute_entry(
            entry,
            self.repository,
            self.destination,
            validity,
            fingerprint,
            self.manifest.resources,
            self.runner,
            self.pool,
            self.cancellation,
            self.event_sink,
        )


def execute_runset(
    manifest: RunsetManifest,
    *,
    workspace_root: str | Path,
    bundle_dir: str | Path,
    runner: AnalysisRunner,
    validity_resolver: ValidityResolver | None = None,
    cancel_event: threading.Event | None = None,
    resume: bool = True,
    bundle_name: str = DEFAULT_BUNDLE_NAME,
    event_sink: EventSink | None = None,
) -> RunsetExecutionResult:
    """Execute a fully validated runset serially and publish its bundle."""

    require_portable_relative_path(bundle_name, "bundle manifest name")
    workspace = Path(workspace_root).resolve()
    repository = resolved_repository(workspace, manifest.repository)
    destination = Path(bundle_dir).resolve()
    preflight_destinations(manifest, destination, bundle_name)
    destination.mkdir(parents=True, exist_ok=True)
    state_path = destination / RUNSET_STATE_NAME
    bundle_path = destination / bundle_name
    resolver = validity_resolver or default_validity
    validities, fingerprints = resolve_validities(
        manifest,
        repository,
        resolver,
    )
    loop = _RunLoop(
        manifest=manifest,
        repository=repository,
        destination=destination,
        runner=runner,
        validities=validities,
        fingerprints=fingerprints,
        cancellation=cancel_event or threading.Event(),
        state=load_state(state_path, manifest),
        state_path=state_path,
        resume=resume,
        event_sink=event_sink,
    )
    ordered_records = loop.run()
    bundle = RunsetBundle(
        name=manifest.name,
        runset_fingerprint=manifest.fingerprint,
        entries=ordered_records,
    )
    atomic_write_bytes(bundle_path, bundle.to_bytes())
    return RunsetExecutionResult(
        bundle=bundle,
        bundle_path=bundle_path,
        state_path=state_path,
        exit_code=aggregate_exit_code(ordered_records),
        analyzer_launches=loop.launches,
        resume_hits=loop.resume_hits,
    )


def _execute_entry(
    entry: RunsetEntry,
    repository: Path,
    destination: Path,
    validity: EntryValidity,
    fingerprint: str,
    resources: RunsetResources,
    runner: AnalysisRunner,
    pool: SharedArtifactPool,
    cancellation: threading.Event,
    event_sink: EventSink | None,
) -> BundleEntry:
    shared = pool.compatible(validity)
    reuse = reuse_record(validity, shared)
    request = RunsetAnalysisRequest(
        entry=entry,
        repository_root=repository,
        validity=validity,
        resources=resources,
        cancel_event=cancellation,
        shared_artifacts=shared,
    )
    emit(event_sink, entry, "started")
    try:
        outcome = runner(request)
        record = record_outcome(
            entry,
            destination,
            validity,
            fingerprint,
            reuse,
            outcome,
            resources.max_report_bytes,
        )
        if record.status == "complete":
            pool.publish(validity, outcome.reusable_artifacts)
    except (ProcessCancelled, ProcessSignal, KeyboardInterrupt) as exc:
        cancellation.set()
        record = interrupted_record(
            entry,
            validity,
            fingerprint,
            exception_reason(exc),
            reuse=reuse,
        )
    except Exception as exc:  # noqa: BLE001 - runset boundary records bounded failures
        record = failed_record(
            entry,
            validity,
            fingerprint,
            "analysis_exception",
            str(exc),
            reuse=reuse,
        )
    emit(event_sink, entry, record.status)
    return record


__all__ = [
    "DEFAULT_BUNDLE_NAME",
    "AnalysisOutcome",
    "AnalysisRunner",
    "EventSink",
    "ReusableArtifact",
    "RunsetAnalysisRequest",
    "RunsetExecutionResult",
    "SharedArtifactPool",
    "ValidityResolver",
    "atomic_write_bytes",
    "default_validity",
    "execute_runset",
    "validate_bundle_reports",
]
