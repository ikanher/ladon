"""Phase-timed pipeline orchestration for Ladon's clean core.

The pipeline is the boundary between side effects and pure analysis. It keeps
phase names stable so future optimization, caching, and feature reintroduction
can target one step without rebuilding a monolith.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Iterator, Mapping

from ladon.analysis.findings import summarize_findings
from ladon.analysis.declaration_graph import summarize_declaration_graph
from ladon.analysis.module_dag import summarize_module_dag
from ladon.analysis.quality_baseline import summarize_quality_baseline
from ladon.analysis.witness_packet import summarize_packet_evidence
from ladon.extraction import ModuleDiscovery, discover_modules
from ladon.ir import ExtractionBundle, LeanDeclaration, LeanModule
from ladon.lean_extraction import extract_with_lean_helper
from ladon.render import report_payload


REQUIRED_PHASES = (
    "discover",
    "lean_extraction",
    "indexing",
    "module_dag",
    "quality_baseline",
    "findings",
    "packet_evidence",
    "rendering",
)


@dataclass(frozen=True)
class PhaseTiming:
    """Timing and status for one named pipeline phase."""

    name: str
    elapsed_seconds: float
    status: str
    counters: dict[str, int] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        """Return the stable JSON shape used in reports."""

        return {
            "name": self.name,
            "elapsed_seconds": self.elapsed_seconds,
            "status": self.status,
            "counters": dict(sorted(self.counters.items())),
        }


@dataclass
class RunContext:
    """User request and run-local metadata for one Ladon invocation."""

    repo_root: Path
    requested_root: str | None = None
    extraction_backend: str = "text"
    lean_extraction_scope: str = "root"
    lean_cache_dir: Path | None = None
    packet_dirs: tuple[Path, ...] = ()
    lean_extractor: Callable[["RunContext", ModuleDiscovery], ExtractionBundle | dict[str, LeanModule]] | None = None
    generated_at_utc: str | None = None
    warnings: list[str] = field(default_factory=list)
    timings: list[PhaseTiming] = field(default_factory=list)

    @contextmanager
    def phase(self, name: str, *, status: str = "ok") -> Iterator[dict[str, int]]:
        """Record elapsed time for a phase and let callers fill counters."""

        counters: dict[str, int] = {}
        start = perf_counter()
        phase_status = status
        try:
            yield counters
        except Exception:
            phase_status = "error"
            raise
        finally:
            elapsed = max(0.0, perf_counter() - start)
            self.timings.append(PhaseTiming(name, elapsed, phase_status, counters))

    def record_skipped(self, name: str, reason: str) -> None:
        """Record a phase that is intentionally absent in the clean core."""

        self.timings.append(PhaseTiming(name, 0.0, "skipped", {"reason": len(reason)}))


@dataclass(frozen=True)
class PipelineResult:
    """Normalized output of one clean-core pipeline run."""

    context: RunContext
    discovery: ModuleDiscovery
    module_dag: dict[str, Any]
    declaration_graph: dict[str, Any] | None = None
    quality_baseline: dict[str, Any] | None = None
    findings: list[dict[str, Any]] = field(default_factory=list)
    packet_evidence: list[dict[str, Any]] = field(default_factory=list)

    def timing_by_phase(self) -> dict[str, PhaseTiming]:
        """Return the last timing record for each phase name."""

        return {timing.name: timing for timing in self.context.timings}

    def to_report_payload(self) -> dict[str, Any]:
        """Build the additive JSON payload consumed by renderers."""

        payload = report_payload(
            self.discovery,
            self.module_dag,
            generated_at_utc=self.context.generated_at_utc,
            warnings=self.context.warnings,
        )
        if self.declaration_graph is not None:
            payload["declaration_graph"] = self.declaration_graph
        if self.quality_baseline is not None:
            payload["quality_baseline"] = self.quality_baseline
        payload["findings"] = list(self.findings)
        if self.packet_evidence:
            payload["packet_evidence"] = list(self.packet_evidence)
        payload["pipeline"] = {"timings": timing_payload(self.context.timings)}
        return payload


def adapt_modules(modules: Mapping[str, LeanModule]) -> dict[str, LeanModule]:
    """Normalize current extraction modules into Ladon's stable IR map."""

    return dict(sorted(modules.items()))


def merge_module_inventory(
    text_modules: Mapping[str, LeanModule],
    helper_modules: Mapping[str, LeanModule],
) -> dict[str, LeanModule]:
    """Merge text inventory with helper rows, preferring helper rows."""

    return adapt_modules({**text_modules, **helper_modules})


def text_extraction_bundle(discovery: ModuleDiscovery) -> ExtractionBundle:
    """Adapt text extraction to the backend-neutral bundle shape."""

    return ExtractionBundle(modules=adapt_modules(discovery.modules), declarations={})


def run_pipeline(context: RunContext) -> PipelineResult:
    """Run the clean-core pipeline and return normalized results."""

    with context.phase("discover") as counters:
        discovery = discover_modules(context.repo_root, context.requested_root)
        counters["modules"] = len(discovery.modules)

    if context.extraction_backend == "lean":
        with context.phase("lean_extraction") as counters:
            bundle = coerce_extraction_bundle(run_lean_extractor(context, discovery))
            modules = merge_module_inventory(discovery.modules, bundle.modules)
            bundle = ExtractionBundle(
                modules=modules,
                declarations=bundle.declarations,
                counters=bundle.counters,
            )
            discovery = discovery_with_modules(discovery, bundle.modules)
            declarations = bundle.declarations or {}
            counters["modules"] = len(bundle.modules)
            counters["declarations"] = len(declarations)
            counters.update(bundle.counters)
    else:
        bundle = text_extraction_bundle(discovery)
        declarations = bundle.declarations or {}
        context.record_skipped("lean_extraction", "text backend selected")

    with context.phase("indexing") as counters:
        modules = adapt_modules(bundle.modules)
        counters["modules"] = len(modules)

    with context.phase("module_dag") as counters:
        dag = summarize_module_dag(modules, chosen_roots=(discovery.analysis_root_module,))
        counters["edges"] = int(dag["edge_count"])

    if declarations:
        with context.phase("declaration_graph") as counters:
            declaration_graph = summarize_declaration_graph(
                declarations,
                chosen_roots=declaration_roots_for_module(
                    discovery.analysis_root_module,
                    declarations,
                ),
                known_reference_names=reference_inventory_names(modules),
            )
            counters["declarations"] = int(declaration_graph["declaration_count"])
            counters["edges"] = int(declaration_graph["edge_count"])
    else:
        declaration_graph = None
        context.record_skipped("declaration_graph", "no declaration IR available")

    with context.phase("quality_baseline") as counters:
        quality_baseline = summarize_quality_baseline(dag, declaration_graph)
        counters["metrics"] = len(quality_baseline["metrics"])

    with context.phase("findings") as counters:
        findings = summarize_findings(dag, declaration_graph, quality_baseline)
        counters["findings"] = len(findings)

    if context.packet_dirs:
        with context.phase("packet_evidence") as counters:
            packet_evidence = [
                summarize_packet_evidence(packet_dir)
                for packet_dir in context.packet_dirs
            ]
            counters["packet_dirs"] = len(packet_evidence)
    else:
        packet_evidence = []
        context.record_skipped("packet_evidence", "no packet directories requested")

    result = PipelineResult(
        context=context,
        discovery=discovery,
        module_dag=dag,
        declaration_graph=declaration_graph,
        quality_baseline=quality_baseline,
        findings=findings,
        packet_evidence=packet_evidence,
    )
    with context.phase("rendering") as counters:
        result.to_report_payload()
        counters["payloads"] = 1
    return result


def coerce_extraction_bundle(
    extracted: ExtractionBundle | dict[str, LeanModule],
) -> ExtractionBundle:
    """Accept legacy module maps from tests while preferring bundles."""

    if isinstance(extracted, ExtractionBundle):
        return extracted
    modules = adapt_modules(extracted)
    return ExtractionBundle(modules=modules, declarations=declarations_from_modules(modules))


def declarations_from_modules(
    modules: Mapping[str, LeanModule],
) -> dict[str, LeanDeclaration]:
    """Create declaration rows without references from module declaration names."""

    return {
        declaration_name: LeanDeclaration(name=declaration_name, module=module.name)
        for module in modules.values()
        for declaration_name in module.declarations
    }


def reference_inventory_names(modules: Mapping[str, LeanModule]) -> tuple[str, ...]:
    """Return declaration names known from text or helper module inventory."""

    names = {
        variant
        for module in modules.values()
        for declaration in module.declarations
        for variant in declaration_name_variants(declaration)
    }
    return tuple(sorted(names))


def declaration_name_variants(declaration: str) -> tuple[str, str]:
    """Return full and basename variants for one declaration name."""

    return declaration, declaration.rsplit(".", 1)[-1]


def declaration_roots_for_module(
    module_name: str,
    declarations: Mapping[str, LeanDeclaration],
) -> tuple[str, ...]:
    """Use declarations owned by the analysis root module as graph roots."""

    return tuple(
        name
        for name, declaration in sorted(declarations.items())
        if declaration.module == module_name
    )


def discovery_with_modules(
    discovery: ModuleDiscovery,
    modules: dict[str, LeanModule],
) -> ModuleDiscovery:
    """Return an immutable discovery record with backend-selected modules."""

    return ModuleDiscovery(
        repo_root=discovery.repo_root,
        analysis_root_file=discovery.analysis_root_file,
        analysis_root_module=discovery.analysis_root_module,
        inventory_root=discovery.inventory_root,
        modules=modules,
    )


def count_declarations(modules: Mapping[str, LeanModule]) -> int:
    """Count declarations in a backend-normalized module map."""

    return sum(len(module.declarations) for module in modules.values())


def run_lean_extractor(
    context: RunContext,
    discovery: ModuleDiscovery,
) -> ExtractionBundle | dict[str, LeanModule]:
    """Run the configured Lean extractor or the bundled parser-helper backend."""

    extractor = context.lean_extractor or default_lean_extractor
    return extractor(context, discovery)


def default_lean_extractor(
    context: RunContext,
    discovery: ModuleDiscovery,
) -> ExtractionBundle:
    """Run the real parser-helper extractor for the Lean backend."""

    return extract_with_lean_helper(
        discovery,
        scope=context.lean_extraction_scope,
        cache_dir=context.lean_cache_dir,
    )


def timing_payload(timings: list[PhaseTiming]) -> dict[str, dict[str, Any]]:
    """Return report timings keyed by phase name."""

    return {timing.name: timing.to_json() for timing in timings}
