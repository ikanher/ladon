"""Pure coverage adaptation for current analysis and report collections.

Source-index coverage uses pointers local to the source-index artifact.  This
adapter consumes those rows as upstream authority, then emits only report-owned
rows whose pointers resolve in the canonical report-v3 ``sections`` object.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from ladon.coverage import (
    CollectionCoverage,
    CoverageCause,
    CoverageRegistry,
)
from ladon.source_index_models import (
    SOURCE_INDEX_DECLARATIONS_COVERAGE,
    SOURCE_INDEX_MODULES_COVERAGE,
    SourceIndex,
)


MODULE_DAG_MODULES_COVERAGE = "module_dag.modules"
DECLARATION_GRAPH_DECLARATIONS_COVERAGE = "declaration_graph.declarations"
REPORT_FINDINGS_COVERAGE = "report.findings"
REPORT_REVIEW_REGIONS_COVERAGE = "report.review_regions"
REPORT_PACKET_EVIDENCE_COVERAGE = "report.packet_evidence"
PROOF_XRAY_ROWS_COVERAGE = "proof_xray.rows"
REGISTERED_PHASE_COVERAGE = (
    ("module_dag", "import_boundary_coverage"),
    ("module_dag", "declaration_collision_coverage"),
    ("module_dag", "declaration_block_duplicate_coverage"),
    ("module_dag", "declaration_file_duplicate_coverage"),
    ("module_dag", "declaration_source_shape_coverage"),
    ("module_dag", "declaration_coreachable_coverage"),
    ("module_dag", "generated_family_candidate_coverage"),
    ("module_dag", "generated_family_partition_coverage"),
    ("module_dag", "audit_command_coverage"),
    ("module_dag", "resource_review_coverage"),
    ("module_dag", "architecture_joined_coverage"),
    ("module_dag", "inspection_option_coverage"),
    ("module_dag", "inspection_proof_mechanism_coverage"),
    ("module_dag", "resource_directive_coverage"),
    ("module_dag", "text_declaration_coverage"),
)


@dataclass(frozen=True)
class _PhaseState:
    status: str
    reason: str | None
    counters: Mapping[str, int]


@dataclass(frozen=True)
class _CollectionOwner:
    identity: str
    pointer: str
    phase: str
    population: str
    authority: str
    visible: int
    data_valid: bool
    total_keys: tuple[str, ...]
    upstream_refs: tuple[str, ...]
    adopt_upstream_total: bool = False


def build_report_coverage(
    source_index: SourceIndex | None,
    phase_status: Mapping[str, Any],
    phase_data: Mapping[str, Any],
    findings: Iterable[Any],
    *,
    scope: str,
    scope_fingerprint: str | None = None,
    analysis_fingerprint: str | None = None,
    module_dag_is_full_inventory: bool = False,
) -> CoverageRegistry:
    """Build report-v3 collection coverage from current analysis owners.

    ``phase_status`` accepts the pipeline's phase timing objects, typed report
    phase envelopes, status strings, or equivalent mappings.  Owner counters
    are treated as pre-cap totals when they exceed the visible collection.
    ``module_dag_is_full_inventory`` is deliberately explicit: a human-readable
    scope label is not sufficient evidence that an inventory total applies.
    Source-index rows are used only to propagate upstream completeness; their
    source-artifact-local ``#/entries`` pointers are not copied into the report
    registry.
    """

    finding_rows = tuple(findings)
    source_coverage = (
        source_index.coverage_registry()
        if source_index is not None
        else CoverageRegistry()
    )
    source_fingerprint = source_index.fingerprint if source_index is not None else None
    owners = (
        _mapping_owner(
            identity=MODULE_DAG_MODULES_COVERAGE,
            pointer="#/sections/module_dag/module_metadata",
            phase="module_dag",
            population="analyzed_modules",
            authority="module_import_graph",
            phase_data=phase_data,
            collection_key="module_metadata",
            total_keys=("module_count", "modules"),
            upstream_refs=(SOURCE_INDEX_MODULES_COVERAGE,),
            adopt_upstream_total=module_dag_is_full_inventory,
        ),
        _sequence_owner(
            identity=DECLARATION_GRAPH_DECLARATIONS_COVERAGE,
            pointer="#/sections/declaration_graph/declarations",
            phase="declaration_graph",
            population="analyzed_declarations",
            authority="declaration_graph",
            phase_data=phase_data,
            collection_key="declarations",
            total_keys=("declaration_count", "declarations"),
            upstream_refs=(SOURCE_INDEX_DECLARATIONS_COVERAGE,),
        ),
        _CollectionOwner(
            identity=REPORT_FINDINGS_COVERAGE,
            pointer="#/sections/findings",
            phase="findings",
            population="promoted_findings",
            authority="finding_selection",
            visible=len(finding_rows),
            data_valid=True,
            total_keys=("finding_count", "findings"),
            upstream_refs=(
                SOURCE_INDEX_MODULES_COVERAGE,
                SOURCE_INDEX_DECLARATIONS_COVERAGE,
            ),
        ),
        _sequence_owner(
            identity=REPORT_REVIEW_REGIONS_COVERAGE,
            pointer="#/sections/review_regions",
            phase="review_regions",
            population="review_regions",
            authority="review_region_synthesis",
            phase_data=phase_data,
            collection_key=None,
            total_keys=("region_count", "regions"),
            upstream_refs=(
                SOURCE_INDEX_MODULES_COVERAGE,
                SOURCE_INDEX_DECLARATIONS_COVERAGE,
            ),
        ),
        _sequence_owner(
            identity=REPORT_PACKET_EVIDENCE_COVERAGE,
            pointer="#/sections/packet_evidence",
            phase="packet_evidence",
            population="requested_packet_summaries",
            authority="packet_evidence_summary",
            phase_data=phase_data,
            collection_key=None,
            total_keys=("packet_count", "packet_dirs"),
            upstream_refs=(),
        ),
        _sequence_owner(
            identity=PROOF_XRAY_ROWS_COVERAGE,
            pointer="#/sections/proof_xray/rows",
            phase="proof_xray",
            population="classified_quoted_proof_xray_rows",
            authority="proof_xray_staging",
            phase_data=phase_data,
            collection_key="rows",
            total_keys=("row_count", "rows"),
            upstream_refs=(),
        ),
    )
    registry = CoverageRegistry()
    for owner in owners:
        registry = registry.register(
            _owner_coverage(
                owner,
                state=_phase_state(phase_status.get(owner.phase)),
                phase_data=phase_data.get(owner.phase),
                upstream=source_coverage,
                source_available=source_index is not None,
                scope=scope,
                source_fingerprint=source_fingerprint,
                scope_fingerprint=scope_fingerprint,
                analysis_fingerprint=analysis_fingerprint,
            )
        )
    for row in _registered_phase_coverage(phase_data):
        _require_report_coverage_identity(
            row,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
        )
        registry = registry.register(row)
    for row, upstream_refs in _registered_review_region_coverage(phase_data):
        _require_report_coverage_identity(
            row,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
        )
        for upstream_ref in upstream_refs:
            registry.require(upstream_ref)
        registry = registry.register(row)
    return registry


def _mapping_owner(
    *,
    identity: str,
    pointer: str,
    phase: str,
    population: str,
    authority: str,
    phase_data: Mapping[str, Any],
    collection_key: str,
    total_keys: tuple[str, ...],
    upstream_refs: tuple[str, ...],
    adopt_upstream_total: bool,
) -> _CollectionOwner:
    data = phase_data.get(phase)
    collection = data.get(collection_key) if isinstance(data, Mapping) else None
    valid = isinstance(collection, Mapping)
    return _CollectionOwner(
        identity=identity,
        pointer=pointer,
        phase=phase,
        population=population,
        authority=authority,
        visible=len(collection) if valid else 0,
        data_valid=valid,
        total_keys=total_keys,
        upstream_refs=upstream_refs,
        adopt_upstream_total=adopt_upstream_total,
    )


def _registered_phase_coverage(
    phase_data: Mapping[str, Any],
) -> tuple[CollectionCoverage, ...]:
    """Decode finite producer registrations owned by canonical report phases."""

    rows: list[CollectionCoverage] = []
    for phase, key in REGISTERED_PHASE_COVERAGE:
        data = phase_data.get(phase)
        raw = data.get(key) if isinstance(data, Mapping) else None
        if not isinstance(raw, Mapping):
            continue
        row = CollectionCoverage.from_mapping(raw)
        expected_prefix = f"#/sections/{phase}/"
        if not row.pointer.startswith(expected_prefix):
            raise ValueError(f"{row.identity} coverage pointer is outside {phase}")
        rows.append(row)
    return tuple(rows)


def _registered_review_region_coverage(
    phase_data: Mapping[str, Any],
) -> tuple[tuple[CollectionCoverage, tuple[str, ...]], ...]:
    """Decode bounded region collections owned by the report phase."""

    raw_regions = phase_data.get("review_regions")
    if not isinstance(raw_regions, list):
        return ()
    rows: list[tuple[CollectionCoverage, tuple[str, ...]]] = []
    for index, region in enumerate(raw_regions):
        if not isinstance(region, Mapping):
            continue
        raw_coverage = region.get("coverage")
        if not isinstance(raw_coverage, Mapping):
            continue
        coverage = CollectionCoverage.from_mapping(raw_coverage)
        expected_pointer = f"#/sections/review_regions/{index}/signals"
        if coverage.pointer != expected_pointer:
            raise ValueError(
                f"{coverage.identity} coverage pointer does not own "
                f"review region {index}"
            )
        if region.get("coverageRef") != coverage.identity:
            raise ValueError(f"review region {index} has mismatched coverageRef")
        upstream_refs = _coverage_ref_sequence(region.get("upstreamCoverageRefs"))
        rows.append((coverage, upstream_refs))
    return tuple(rows)


def _coverage_ref_sequence(raw: Any) -> tuple[str, ...]:
    """Decode a non-empty unique coverage-reference sequence."""

    if not (
        isinstance(raw, list)
        and raw
        and all(isinstance(row, str) and row for row in raw)
        and len(set(raw)) == len(raw)
    ):
        raise ValueError(
            "registered review region requires unique upstream coverage refs"
        )
    return tuple(raw)


def _require_report_coverage_identity(
    row: CollectionCoverage,
    *,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
) -> None:
    """Reject producer coverage that claims a different analysis input set."""

    if source_fingerprint is not None and row.source_fingerprint != source_fingerprint:
        raise ValueError(f"{row.identity} coverage source fingerprint is incompatible")
    if scope_fingerprint is not None and row.scope_fingerprint != scope_fingerprint:
        raise ValueError(f"{row.identity} coverage scope fingerprint is incompatible")


def _sequence_owner(
    *,
    identity: str,
    pointer: str,
    phase: str,
    population: str,
    authority: str,
    phase_data: Mapping[str, Any],
    collection_key: str | None,
    total_keys: tuple[str, ...],
    upstream_refs: tuple[str, ...],
) -> _CollectionOwner:
    data = phase_data.get(phase)
    collection = (
        data.get(collection_key)
        if collection_key is not None and isinstance(data, Mapping)
        else data
    )
    valid = isinstance(collection, (list, tuple))
    return _CollectionOwner(
        identity=identity,
        pointer=pointer,
        phase=phase,
        population=population,
        authority=authority,
        visible=len(collection) if valid else 0,
        data_valid=valid,
        total_keys=total_keys,
        upstream_refs=upstream_refs,
    )


def _owner_coverage(
    owner: _CollectionOwner,
    *,
    state: _PhaseState,
    phase_data: Any,
    upstream: CoverageRegistry,
    source_available: bool,
    scope: str,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
    analysis_fingerprint: str | None,
) -> CollectionCoverage:
    owner_total = _owner_total(owner, state, phase_data)
    observed = max(owner.visible, owner_total or 0)
    phase_causes = _owner_phase_causes(owner, state)
    upstream_rows, upstream_causes = _upstream_rows(
        owner,
        upstream,
        source_available=source_available,
    )
    causes = _unique_causes((*phase_causes, *upstream_causes))
    if state.status != "complete" or not owner.data_valid:
        return _unknown(
            owner,
            observed=observed,
            causes=causes,
            state=state,
            scope=scope,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
        )
    return _complete_owner_coverage(
        owner,
        owner_total=owner_total,
        observed=observed,
        state=state,
        upstream_rows=upstream_rows,
        causes=causes,
        source_available=source_available,
        scope=scope,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )


def _complete_owner_coverage(
    owner: _CollectionOwner,
    *,
    owner_total: int | None,
    observed: int,
    state: _PhaseState,
    upstream_rows: tuple[CollectionCoverage, ...],
    causes: tuple[CoverageCause, ...],
    source_available: bool,
    scope: str,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
    analysis_fingerprint: str | None,
) -> CollectionCoverage:
    if owner_total is None or owner_total < owner.visible:
        return _invalid_owner_count_coverage(
            owner,
            owner_total=owner_total,
            observed=observed,
            causes=causes,
            state=state,
            scope=scope,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
        )
    if owner.upstream_refs and not source_available:
        return _unknown(
            owner,
            observed=observed,
            causes=causes,
            state=state,
            scope=scope,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
        )
    if len(upstream_rows) != len(owner.upstream_refs):
        return _unknown(
            owner,
            observed=observed,
            causes=causes,
            state=state,
            scope=scope,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
        )
    incomplete_upstream = tuple(
        row for row in upstream_rows if row.completeness != "complete"
    )
    if incomplete_upstream:
        return _incomplete_upstream_coverage(
            owner,
            rows=incomplete_upstream,
            observed=observed,
            causes=causes,
            state=state,
            scope=scope,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
        )
    return _exact_owner_coverage(
        owner,
        owner_total=owner_total,
        causes=causes,
        scope=scope,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )


def _invalid_owner_count_coverage(
    owner: _CollectionOwner,
    *,
    owner_total: int | None,
    observed: int,
    causes: tuple[CoverageCause, ...],
    state: _PhaseState,
    scope: str,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
    analysis_fingerprint: str | None,
) -> CollectionCoverage:
    detail = (
        f"{owner.identity} has {owner.visible} visible members but no valid "
        "owner total at least that large"
    )
    if owner_total is not None:
        detail = f"{detail}; reported owner total was {owner_total}"
    conflict = CoverageCause(
        kind="analysis",
        identifier=f"{owner.identity}.owner_count_invalid",
        detail=detail,
    )
    return _unknown(
        owner,
        observed=observed,
        causes=_unique_causes((*causes, conflict)),
        state=state,
        scope=scope,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )


def _incomplete_upstream_coverage(
    owner: _CollectionOwner,
    *,
    rows: tuple[CollectionCoverage, ...],
    observed: int,
    causes: tuple[CoverageCause, ...],
    state: _PhaseState,
    scope: str,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
    analysis_fingerprint: str | None,
) -> CollectionCoverage:
    upstream_total = _adoptable_upstream_total(
        owner,
        rows,
        observed=observed,
    )
    if upstream_total is None:
        return _unknown(
            owner,
            observed=observed,
            causes=causes,
            state=state,
            scope=scope,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
        )
    return CollectionCoverage.exact(
        identity=owner.identity,
        pointer=owner.pointer,
        visible=owner.visible,
        observed_lower_bound=observed,
        total=upstream_total,
        population=owner.population,
        scope=scope,
        authority=owner.authority,
        causes=causes,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )


def _exact_owner_coverage(
    owner: _CollectionOwner,
    *,
    owner_total: int,
    causes: tuple[CoverageCause, ...],
    scope: str,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
    analysis_fingerprint: str | None,
) -> CollectionCoverage:
    exact_causes = _owner_cap_causes(owner, owner_total, causes)
    return CollectionCoverage.exact(
        identity=owner.identity,
        pointer=owner.pointer,
        visible=owner.visible,
        observed_lower_bound=owner_total,
        total=owner_total,
        population=owner.population,
        scope=scope,
        authority=owner.authority,
        causes=exact_causes,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )


def _owner_cap_causes(
    owner: _CollectionOwner,
    owner_total: int,
    causes: tuple[CoverageCause, ...],
) -> tuple[CoverageCause, ...]:
    if owner_total == owner.visible:
        return causes
    return _unique_causes(
        (
            *causes,
            CoverageCause(
                kind="analysis",
                identifier=f"{owner.identity}.owner_cap",
                detail=(
                    f"{owner.identity} exposes {owner.visible} of "
                    f"{owner_total} owner-counted members"
                ),
                controlling_cap=owner.visible,
            ),
        )
    )


def _owner_total(
    owner: _CollectionOwner,
    state: _PhaseState,
    phase_data: Any,
) -> int | None:
    if isinstance(phase_data, Mapping):
        for key in owner.total_keys:
            value = _count(phase_data.get(key))
            if value is not None:
                return value
    for key in owner.total_keys:
        value = _count(state.counters.get(key))
        if value is not None:
            return value
    return owner.visible if state.status == "complete" and owner.data_valid else None


def _upstream_rows(
    owner: _CollectionOwner,
    registry: CoverageRegistry,
    *,
    source_available: bool,
) -> tuple[tuple[CollectionCoverage, ...], tuple[CoverageCause, ...]]:
    if not owner.upstream_refs:
        return (), ()
    if not source_available:
        return (
            (),
            (
                CoverageCause(
                    kind="analysis",
                    identifier="coverage.source_index_unavailable",
                    detail=(
                        "current report collection has no source-index "
                        "coverage authority"
                    ),
                ),
            ),
        )
    rows: list[CollectionCoverage] = []
    causes: list[CoverageCause] = []
    for reference in owner.upstream_refs:
        row = registry.collections.get(reference)
        if row is None:
            causes.append(
                CoverageCause(
                    kind="analysis",
                    identifier="coverage.source_collection_unavailable",
                    detail=f"missing upstream coverage collection {reference}",
                )
            )
            continue
        rows.append(row)
        if row.completeness != "complete":
            causes.extend(row.causes)
    return tuple(rows), _unique_causes(causes)


def _adoptable_upstream_total(
    owner: _CollectionOwner,
    rows: tuple[CollectionCoverage, ...],
    *,
    observed: int,
) -> int | None:
    if not owner.adopt_upstream_total or len(rows) != 1:
        return None
    row = rows[0]
    if not row.total_known or row.total is None or row.total < observed:
        return None
    return row.total


def _phase_causes(
    owner: _CollectionOwner,
    state: _PhaseState,
) -> tuple[CoverageCause, ...]:
    if state.status == "complete":
        return ()
    detail = f"{owner.phase} phase status is {state.status}"
    if state.reason:
        detail = f"{detail}: {state.reason}"
    return (
        CoverageCause(
            kind="analysis",
            identifier=f"{owner.phase}.phase_{state.status}",
            detail=detail,
        ),
    )


def _owner_phase_causes(
    owner: _CollectionOwner,
    state: _PhaseState,
) -> tuple[CoverageCause, ...]:
    causes = _phase_causes(owner, state)
    if owner.data_valid:
        return causes
    invalid = CoverageCause(
        kind="analysis",
        identifier=f"{owner.phase}.invalid_collection",
        detail=(
            f"{owner.phase} did not expose the expected canonical "
            f"collection for {owner.identity}"
        ),
    )
    return (*causes, invalid)


def _unknown(
    owner: _CollectionOwner,
    *,
    observed: int,
    causes: tuple[CoverageCause, ...],
    state: _PhaseState,
    scope: str,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
    analysis_fingerprint: str | None,
) -> CollectionCoverage:
    if not causes:
        causes = (
            CoverageCause(
                kind="analysis",
                identifier=f"{owner.identity}.coverage_unavailable",
                detail=f"coverage is unavailable for {owner.identity}",
            ),
        )
    completeness = (
        "unavailable"
        if state.status in {"missing", "skipped", "failed"} and observed == 0
        else "partial"
    )
    return CollectionCoverage.unknown(
        identity=owner.identity,
        pointer=owner.pointer,
        visible=owner.visible,
        observed_lower_bound=observed,
        completeness=completeness,
        population=owner.population,
        scope=scope,
        authority=owner.authority,
        causes=causes,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )


def _phase_state(raw: Any) -> _PhaseState:
    status = _field(raw, "status")
    normalized = {
        "ok": "complete",
        "complete": "complete",
        "partial": "partial",
        "skipped": "skipped",
        "error": "failed",
        "failed": "failed",
    }.get(str(status), "missing")
    reason = _field(raw, "reason")
    counters = _field(raw, "counters")
    return _PhaseState(
        status=normalized,
        reason=(str(reason) if reason is not None and reason != "" else None),
        counters={
            str(key): value
            for key, value in (
                counters.items() if isinstance(counters, Mapping) else ()
            )
            if _count(value) is not None
        },
    )


def _field(raw: Any, name: str) -> Any:
    if isinstance(raw, str):
        return raw if name == "status" else None
    if isinstance(raw, Mapping):
        return raw.get(name)
    return getattr(raw, name, None)


def _count(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _unique_causes(
    causes: Iterable[CoverageCause],
) -> tuple[CoverageCause, ...]:
    unique = {
        (
            cause.kind,
            cause.identifier,
            cause.detail,
            cause.controlling_cap,
        ): cause
        for cause in causes
    }
    return tuple(unique[key] for key in sorted(unique))


__all__ = [
    "DECLARATION_GRAPH_DECLARATIONS_COVERAGE",
    "MODULE_DAG_MODULES_COVERAGE",
    "PROOF_XRAY_ROWS_COVERAGE",
    "REPORT_FINDINGS_COVERAGE",
    "REPORT_PACKET_EVIDENCE_COVERAGE",
    "REPORT_REVIEW_REGIONS_COVERAGE",
    "REGISTERED_PHASE_COVERAGE",
    "build_report_coverage",
]
