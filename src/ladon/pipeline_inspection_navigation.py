"""Bounded report-owned navigation rows from the typed lexical index.

These rows let the ordinary report artifact support the same CLI inspection
nouns as a source-index artifact.  They remain lexical navigation evidence:
their presence does not establish Lean elaboration, proof use, runtime cost,
or theorem quality.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar

from ladon.coverage import CollectionCoverage, CoverageCause
from ladon.ir import LeanModule
from ladon.source_index_models import (
    SOURCE_INDEX_DECLARATIONS_COVERAGE,
    SOURCE_INDEX_OPTIONS_COVERAGE,
    SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE,
    SourceIndex,
)
from ladon.source_index_navigation_codec import (
    source_index_option_mapping,
    source_index_proof_mechanism_mapping,
)


INSPECTION_NAVIGATION_SCHEMA = "ladon-inspection-navigation-v1"
MAX_INSPECTION_NAVIGATION_ROWS = 10_000
INSPECTION_OPTIONS_COVERAGE = "module_dag.inspection_options"
INSPECTION_PROOF_MECHANISMS_COVERAGE = "module_dag.inspection_proof_mechanisms"
TEXT_DECLARATIONS_COVERAGE = "module_dag.text_declarations"
_NAVIGATION_POINTER = "#/sections/module_dag/inspection_navigation"
_RowT = TypeVar("_RowT")


def attach_inspection_navigation(
    dag: dict[str, Any],
    modules: Mapping[str, LeanModule],
    source_index: SourceIndex | None,
) -> None:
    """Attach bounded option and proof-token rows with truthful coverage."""

    option_rows, option_total = _bounded_navigation_rows(
        modules,
        rows=lambda module: module.option_rows,
        mapping=source_index_option_mapping,
        coverage_ref=INSPECTION_OPTIONS_COVERAGE,
    )
    mechanism_rows, mechanism_total = _bounded_navigation_rows(
        modules,
        rows=lambda module: module.proof_mechanisms,
        mapping=source_index_proof_mechanism_mapping,
        coverage_ref=INSPECTION_PROOF_MECHANISMS_COVERAGE,
        reserve_key=lambda row: (row.kind, row.mechanism, row.status),
        evidence_kind=lambda row: f"{row.kind}:{row.mechanism}",
    )
    dag["inspection_navigation"] = {
        "schema": INSPECTION_NAVIGATION_SCHEMA,
        "options": option_rows,
        "proofMechanisms": mechanism_rows,
    }
    dag["inspection_option_coverage"] = _navigation_coverage(
        dag,
        identity=INSPECTION_OPTIONS_COVERAGE,
        pointer=f"{_NAVIGATION_POINTER}/options",
        visible=len(option_rows),
        observed=option_total,
        population="lexical_option_commands",
        upstream_identity=SOURCE_INDEX_OPTIONS_COVERAGE,
        source_index=source_index,
    ).to_dict()
    dag["inspection_proof_mechanism_coverage"] = _navigation_coverage(
        dag,
        identity=INSPECTION_PROOF_MECHANISMS_COVERAGE,
        pointer=f"{_NAVIGATION_POINTER}/proofMechanisms",
        visible=len(mechanism_rows),
        observed=mechanism_total,
        population="lexical_proof_mechanism_occurrences",
        upstream_identity=SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE,
        source_index=source_index,
    ).to_dict()
    declaration_visible = sum(
        len(row.get("textDeclarations", ()))
        for row in dag.get("module_metadata", {}).values()
        if isinstance(row, Mapping)
    )
    declaration_observed = sum(
        len(module.declaration_evidence) for module in modules.values()
    )
    dag["text_declaration_coverage"] = _navigation_coverage(
        dag,
        identity=TEXT_DECLARATIONS_COVERAGE,
        pointer="#/sections/module_dag/module_metadata",
        visible=declaration_visible,
        observed=declaration_observed,
        population="lexical_declaration_evidence",
        upstream_identity=SOURCE_INDEX_DECLARATIONS_COVERAGE,
        source_index=source_index,
    ).to_dict()


def _bounded_navigation_rows(
    modules: Mapping[str, LeanModule],
    *,
    rows: Callable[[LeanModule], Sequence[_RowT]],
    mapping: Callable[[_RowT], dict[str, Any]],
    coverage_ref: str,
    reserve_key: Callable[[_RowT], tuple[str, ...]] | None = None,
    evidence_kind: Callable[[_RowT], str] | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Select rows round-robin so large modules cannot erase small modules."""

    populations: list[Sequence[_RowT]] = []
    for name in sorted(modules):
        population = rows(modules[name])
        if population:
            populations.append(population)
    observed = sum(len(population) for population in populations)
    reserved = _reserved_rows(populations, key=reserve_key)
    selected = [
        *reserved,
        *_round_robin_rows(
            populations,
            limit=max(0, MAX_INSPECTION_NAVIGATION_ROWS - len(reserved)),
            excluded={id(row) for row in reserved},
        ),
    ]
    return [
        {
            **mapping(row),
            **(
                {"evidenceKind": evidence_kind(row)}
                if evidence_kind is not None
                else {}
            ),
            "coverageRef": coverage_ref,
        }
        for row in selected
    ], observed


def _round_robin_rows(
    populations: Sequence[Sequence[_RowT]],
    *,
    limit: int,
    excluded: set[int] | None = None,
) -> list[_RowT]:
    """Return a deterministic fair prefix without flattening every row."""

    omitted = excluded or set()
    active = deque((population, 0) for population in populations if population)
    selected: list[_RowT] = []
    while active and len(selected) < limit:
        population, index = active.popleft()
        next_index = _next_included_index(population, index, omitted)
        if next_index >= len(population):
            continue
        selected.append(population[next_index])
        next_index += 1
        if next_index < len(population):
            active.append((population, next_index))
    return selected


def _reserved_rows(
    populations: Sequence[Sequence[_RowT]],
    *,
    key: Callable[[_RowT], tuple[str, ...]] | None,
) -> list[_RowT]:
    """Reserve one deterministic witness for every finite evidence kind."""

    if key is None:
        return []
    selected: list[_RowT] = []
    seen: set[tuple[str, ...]] = set()
    for population in populations:
        for row in population:
            row_key = key(row)
            if row_key in seen:
                continue
            seen.add(row_key)
            selected.append(row)
            if len(selected) == MAX_INSPECTION_NAVIGATION_ROWS:
                return selected
    return selected


def _next_included_index(
    population: Sequence[_RowT],
    index: int,
    excluded: set[int],
) -> int:
    """Skip rows already retained by a diversity reservation."""

    while index < len(population) and id(population[index]) in excluded:
        index += 1
    return index


def _navigation_coverage(
    dag: Mapping[str, Any],
    *,
    identity: str,
    pointer: str,
    visible: int,
    observed: int,
    population: str,
    upstream_identity: str,
    source_index: SourceIndex | None,
) -> CollectionCoverage:
    """Describe report retention without claiming completeness for failed input."""

    upstream = (
        source_index.coverage_registry().require(upstream_identity)
        if source_index is not None
        else None
    )
    cap_causes = _cap_causes(identity, visible=visible, observed=observed)
    common = {
        "identity": identity,
        "pointer": pointer,
        "visible": visible,
        "population": population,
        "scope": "selected_module_graph",
        "authority": "lexical_text",
        "source_fingerprint": (
            upstream.source_fingerprint if upstream is not None else None
        ),
        "scope_fingerprint": _scope_fingerprint(dag),
    }
    if upstream is not None and upstream.completeness == "complete":
        return CollectionCoverage.exact(
            total=observed,
            observed_lower_bound=observed,
            causes=cap_causes,
            **common,
        )
    return CollectionCoverage.unknown(
        observed_lower_bound=observed,
        completeness=(upstream.completeness if upstream is not None else "unavailable"),
        causes=(
            (*upstream.causes, *cap_causes)
            if upstream is not None
            else (
                CoverageCause(
                    kind="analysis",
                    identifier=f"{identity}.source_index_unavailable",
                    detail=(
                        "Report navigation coverage has no source-index "
                        "population authority."
                    ),
                ),
                *cap_causes,
            )
        ),
        **common,
    )


def _cap_causes(
    identity: str,
    *,
    visible: int,
    observed: int,
) -> tuple[CoverageCause, ...]:
    """Describe only a cap that actually omitted observed rows."""

    if visible >= observed:
        return ()
    return (
        CoverageCause(
            kind="analysis",
            identifier=f"{identity}.report_navigation_limit",
            detail=(
                f"The report retains {visible} of {observed} observed navigation rows."
            ),
            controlling_cap=MAX_INSPECTION_NAVIGATION_ROWS,
        ),
    )


def _scope_fingerprint(dag: Mapping[str, Any]) -> str | None:
    """Read the exact selected-scope identity from the module-DAG owner."""

    scope = dag.get("analysis_scope")
    fingerprint = scope.get("fingerprint") if isinstance(scope, Mapping) else None
    return fingerprint if isinstance(fingerprint, str) and fingerprint else None


__all__ = [
    "INSPECTION_NAVIGATION_SCHEMA",
    "INSPECTION_OPTIONS_COVERAGE",
    "INSPECTION_PROOF_MECHANISMS_COVERAGE",
    "MAX_INSPECTION_NAVIGATION_ROWS",
    "TEXT_DECLARATIONS_COVERAGE",
    "attach_inspection_navigation",
]
