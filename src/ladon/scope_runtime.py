"""Side-effect-free source-index and scope resolution for analysis and preview."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ladon.changed_set import ChangedSetManifestSource
from ladon.extraction import ModuleDiscovery
from ladon.scope import ScopePlan, ScopePlanningError, plan_scope
from ladon.source_index import SourceIndex, SourceIndexResult, build_source_index


@dataclass(frozen=True)
class ResolvedAnalysisScope:
    """One reusable source index, explicit plan, and selected discovery view."""

    source_index: SourceIndexResult
    scope_plan: ScopePlan
    discovery: ModuleDiscovery

    def preview_payload(
        self,
        *,
        cache_dir: Path | None,
        extraction_backend: str,
        policies: Mapping[str, Mapping[str, Any]] | None = None,
        resources: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a schema-versioned non-executing preview document."""

        cache = self.source_index.cache
        return {
            "schema": "ladon-analysis-preview-v1",
            "sourceIndex": {
                "schema": self.source_index.index.schema,
                "fingerprint": self.source_index.index.fingerprint,
                "status": self.source_index.index.index_status,
                "inventoryModules": source_index_inventory_count(
                    self.source_index.index
                ),
                "indexedModules": len(self.source_index.index.entries),
                "layoutStatus": self.source_index.index.layout_status,
                "diagnostics": [
                    dict(row) for row in self.source_index.index.diagnostics
                ],
                "cache": source_index_cache_payload(cache),
            },
            "scope": self.scope_plan.to_payload(),
            "policies": {
                name: dict(row)
                for name, row in sorted((policies or {}).items())
            },
            "resources": dict(resources or {}),
            "execution": {
                "extractionBackend": extraction_backend,
                "willRunLean": False,
                "willRunLake": False,
                "willRunVersionControl": False,
                "leanCompiledStateExpectation": (
                    "required_for_analysis"
                    if extraction_backend == "lean"
                    else "not_required"
                ),
                "cacheDirectory": (
                    str(cache_dir)
                    if cache_dir is not None
                    else (
                        str(cache.cache_path.parent)
                        if cache.cache_path is not None
                        else None
                    )
                ),
            },
        }


def resolve_analysis_scope(
    repo_root: Path,
    *,
    scope_kind: str,
    roots: Sequence[str] = (),
    navigation_roots: Sequence[str] = (),
    changed_paths: Sequence[str | Path] = (),
    changed_manifest: ChangedSetManifestSource | None = None,
    max_modules: int | None = None,
    max_context_modules: int | None = None,
    lean_batch_size: int = 8,
    cache_dir: Path | None = None,
    use_cache: bool = True,
    index_options: Mapping[str, Any] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> ResolvedAnalysisScope:
    """Build/reuse the lexical index and resolve one executable population."""

    indexed = build_source_index(
        repo_root,
        options=index_options,
        cache_dir=cache_dir,
        use_cache=use_cache,
        progress_callback=progress_callback,
    )
    requested_roots = requested_scope_roots(
        indexed.index,
        scope_kind,
        roots,
    )
    plan = plan_scope(
        indexed.index,
        kind=scope_kind,
        roots=requested_roots,
        navigation_roots=navigation_roots,
        changed_paths=changed_paths,
        changed_manifest=changed_manifest,
        max_modules=max_modules,
        max_context_modules=max_context_modules,
        lean_batch_size=lean_batch_size,
    )
    require_valid_scope(plan)
    report_anchor_module = analysis_root_name(
        indexed.index,
        plan,
        scope_kind=scope_kind,
        requested_roots=requested_roots,
    )
    discovery = discovery_from_scope(
        indexed.index,
        plan,
        analysis_root_module=report_anchor_module,
    )
    return ResolvedAnalysisScope(indexed, plan, discovery)


def requested_scope_roots(
    index: SourceIndex,
    scope_kind: str,
    roots: Sequence[str],
) -> tuple[str, ...]:
    """Normalize legacy roots or resolve the ordinary owner default.

    For inventory scope, explicit values remain accepted through this
    compatibility entry point and are normalized into navigation roots by the
    scope planner. They never select or narrow the inventory population.
    """

    requested = tuple(str(root) for root in roots)
    if requested or scope_kind not in {"owner", "closure"}:
        return requested
    return resolve_root_modules(index, (), allow_empty=False)


def require_valid_scope(plan: ScopePlan) -> None:
    """Raise one actionable error for an invalid planned population."""

    if plan.completeness != "invalid":
        return
    messages = "; ".join(
        diagnostic.message
        for diagnostic in plan.diagnostics
        if diagnostic.severity == "error"
    )
    raise ScopePlanningError(messages or "analysis scope is invalid")


def analysis_root_name(
    index: SourceIndex,
    plan: ScopePlan,
    *,
    scope_kind: str,
    requested_roots: Sequence[str],
) -> str:
    """Return the internal report anchor used by the discovery contract.

    This compatibility value selects a concrete file for extraction/output
    plumbing.  Report adaptation must derive analysis-root claims from the
    plan's resolved selection or navigation roots instead.
    """

    del index, scope_kind, requested_roots
    if plan.report_anchor is None:
        raise ScopePlanningError("analysis scope selects no root module")
    return plan.report_anchor


def resolve_root_modules(
    index: SourceIndex,
    roots: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    """Resolve explicit roots or the sole top-level module through the index."""

    selected = tuple(roots)
    if not selected and not allow_empty:
        top_level = tuple(
            module for module in index.modules if "." not in module
        )
        if len(top_level) != 1:
            raise ScopePlanningError(
                "source layout does not select one unambiguous root; pass --root"
            )
        selected = top_level
    if not selected:
        return ()
    resolution = plan_scope(index, kind="owner", roots=selected)
    errors = [
        row.message
        for row in resolution.diagnostics
        if row.severity == "error"
    ]
    if errors:
        raise ScopePlanningError("; ".join(errors))
    return resolution.resolved_roots


def discovery_from_scope(
    index: SourceIndex,
    plan: ScopePlan,
    *,
    analysis_root_module: str,
) -> ModuleDiscovery:
    """Adapt selected indexed modules to the existing backend-neutral boundary."""

    selected = set(plan.selected_modules)
    modules = {
        name: module
        for name, module in index.modules.items()
        if name in selected
    }
    if analysis_root_module not in modules:
        raise ScopePlanningError(
            "scope report anchor is outside the selected module population"
        )
    path = index.repo_root / index.paths[analysis_root_module]
    source_roots = tuple(
        str(row.get("path", ""))
        for row in index.source_roots
        if row.get("path") is not None
    )
    return ModuleDiscovery(
        repo_root=index.repo_root,
        analysis_root_file=path,
        analysis_root_module=analysis_root_module,
        inventory_root=analysis_root_module.split(".", maxsplit=1)[0],
        modules=dict(sorted(modules.items())),
        discovery_status=index.layout_status,
        diagnostics=tuple(dict(row) for row in index.diagnostics),
        source_roots=source_roots,
    )


def source_index_cache_payload(cache: Any) -> dict[str, Any]:
    """Return the stable report/preview cache-decision vocabulary."""

    return {
        "status": cache.status,
        "reason": cache.reason,
        "fingerprintVersion": cache.fingerprint_version,
        "fingerprint": cache.fingerprint,
        "path": str(cache.cache_path) if cache.cache_path is not None else None,
        "committed": cache.committed,
        "reusedEntries": cache.reused_entries,
        "rebuiltEntries": cache.rebuilt_entries,
        "failedEntries": cache.failed_entries,
    }


def source_index_inventory_count(index: SourceIndex) -> int:
    """Return manifest population, including deterministic failed source units."""

    sources = index.fingerprint_manifest.get("sources", [])
    return len(sources) if isinstance(sources, list) else len(index.entries)
