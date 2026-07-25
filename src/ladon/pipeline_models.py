"""Run state and report adaptation for Ladon's analysis pipeline."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Iterator, Mapping

from ladon.extraction import ModuleDiscovery
from ladon.finding_workflow import enrich_findings
from ladon.ir import ExtractionBundle, LeanAuditQuery, LeanModule
from ladon.lean_runtime import (
    DEFAULT_LEAN_BATCH_SIZE,
    DEFAULT_LEAN_BATCH_TIMEOUT_SECONDS,
)
from ladon.progress import (
    PhaseProgress,
    ProgressReporter,
    ResourceLimitExceeded,
    RunBudget,
)
from ladon.report_v2 import (
    ReportMetadata,
    ReportV2,
    build_report_v2,
)
from ladon.report_contract import default_phase_disposition
from ladon.scope import ScopePlan


REQUIRED_PHASES = (
    "discover",
    "lean_extraction",
    "indexing",
    "module_dag",
    "module_readiness",
    "architecture_policy",
    "source_patterns",
    "import_diet",
    "proof_xray",
    "quality_baseline",
    "findings",
    "refactoring_prescriptions",
    "packet_evidence",
    "review_regions",
    "rendering",
)
CORE_REQUIRED_PHASES = frozenset(
    {"discover", "indexing", "module_dag", "findings", "rendering"}
)


@dataclass(frozen=True)
class PhaseTiming:
    """Timing and status for one named pipeline phase."""

    name: str
    elapsed_seconds: float
    status: str
    counters: dict[str, int] = field(default_factory=dict)
    reason: str | None = None

    def to_json(self) -> dict[str, Any]:
        """Return the stable JSON shape used in reports."""

        return {
            "name": self.name,
            "elapsed_seconds": self.elapsed_seconds,
            "status": self.status,
            "counters": dict(sorted(self.counters.items())),
            "reason": self.reason,
        }


@dataclass
class RunContext:
    """User request and run-local metadata for one Ladon invocation."""

    repo_root: Path
    requested_root: str | None = None
    requested_roots: tuple[str, ...] = ()
    analysis_scope: str = "owner"
    changed_paths: tuple[str, ...] = ()
    changed_manifest: Path | None = None
    max_scope_modules: int | None = None
    max_context_modules: int | None = None
    source_cache_dir: Path | None = None
    source_cache_enabled: bool = True
    build_requested: bool = False
    build_timeout_seconds: float = 300.0
    preflight: dict[str, str] = field(default_factory=dict)
    extraction_backend: str = "text"
    lean_extraction_scope: str = "root"
    lean_cache_dir: Path | None = None
    lean_batch_size: int = DEFAULT_LEAN_BATCH_SIZE
    lean_helper_timeout_seconds: float = DEFAULT_LEAN_BATCH_TIMEOUT_SECONDS
    lean_strict: bool = False
    packet_dirs: tuple[Path, ...] = ()
    packet_profile: str = "generic"
    architecture_policy_path: Path | None = None
    architecture_policy: dict[str, Any] | None = None
    source_pattern_policy_path: Path | None = None
    source_pattern_policy: dict[str, Any] | None = None
    generated_family_policy_path: Path | None = None
    generated_family_policy: dict[str, Any] | None = None
    module_system_witness_path: Path | None = None
    module_system_witness: dict[str, Any] | None = None
    import_diet_witness_path: Path | None = None
    import_diet_witness: dict[str, Any] | None = None
    proof_xray_path: Path | None = None
    proof_xray: dict[str, Any] | None = None
    lean_extractor: Callable[
        ["RunContext", ModuleDiscovery],
        ExtractionBundle | dict[str, LeanModule],
    ] | None = None
    generated_at_utc: str | None = None
    warnings: list[str] = field(default_factory=list)
    timings: list[PhaseTiming] = field(default_factory=list)
    lean_runtime: dict[str, Any] | None = None
    lean_audit_queries: dict[str, LeanAuditQuery] = field(default_factory=dict)
    progress: ProgressReporter | None = None
    budget: RunBudget | None = None
    cancel_event: threading.Event = field(default_factory=threading.Event)
    limit_failure: dict[str, Any] | None = None
    scope_plan: ScopePlan | None = None
    source_index_cache: dict[str, Any] | None = None
    inventory_module_count: int = 0
    indexed_module_count: int = 0
    source_index_status: str = "complete"
    source_index_diagnostics: tuple[Mapping[str, Any], ...] = ()
    policy_inputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    retained_discovery: ModuleDiscovery | None = None
    retained_modules: dict[str, LeanModule] = field(default_factory=dict)
    _active_progress: PhaseProgress | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _active_phase_name: str | None = field(default=None, init=False, repr=False)
    _active_phase_status: str | None = field(default=None, init=False, repr=False)
    _active_phase_reason: str | None = field(default=None, init=False, repr=False)

    @contextmanager
    def phase(
        self,
        name: str,
        *,
        status: str = "ok",
    ) -> Iterator[dict[str, int]]:
        """Record elapsed time for a phase and let callers fill counters."""

        counters: dict[str, int] = {}
        start = perf_counter()
        phase_status = status
        reason: str | None = None
        pulse = self.progress.phase(name) if self.progress is not None else None
        previous_active = (
            self._active_progress,
            self._active_phase_name,
            self._active_phase_status,
            self._active_phase_reason,
        )
        self._active_progress = pulse
        self._active_phase_name = name
        self._active_phase_status = None
        self._active_phase_reason = None
        if pulse is not None:
            pulse.start()
        try:
            if self.budget is not None:
                with self.budget.watch(name, self.cancel_event):
                    yield counters
            else:
                yield counters
        except ResourceLimitExceeded as exc:
            phase_status = "error"
            reason = str(exc)
            self.limit_failure = {
                "id": f"resource.{exc.kind}",
                "kind": exc.kind,
                "phase": exc.phase,
                "observed": exc.observed,
                "limit": exc.limit,
                "reason": reason,
            }
            self.cancel_event.set()
            raise
        except Exception as exc:
            phase_status = "error"
            reason = str(exc)
            raise
        finally:
            if phase_status != "error" and self._active_phase_status is not None:
                phase_status = self._active_phase_status
                reason = self._active_phase_reason
            elapsed = max(0.0, perf_counter() - start)
            self.timings.append(
                PhaseTiming(name, elapsed, phase_status, counters, reason)
            )
            if pulse is not None:
                pulse.finish(
                    status=progress_terminal_status(phase_status),
                    completed=progress_completed(counters),
                    cache=progress_cache_counters(counters),
                )
            (
                self._active_progress,
                self._active_phase_name,
                self._active_phase_status,
                self._active_phase_reason,
            ) = previous_active

    def record_skipped(self, name: str, reason: str) -> None:
        """Record a phase that is intentionally absent in the clean core."""

        self.timings.append(PhaseTiming(name, 0.0, "skipped", {}, reason))

    def mark_phase_partial(self, name: str, reason: str) -> None:
        """Change the latest completed phase to partial without losing counters."""

        if self._active_phase_name == name:
            self._active_phase_status = "partial"
            self._active_phase_reason = reason
            return
        for index in range(len(self.timings) - 1, -1, -1):
            timing = self.timings[index]
            if timing.name == name:
                self.timings[index] = PhaseTiming(
                    timing.name,
                    timing.elapsed_seconds,
                    "partial",
                    timing.counters,
                    reason,
                )
                return
        raise ValueError(f"cannot mark unrecorded phase partial: {name}")

    def progress_update(
        self,
        completed: int,
        total: int | None = None,
    ) -> None:
        """Publish a bounded completed-unit update for the active phase."""

        if self._active_progress is not None:
            self._active_progress.update(completed=completed, total=total)

    def set_phase_counter(self, name: str, key: str, value: int) -> None:
        """Finalize one earlier phase counter after deterministic promotion."""

        for index in range(len(self.timings) - 1, -1, -1):
            timing = self.timings[index]
            if timing.name != name:
                continue
            counters = dict(timing.counters)
            counters[key] = value
            self.timings[index] = PhaseTiming(
                timing.name,
                timing.elapsed_seconds,
                timing.status,
                counters,
                timing.reason,
            )
            return
        raise ValueError(f"cannot update unrecorded phase counter: {name}")


def progress_completed(counters: Mapping[str, int]) -> int | None:
    """Return one bounded progress count without inventing a total."""

    for key in ("modules", "declarations", "findings", "rows", "payloads"):
        if key in counters:
            return int(counters[key])
    return None


def progress_terminal_status(status: str) -> str:
    """Map internal phase timing vocabulary to progress event status."""

    return {
        "ok": "complete",
        "partial": "partial",
        "error": "failed",
    }.get(status, status)


def progress_cache_counters(counters: Mapping[str, int]) -> dict[str, int]:
    """Return cache-related counters for terminal progress events."""

    return {
        key: int(value)
        for key, value in sorted(counters.items())
        if "cache" in key
    }


@dataclass(frozen=True)
class PipelineResult:
    """Normalized output of one clean-core pipeline run."""

    context: RunContext
    discovery: ModuleDiscovery
    module_dag: dict[str, Any]
    module_readiness: dict[str, Any] | None = None
    architecture_policy: dict[str, Any] | None = None
    source_patterns: dict[str, Any] | None = None
    import_diet: dict[str, Any] | None = None
    proof_xray: dict[str, Any] | None = None
    declaration_graph: dict[str, Any] | None = None
    quality_baseline: dict[str, Any] | None = None
    refactoring_prescriptions: dict[str, Any] | None = None
    findings: list[dict[str, Any]] = field(default_factory=list)
    packet_evidence: list[dict[str, Any]] = field(default_factory=list)
    review_regions: list[dict[str, Any]] = field(default_factory=list)

    def timing_by_phase(self) -> dict[str, PhaseTiming]:
        """Return the last timing record for each phase name."""

        return {timing.name: timing for timing in self.context.timings}

    def to_report_payload(self) -> dict[str, Any]:
        """Return the schema-facing frozen v2 report projection."""

        return self.to_report_model().to_dict()

    def to_report_model(self) -> ReportV2:
        """Adapt all analysis phase boundaries into the typed v2 model."""

        metadata = ReportMetadata(
            repo_root=str(self.discovery.repo_root),
            analysis_root=str(self.discovery.analysis_root_file),
            analysis_root_module=self.discovery.analysis_root_module,
            inventory_root=self.discovery.inventory_root,
            extraction_backend=self.context.extraction_backend,
            generated_at_utc=self.context.generated_at_utc,
        )
        report = build_report_v2(
            metadata=metadata,
            phase_records=self.timing_by_phase(),
            phase_data=report_phase_data(self),
            findings=enrich_findings(
                self.findings,
                analysis_root_module=self.discovery.analysis_root_module,
                inventory_root=self.discovery.inventory_root,
                module_dag=self.module_dag,
                scope=getattr(self.context, "scope_plan", None),
            ),
            warnings=self.context.warnings,
        )
        return require_core_report_phases(report)


def require_core_report_phases(report: ReportV2) -> ReportV2:
    """Mark phases required for every valid analysis report."""

    phases = dict(report.phases)
    for name in CORE_REQUIRED_PHASES:
        phases[name] = replace(
            phases[name],
            required=True,
            disposition=default_phase_disposition(
                phases[name].status,
                True,
            ),
        )
    return replace(report, phases=phases)


def report_phase_data(result: PipelineResult) -> dict[str, Any]:
    """Return known owner payloads keyed by registered phase."""

    module_dag = (
        dict(result.module_dag)
        if isinstance(result.module_dag, Mapping)
        else result.module_dag
    )
    if result.context.budget is not None and isinstance(module_dag, dict):
        module_dag["run_resources"] = result.context.budget.metadata()
    return {
        "discover": {
            "status": result.context.source_index_status,
            "inventoryModuleCount": result.context.inventory_module_count,
            "indexedModuleCount": result.context.indexed_module_count,
            "failedModuleCount": max(
                0,
                result.context.inventory_module_count
                - result.context.indexed_module_count,
            ),
            "cache": dict(result.context.source_index_cache or {}),
            "diagnostics": [
                dict(row) for row in result.context.source_index_diagnostics
            ],
            "policies": {
                name: dict(row)
                for name, row in sorted(result.context.policy_inputs.items())
            },
        },
        "lean_extraction": result.context.lean_runtime,
        "module_dag": module_dag,
        "declaration_graph": result.declaration_graph,
        "module_readiness": result.module_readiness,
        "architecture_policy": result.architecture_policy,
        "source_patterns": result.source_patterns,
        "import_diet": result.import_diet,
        "proof_xray": result.proof_xray,
        "quality_baseline": result.quality_baseline,
        "refactoring_prescriptions": result.refactoring_prescriptions,
        "packet_evidence": list(result.packet_evidence),
        "review_regions": list(result.review_regions),
    }


def pipeline_result(
    context: RunContext,
    discovery: ModuleDiscovery,
    dag: dict[str, Any],
    **values: Any,
) -> PipelineResult:
    """Build one result from complete or explicitly retained phase values."""

    return PipelineResult(
        context=context,
        discovery=discovery,
        module_dag=dag,
        **values,
    )
