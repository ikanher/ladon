"""Typed import-boundary classification over registered module identities."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ladon.coverage import (
    CollectionCoverage,
    CoverageCause,
    InspectionAction,
)
from ladon.ir import LeanModule

IMPORT_BOUNDARY_COVERAGE = "module_dag.import_boundaries"
IMPORT_BOUNDARY_POINTER = "#/sections/module_dag/import_boundaries"
IMPORT_BOUNDARY_CLASSIFICATIONS = (
    "selected_internal",
    "known_inventory_boundary",
    "external_boundary",
    "missing_internal",
    "unavailable",
)
IMPORT_BOUNDARY_AUTHORITY = "lexical_text_and_source_index_membership"
IMPORT_BOUNDARY_NONCLAIM = (
    "Lexical import and inventory-identity evidence only; not a Lean resolver, "
    "elaboration result, compilation diagnostic, or defect confirmation."
)


@dataclass(frozen=True)
class ImportBoundaryRow:
    """One canonical selected-module import occurrence and its boundary class."""

    source_module: str
    source_path: str
    target_module: str
    site_ordinal: int
    line: int | None
    import_text: str
    synthetic: bool
    classification: str
    authority: str
    source_fingerprint: str | None
    scope_fingerprint: str | None
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        if self.classification not in IMPORT_BOUNDARY_CLASSIFICATIONS:
            raise ValueError(
                f"unsupported import-boundary class: {self.classification}"
            )
        if not all(
            (
                self.source_module,
                self.source_path,
                self.target_module,
                self.authority,
            )
        ):
            raise ValueError("import-boundary identity fields must be non-empty")
        if self.site_ordinal < 0:
            raise ValueError("import-boundary site ordinal must be non-negative")
        if self.line is not None and self.line < 1:
            raise ValueError("import-boundary line must be positive")
        unavailable = self.classification == "unavailable"
        if unavailable != (self.unavailable_reason is not None):
            raise ValueError(
                "only unavailable import boundaries carry an unavailable reason"
            )

    @property
    def identity(self) -> str:
        """Return a deterministic occurrence identity within the selected DAG."""

        return (
            f"import-boundary:{self.source_module}:"
            f"{self.site_ordinal}:{self.target_module}"
        )

    def to_dict(self, *, row_index: int) -> dict[str, Any]:
        """Return the canonical report row with lexical and population refs."""

        row = {
            "id": self.identity,
            "classification": self.classification,
            "sourceModule": self.source_module,
            "sourcePath": self.source_path,
            "targetModule": self.target_module,
            "siteOrdinal": self.site_ordinal,
            "line": self.line,
            "importText": self.import_text,
            "synthetic": self.synthetic,
            "authority": self.authority,
            "classificationAuthority": "ladon_derived",
            "sourceIndexFingerprint": self.source_fingerprint,
            "scopeFingerprint": self.scope_fingerprint,
            "coverageRef": IMPORT_BOUNDARY_COVERAGE,
            "evidenceRefs": self._evidence_refs(row_index),
            "inspectionAction": InspectionAction(
                noun="imports",
                stable_id=self.identity,
            ).to_dict(),
            "nonclaim": IMPORT_BOUNDARY_NONCLAIM,
        }
        if self.unavailable_reason is not None:
            row["unavailableReason"] = self.unavailable_reason
        return row

    def _evidence_refs(self, row_index: int) -> list[dict[str, Any]]:
        """Link the lexical occurrence, selected scope, and full inventory."""

        return [
            {
                "type": "source",
                "pointer": f"{IMPORT_BOUNDARY_POINTER}/{row_index}",
                "path": self.source_path,
                "line": self.line,
            },
            {
                "type": "scope_population",
                "pointer": "#/sections/module_dag/analysis_scope",
                "fingerprint": self.scope_fingerprint,
            },
            {
                "type": "source_index_inventory",
                "pointer": "#/sections/module_dag/source_index",
                "module": self.target_module,
                "fingerprint": self.source_fingerprint,
            },
        ]

    def to_missing_internal_dict(self) -> dict[str, Any]:
        """Return the frozen compatibility shape for a genuine missing row."""

        if self.classification != "missing_internal":
            raise ValueError("only missing-internal boundaries use this adapter")
        return {
            "sourceModule": self.source_module,
            "sourcePath": self.source_path,
            "targetModule": self.target_module,
            "line": self.line,
            "importText": self.import_text,
            "authority": "lexical_text",
            "nonclaim": (
                "Missing conventional source-path evidence only; not a Lean "
                "resolver or compilation diagnostic."
            ),
        }


@dataclass(frozen=True)
class ImportBoundaryResult:
    """Pure, deterministic import-boundary rows plus shared collection coverage."""

    rows: tuple[ImportBoundaryRow, ...]
    coverage: CollectionCoverage

    def __post_init__(self) -> None:
        if self.coverage.identity != IMPORT_BOUNDARY_COVERAGE:
            raise ValueError(
                "import-boundary result has the wrong coverage identity"
            )
        if self.coverage.visible != len(self.rows):
            raise ValueError(
                "import-boundary coverage must count every visible occurrence"
            )

    def row_dicts(self) -> list[dict[str, Any]]:
        """Return report rows in their canonical order."""

        return [
            row.to_dict(row_index=index)
            for index, row in enumerate(self.rows)
        ]

    def counts(self) -> dict[str, int]:
        """Count every supported classification, including zero populations."""

        counts = Counter(row.classification for row in self.rows)
        return {
            classification: counts[classification]
            for classification in IMPORT_BOUNDARY_CLASSIFICATIONS
        }

    def missing_internal_imports(self) -> list[dict[str, Any]]:
        """Adapt only genuine missing boundaries to the compatibility surface."""

        return [
            row.to_missing_internal_dict()
            for row in self.rows
            if row.classification == "missing_internal"
        ]


@dataclass(frozen=True)
class _ImportOccurrence:
    """One normalized real or synthetic import occurrence before classification."""

    source_module: str
    source_path: str
    target_module: str
    original_ordinal: int
    line: int | None
    import_text: str
    synthetic: bool


def classify_import_boundaries(
    modules: Mapping[str, LeanModule],
    *,
    chosen_roots: Sequence[str] = (),
    full_inventory_modules: Iterable[str] | None = None,
    full_inventory_fingerprint: str | None = None,
    scope_source_fingerprint: str | None = None,
    scope_fingerprint: str | None = None,
    selected_import_coverage: CollectionCoverage | None = None,
) -> ImportBoundaryResult:
    """Classify every canonical selected import occurrence.

    Full-inventory membership is usable only when the inventory and scope cite
    the same non-empty source-index fingerprint and every selected module is a
    member of that inventory. Selected-internal occurrences remain known from
    the selected mapping itself; all other rows fail closed as ``unavailable``
    when the inventory evidence cannot be joined.
    """

    occurrences = _canonical_import_occurrences(modules)
    inventory = _normalized_inventory(full_inventory_modules)
    unavailable_reason = _inventory_unavailable_reason(
        selected_modules=frozenset(modules),
        full_inventory_modules=inventory,
        full_inventory_supplied=full_inventory_modules is not None,
        full_inventory_fingerprint=full_inventory_fingerprint,
        scope_source_fingerprint=scope_source_fingerprint,
    )
    project_namespaces = owned_inventory_namespaces(
        modules,
        chosen_roots,
        inventory if unavailable_reason is None else None,
    )
    rows = _classified_rows(
        occurrences,
        selected_modules=frozenset(modules),
        full_inventory_modules=inventory,
        inventory_unavailable_reason=unavailable_reason,
        chosen_roots=chosen_roots,
        project_namespaces=project_namespaces,
        full_inventory_fingerprint=full_inventory_fingerprint,
        scope_fingerprint=scope_fingerprint,
    )
    return ImportBoundaryResult(
        rows=rows,
        coverage=_import_boundary_coverage(
            visible=len(rows),
            selected_import_coverage=selected_import_coverage,
            source_fingerprint=full_inventory_fingerprint,
            scope_fingerprint=scope_fingerprint,
        ),
    )


def _classified_rows(
    occurrences: Sequence[_ImportOccurrence],
    *,
    selected_modules: frozenset[str],
    full_inventory_modules: frozenset[str],
    inventory_unavailable_reason: str | None,
    chosen_roots: Sequence[str],
    project_namespaces: frozenset[str],
    full_inventory_fingerprint: str | None,
    scope_fingerprint: str | None,
) -> tuple[ImportBoundaryRow, ...]:
    """Classify normalized rows with stable occurrence ordinals."""

    return tuple(
        _classify_import_occurrence(
            occurrence,
            site_ordinal=site_ordinal,
            selected_modules=selected_modules,
            full_inventory_modules=full_inventory_modules,
            inventory_unavailable_reason=inventory_unavailable_reason,
            chosen_roots=chosen_roots,
            project_namespaces=project_namespaces,
            full_inventory_fingerprint=full_inventory_fingerprint,
            scope_fingerprint=scope_fingerprint,
        )
        for site_ordinal, occurrence in enumerate(occurrences)
    )


def _canonical_import_occurrences(
    modules: Mapping[str, LeanModule],
) -> tuple[_ImportOccurrence, ...]:
    """Return every real site plus imports lacking source-site evidence."""

    occurrences = [
        occurrence
        for module in sorted(modules.values(), key=lambda item: item.name)
        for occurrence in _module_import_occurrences(module)
    ]
    return tuple(sorted(occurrences, key=_import_occurrence_key))


def _module_import_occurrences(module: LeanModule) -> list[_ImportOccurrence]:
    """Preserve duplicate sites and synthesize only unmatched import entries."""

    rows = [
        _ImportOccurrence(
            source_module=module.name,
            source_path=module.path,
            target_module=site.module,
            original_ordinal=index,
            line=site.line,
            import_text=site.text or "",
            synthetic=False,
        )
        for index, site in enumerate(module.import_sites)
    ]
    represented = Counter(site.module for site in module.import_sites)
    next_ordinal = len(rows)
    for target in module.imports:
        if represented[target]:
            represented[target] -= 1
            continue
        rows.append(
            _ImportOccurrence(
                source_module=module.name,
                source_path=module.path,
                target_module=target,
                original_ordinal=next_ordinal,
                line=None,
                import_text=f"import {target}",
                synthetic=True,
            )
        )
        next_ordinal += 1
    return rows


def _import_occurrence_key(row: _ImportOccurrence) -> tuple[Any, ...]:
    """Return a stable ordering key that puts exact line anchors first."""

    return (
        row.source_module,
        row.line is None,
        row.line if row.line is not None else 0,
        row.target_module,
        row.import_text,
        row.original_ordinal,
    )


def _normalized_inventory(
    full_inventory_modules: Iterable[str] | None,
) -> frozenset[str]:
    """Normalize a caller-owned identity population without inferring names."""

    if full_inventory_modules is None:
        return frozenset()
    names = tuple(full_inventory_modules)
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError(
            "full inventory module identities must be non-empty strings"
        )
    return frozenset(names)


def _inventory_unavailable_reason(
    *,
    selected_modules: frozenset[str],
    full_inventory_modules: frozenset[str],
    full_inventory_supplied: bool,
    full_inventory_fingerprint: str | None,
    scope_source_fingerprint: str | None,
) -> str | None:
    """Return why inventory membership cannot support a boundary claim."""

    if not full_inventory_supplied:
        return "full_inventory_not_supplied"
    if not full_inventory_fingerprint or not scope_source_fingerprint:
        return "source_index_fingerprint_unavailable"
    if full_inventory_fingerprint != scope_source_fingerprint:
        return "source_index_fingerprint_mismatch"
    if not selected_modules.issubset(full_inventory_modules):
        return "selected_modules_absent_from_full_inventory"
    return None


def owned_inventory_namespaces(
    modules: Mapping[str, LeanModule],
    chosen_roots: Sequence[str],
    full_inventory_modules: frozenset[str] | None,
) -> frozenset[str]:
    """Apply the existing top-namespace ownership rule to registered identities."""

    names = [
        *modules,
        *chosen_roots,
        *(full_inventory_modules or ()),
    ]
    return frozenset(name.split(".", 1)[0] for name in names if name)


def _classify_import_occurrence(
    occurrence: _ImportOccurrence,
    *,
    site_ordinal: int,
    selected_modules: frozenset[str],
    full_inventory_modules: frozenset[str],
    inventory_unavailable_reason: str | None,
    chosen_roots: Sequence[str],
    project_namespaces: frozenset[str],
    full_inventory_fingerprint: str | None,
    scope_fingerprint: str | None,
) -> ImportBoundaryRow:
    """Classify one normalized occurrence without consulting external state."""

    target = occurrence.target_module
    classification, unavailable_reason = _boundary_classification(
        occurrence.source_module,
        target,
        selected_modules=selected_modules,
        full_inventory_modules=full_inventory_modules,
        inventory_unavailable_reason=inventory_unavailable_reason,
        chosen_roots=chosen_roots,
        project_namespaces=project_namespaces,
    )
    return ImportBoundaryRow(
        source_module=occurrence.source_module,
        source_path=occurrence.source_path,
        target_module=target,
        site_ordinal=site_ordinal,
        line=occurrence.line,
        import_text=occurrence.import_text,
        synthetic=occurrence.synthetic,
        classification=classification,
        authority=(
            "lexical_text"
            if classification == "unavailable"
            else IMPORT_BOUNDARY_AUTHORITY
        ),
        source_fingerprint=full_inventory_fingerprint,
        scope_fingerprint=scope_fingerprint,
        unavailable_reason=unavailable_reason,
    )


def _boundary_classification(
    source: str,
    target: str,
    *,
    selected_modules: frozenset[str],
    full_inventory_modules: frozenset[str],
    inventory_unavailable_reason: str | None,
    chosen_roots: Sequence[str],
    project_namespaces: frozenset[str],
) -> tuple[str, str | None]:
    """Return one class and an unavailable reason when applicable."""

    if target in selected_modules:
        return "selected_internal", None
    if inventory_unavailable_reason is not None:
        return "unavailable", inventory_unavailable_reason
    if target in full_inventory_modules:
        return "known_inventory_boundary", None
    if import_is_inside_scope(
        source,
        target,
        chosen_roots,
        project_namespaces=project_namespaces,
    ):
        return "missing_internal", None
    return "external_boundary", None


def same_top_namespace(source: str, target: str) -> bool:
    """Return whether two modules share a plausible project namespace."""

    return bool(
        source
        and target
        and source.split(".", 1)[0] == target.split(".", 1)[0]
    )


def owned_top_namespaces(
    modules: Mapping[str, LeanModule],
    chosen_roots: Sequence[str],
) -> frozenset[str]:
    """Return discovered/configured top namespaces that the project owns."""

    names = [*modules, *chosen_roots]
    return frozenset(
        name.split(".", 1)[0]
        for name in names
        if name
    )


def import_is_inside_scope(
    source: str,
    target: str,
    chosen_roots: Sequence[str],
    *,
    project_namespaces: frozenset[str] | None = None,
) -> bool:
    """Return whether a missing import belongs to the selected review scope."""

    namespaces = project_namespaces or frozenset(
        root.split(".", 1)[0]
        for root in chosen_roots
        if root
    )
    if namespaces and target:
        return target.split(".", 1)[0] in namespaces
    return same_top_namespace(source, target)


def _import_boundary_coverage(
    *,
    visible: int,
    selected_import_coverage: CollectionCoverage | None,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
) -> CollectionCoverage:
    """Adapt selected-import observation truth to boundary-row coverage."""

    if selected_import_coverage is None:
        return _exact_import_boundary_coverage(
            visible=visible,
            authority="lexical_text",
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
        )
    if selected_import_coverage.completeness != "complete":
        return _unknown_import_boundary_coverage(
            visible=visible,
            upstream=selected_import_coverage,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
        )
    if selected_import_coverage.total == visible:
        return _exact_import_boundary_coverage(
            visible=visible,
            authority=selected_import_coverage.authority,
            source_fingerprint=(
                selected_import_coverage.source_fingerprint
                or source_fingerprint
            ),
            scope_fingerprint=(
                selected_import_coverage.scope_fingerprint
                or scope_fingerprint
            ),
            analysis_fingerprint=(
                selected_import_coverage.analysis_fingerprint
            ),
        )
    return _unstable_import_boundary_coverage(
        visible=visible,
        upstream=selected_import_coverage,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
    )


def _exact_import_boundary_coverage(
    *,
    visible: int,
    authority: str,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
    analysis_fingerprint: str | None = None,
) -> CollectionCoverage:
    """Return exact coverage for a fully observed selected import population."""

    return CollectionCoverage.exact(
        identity=IMPORT_BOUNDARY_COVERAGE,
        pointer=IMPORT_BOUNDARY_POINTER,
        visible=visible,
        total=visible,
        population="selected_lexical_import_occurrences",
        scope="selected_module_population",
        authority=authority,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )


def _unknown_import_boundary_coverage(
    *,
    visible: int,
    upstream: CollectionCoverage,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
) -> CollectionCoverage:
    """Preserve an upstream partial, unavailable, or unstable population."""

    return CollectionCoverage.unknown(
        identity=IMPORT_BOUNDARY_COVERAGE,
        pointer=IMPORT_BOUNDARY_POINTER,
        visible=visible,
        observed_lower_bound=visible,
        completeness=upstream.completeness,
        population="selected_lexical_import_occurrences",
        scope="selected_module_population",
        authority=upstream.authority,
        causes=upstream.causes,
        source_fingerprint=upstream.source_fingerprint or source_fingerprint,
        scope_fingerprint=upstream.scope_fingerprint or scope_fingerprint,
        analysis_fingerprint=upstream.analysis_fingerprint,
    )


def _unstable_import_boundary_coverage(
    *,
    visible: int,
    upstream: CollectionCoverage,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
) -> CollectionCoverage:
    """Fail closed when a supposedly exact upstream cardinality disagrees."""

    return CollectionCoverage.unknown(
        identity=IMPORT_BOUNDARY_COVERAGE,
        pointer=IMPORT_BOUNDARY_POINTER,
        visible=visible,
        observed_lower_bound=visible,
        completeness="unstable",
        population="selected_lexical_import_occurrences",
        scope="selected_module_population",
        authority=upstream.authority,
        causes=(
            CoverageCause(
                kind="drift",
                identifier="module_dag.selected_import_coverage_mismatch",
                detail=(
                    "Selected import coverage total does not match the "
                    "canonical selected import occurrences."
                ),
            ),
        ),
        source_fingerprint=upstream.source_fingerprint or source_fingerprint,
        scope_fingerprint=upstream.scope_fingerprint or scope_fingerprint,
        analysis_fingerprint=upstream.analysis_fingerprint,
    )


__all__ = [
    "IMPORT_BOUNDARY_AUTHORITY",
    "IMPORT_BOUNDARY_CLASSIFICATIONS",
    "IMPORT_BOUNDARY_COVERAGE",
    "IMPORT_BOUNDARY_NONCLAIM",
    "IMPORT_BOUNDARY_POINTER",
    "ImportBoundaryResult",
    "ImportBoundaryRow",
    "classify_import_boundaries",
    "import_is_inside_scope",
    "owned_top_namespaces",
    "same_top_namespace",
]
