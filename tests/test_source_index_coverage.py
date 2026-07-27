from __future__ import annotations

from pathlib import Path

from ladon.coverage import CollectionCoverage, CoverageCause
from ladon.ir import LeanModule, LeanTextDeclaration
from ladon.source_index_models import (
    SOURCE_FAILURE_DIAGNOSTIC,
    SOURCE_INDEX_AUDITS_COVERAGE,
    SOURCE_INDEX_COMMAND_SKELETONS_COVERAGE,
    SOURCE_INDEX_DECLARATIONS_COVERAGE,
    SOURCE_INDEX_IMPORTS_COVERAGE,
    SOURCE_INDEX_MODULES_COVERAGE,
    SOURCE_INDEX_OPTIONS_COVERAGE,
    SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE,
    SOURCE_INDEX_RESOURCES_COVERAGE,
    SOURCE_INDEX_SCOPE_CONTEXTS_COVERAGE,
    SourceIndex,
    SourceIndexEntry,
)


def _declaration(name: str, line: int) -> LeanTextDeclaration:
    return LeanTextDeclaration(
        name=name,
        kind="theorem",
        line=line,
        column=1,
        start_offset=line * 10,
        end_offset=line * 10 + 8,
    )


def _entry(
    name: str,
    *,
    imports: tuple[str, ...] = (),
    declarations: tuple[LeanTextDeclaration, ...] = (),
    digest_character: str,
) -> SourceIndexEntry:
    path = f"{name.replace('.', '/')}.lean"
    module = LeanModule(
        name=name,
        path=path,
        imports=imports,
        declarations=tuple(row.name for row in declarations),
        declaration_evidence=declarations,
    )
    return SourceIndexEntry(
        module=module,
        content_sha256=digest_character * 64,
        source_bytes=100,
    )


def _manifest(entries: tuple[SourceIndexEntry, ...]) -> dict[str, object]:
    return {
        "sources": [
            {
                "module": entry.name,
                "path": entry.path,
                "status": "present",
                "bytes": entry.source_bytes,
                "sha256": entry.content_sha256,
            }
            for entry in entries
        ]
    }


def _complete_index(
    entries: tuple[SourceIndexEntry, ...],
) -> SourceIndex:
    return SourceIndex(
        repo_root=Path("/fixture"),
        fingerprint="f" * 64,
        fingerprint_manifest=_manifest(entries),
        layout_status="complete",
        source_roots=(),
        entries=entries,
        options={},
    )


def test_complete_source_index_has_exact_logical_population_coverage() -> None:
    entries = (
        _entry(
            "Pkg",
            imports=("Pkg.Core", "External.Library"),
            declarations=(_declaration("Pkg.main", 3),),
            digest_character="a",
        ),
        _entry(
            "Pkg.Core",
            declarations=(
                _declaration("Pkg.Core.first", 4),
                _declaration("Pkg.Core.second", 8),
            ),
            digest_character="b",
        ),
    )

    registry = _complete_index(entries).coverage_registry()

    modules = registry.require(SOURCE_INDEX_MODULES_COVERAGE)
    imports = registry.require(SOURCE_INDEX_IMPORTS_COVERAGE)
    declarations = registry.require(SOURCE_INDEX_DECLARATIONS_COVERAGE)
    assert tuple(registry.collections) == (
        SOURCE_INDEX_AUDITS_COVERAGE,
        SOURCE_INDEX_COMMAND_SKELETONS_COVERAGE,
        SOURCE_INDEX_DECLARATIONS_COVERAGE,
        SOURCE_INDEX_IMPORTS_COVERAGE,
        SOURCE_INDEX_MODULES_COVERAGE,
        SOURCE_INDEX_OPTIONS_COVERAGE,
        SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE,
        SOURCE_INDEX_RESOURCES_COVERAGE,
        SOURCE_INDEX_SCOPE_CONTEXTS_COVERAGE,
    )
    assert (modules.visible, modules.total, modules.omitted) == (2, 2, 0)
    assert (imports.visible, imports.total, imports.omitted) == (2, 2, 0)
    assert (
        declarations.visible,
        declarations.total,
        declarations.omitted,
    ) == (3, 3, 0)
    assert {row.pointer for row in registry.collections.values()} == {"#/entries"}
    assert {row.completeness for row in registry.collections.values()} == {"complete"}
    assert {row.source_fingerprint for row in registry.collections.values()} == {
        "f" * 64
    }


def test_complete_empty_source_index_reports_observed_empty_populations() -> None:
    registry = _complete_index(()).coverage_registry()

    for coverage in registry.collections.values():
        assert coverage.visible == 0
        assert coverage.observed_lower_bound == 0
        assert coverage.total_known is True
        assert coverage.total == 0
        assert coverage.omitted == 0
        assert coverage.completeness == "complete"
        assert coverage.causes == ()


def _partial_index() -> tuple[SourceIndex, str]:
    indexed = _entry(
        "Pkg",
        imports=("Pkg.Core",),
        declarations=(_declaration("Pkg.main", 3),),
        digest_character="a",
    )
    missing = _entry(
        "Pkg.Core",
        imports=("External.Library",),
        declarations=(_declaration("Pkg.Core.hidden", 4),),
        digest_character="b",
    )
    failure_message = (
        "Skipped Lean source module Pkg.Core at Pkg/Core.lean: "
        "parse_error (fixture parser failure)."
    )
    index = SourceIndex(
        repo_root=Path("/fixture"),
        fingerprint="f" * 64,
        fingerprint_manifest=_manifest((indexed, missing)),
        layout_status="complete",
        source_roots=(),
        entries=(indexed,),
        options={},
        index_status="partial",
        diagnostics=(
            {
                "id": SOURCE_FAILURE_DIAGNOSTIC,
                "module": "Pkg.Core",
                "path": "Pkg/Core.lean",
                "cause": "parse_error",
                "detail": "fixture parser failure",
                "message": failure_message,
            },
        ),
    )
    return index, failure_message


def _assert_unknown_dependent_coverage(
    coverage: CollectionCoverage,
    failure_message: str,
    *,
    visible: int,
) -> None:
    assert coverage.visible == visible
    assert coverage.observed_lower_bound == visible
    assert coverage.total_known is False
    assert coverage.total is None
    assert coverage.omitted is None
    assert coverage.completeness == "partial"
    _assert_failure_cause(coverage.causes, failure_message)


def _assert_failure_cause(
    causes: tuple[CoverageCause, ...],
    failure_message: str,
) -> None:
    assert len(causes) == 1
    cause = causes[0]
    assert cause.kind == "extraction"
    assert cause.identifier == SOURCE_FAILURE_DIAGNOSTIC
    assert cause.detail == failure_message


def test_partial_source_index_keeps_only_dependent_lower_bounds() -> None:
    index, failure_message = _partial_index()

    registry = index.coverage_registry()
    modules = registry.require(SOURCE_INDEX_MODULES_COVERAGE)
    assert modules.total_known is True
    assert (modules.visible, modules.total, modules.omitted) == (1, 2, 1)
    assert modules.completeness == "partial"

    for identity in (
        SOURCE_INDEX_IMPORTS_COVERAGE,
        SOURCE_INDEX_DECLARATIONS_COVERAGE,
    ):
        coverage = registry.require(identity)
        _assert_unknown_dependent_coverage(
            coverage,
            failure_message,
            visible=1,
        )
    for identity in (
        SOURCE_INDEX_OPTIONS_COVERAGE,
        SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE,
        SOURCE_INDEX_RESOURCES_COVERAGE,
        SOURCE_INDEX_SCOPE_CONTEXTS_COVERAGE,
    ):
        _assert_unknown_dependent_coverage(
            registry.require(identity),
            failure_message,
            visible=0,
        )


def test_failure_causes_are_deterministic_across_diagnostic_order() -> None:
    indexed = _entry("Pkg", digest_character="a")
    missing_a = _entry("Pkg.A", digest_character="b")
    missing_b = _entry("Pkg.B", digest_character="c")
    diagnostics = (
        {
            "id": SOURCE_FAILURE_DIAGNOSTIC,
            "module": "Pkg.B",
            "path": "Pkg/B.lean",
            "cause": "parse_error",
            "message": "Pkg.B failed",
        },
        {
            "id": SOURCE_FAILURE_DIAGNOSTIC,
            "module": "Pkg.A",
            "path": "Pkg/A.lean",
            "cause": "read_error",
            "message": "Pkg.A failed",
        },
    )

    def registry_for(
        rows: tuple[dict[str, str], ...],
    ) -> dict[str, object]:
        index = SourceIndex(
            repo_root=Path("/fixture"),
            fingerprint="f" * 64,
            fingerprint_manifest=_manifest((indexed, missing_a, missing_b)),
            layout_status="complete",
            source_roots=(),
            entries=(indexed,),
            options={},
            index_status="partial",
            diagnostics=rows,
        )
        return index.coverage_registry().to_dict()

    assert registry_for(diagnostics) == registry_for(tuple(reversed(diagnostics)))
