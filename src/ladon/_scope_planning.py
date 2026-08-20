"""Deterministic orchestration and projection for :mod:`ladon.scope`."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from ladon._scope_resolution import (
    canonical_kind,
    direct_context,
    external_boundaries,
    index_diagnostics,
    resolve_owner_roots,
    resolve_population,
)
from ladon.changed_set import ChangedSetManifestSource
from ladon.ir import LeanModule
from ladon.scope import (
    SCOPE_FINGERPRINT_VERSION,
    ScopeDiagnostic,
    ScopePlan,
    ScopePlanningError,
    ScopeRequest,
    _EffectivePopulation,
    _Population,
)
from ladon.source_index import SourceIndex


def plan_scope(
    index: SourceIndex,
    request: ScopeRequest | None = None,
    *,
    kind: str | None = None,
    roots: Sequence[str] = (),
    navigation_roots: Sequence[str] = (),
    changed_paths: Sequence[str | Path] = (),
    changed_manifest: ChangedSetManifestSource | None = None,
    max_modules: int | None = None,
    max_context_modules: int | None = None,
    lean_batch_size: int = 8,
) -> ScopePlan:
    """Resolve one scope from indexed facts without starting external work."""

    selected = _coerce_request(
        request,
        kind=kind,
        roots=roots,
        navigation_roots=navigation_roots,
        changed_paths=changed_paths,
        changed_manifest=changed_manifest,
        max_modules=max_modules,
        max_context_modules=max_context_modules,
        lean_batch_size=lean_batch_size,
    )
    selected_kind = canonical_kind(selected.kind)
    _validate_request(selected)
    selection_roots, requested_navigation = _split_roots(
        selected_kind,
        selected,
    )
    population = resolve_population(
        selected_kind,
        index,
        selection_roots,
        selected.changed_paths,
        selected.changed_manifest,
    )
    resolved_navigation, navigation_diagnostics = (
        _resolve_navigation_roots(
            selected_kind,
            index,
            requested_navigation,
        )
    )
    population.diagnostics.extend(navigation_diagnostics)
    effective = _effective_population(index, selected, population)
    report_anchor = _report_anchor(
        selected_kind,
        population,
        effective,
    )
    fingerprint = _scope_fingerprint(
        index,
        selected_kind,
        selection_roots,
        requested_navigation,
        resolved_navigation,
        report_anchor,
        selected,
        population,
        effective,
    )
    return _scope_plan(
        index,
        selected.kind,
        selected_kind,
        selection_roots,
        requested_navigation,
        resolved_navigation,
        report_anchor,
        selected,
        population,
        effective,
        fingerprint,
    )


def plan_analysis_scope(
    index: SourceIndex,
    request: ScopeRequest,
) -> ScopePlan:
    """Explicit-request spelling for callers that persist scope inputs."""

    return plan_scope(index, request)


def _coerce_request(
    request: ScopeRequest | None,
    *,
    kind: str | None,
    roots: Sequence[str],
    navigation_roots: Sequence[str],
    changed_paths: Sequence[str | Path],
    changed_manifest: ChangedSetManifestSource | None,
    max_modules: int | None,
    max_context_modules: int | None,
    lean_batch_size: int,
) -> ScopeRequest:
    if request is not None:
        _require_no_keyword_request(
            kind=kind,
            roots=roots,
            navigation_roots=navigation_roots,
            changed_paths=changed_paths,
            changed_manifest=changed_manifest,
            max_modules=max_modules,
            max_context_modules=max_context_modules,
            lean_batch_size=lean_batch_size,
        )
        return request
    if kind is None:
        raise ScopePlanningError("scope kind is required")
    return ScopeRequest(
        kind=kind,
        roots=tuple(str(row) for row in roots),
        navigation_roots=tuple(str(row) for row in navigation_roots),
        changed_paths=tuple(str(row) for row in changed_paths),
        changed_manifest=changed_manifest,
        max_modules=max_modules,
        max_context_modules=max_context_modules,
        lean_batch_size=lean_batch_size,
    )


def _require_no_keyword_request(
    *,
    kind: str | None,
    roots: Sequence[str],
    navigation_roots: Sequence[str],
    changed_paths: Sequence[str | Path],
    changed_manifest: ChangedSetManifestSource | None,
    max_modules: int | None,
    max_context_modules: int | None,
    lean_batch_size: int,
) -> None:
    supplied_keywords = (
        kind is not None,
        bool(roots),
        bool(navigation_roots),
        bool(changed_paths),
        changed_manifest is not None,
        max_modules is not None,
        max_context_modules is not None,
        lean_batch_size != 8,
    )
    if any(supplied_keywords):
        raise ScopePlanningError(
            "pass either ScopeRequest or keyword scope inputs, not both"
        )


def _validate_request(request: ScopeRequest) -> None:
    _validate_limit(request.max_modules, "max_modules")
    _validate_limit(request.max_context_modules, "max_context_modules")
    if request.lean_batch_size <= 0:
        raise ScopePlanningError("lean_batch_size must be positive")


def _split_roots(
    kind: str,
    request: ScopeRequest,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Normalize compatibility roots into distinct selection/navigation inputs."""

    roots = tuple(sorted(set(request.roots)))
    navigation_roots = tuple(sorted(set(request.navigation_roots)))
    if kind == "inventory":
        return _inventory_roots(roots, navigation_roots)
    if navigation_roots:
        raise ScopePlanningError(
            "navigation_roots are supported only for inventory scope"
        )
    return roots, ()


def _inventory_roots(
    roots: tuple[str, ...],
    navigation_roots: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if roots and navigation_roots:
        raise ScopePlanningError(
            "pass inventory navigation roots through either roots or "
            "navigation_roots, not both"
        )
    return (), navigation_roots or roots


def _resolve_navigation_roots(
    kind: str,
    index: SourceIndex,
    requested: tuple[str, ...],
) -> tuple[tuple[str, ...], list[ScopeDiagnostic]]:
    """Resolve optional inventory navigation roots without selecting modules."""

    if kind != "inventory" or not requested:
        return (), []
    resolved, diagnostics = resolve_owner_roots(index, requested)
    return tuple(sorted(resolved)), diagnostics


def _report_anchor(
    kind: str,
    population: _Population,
    effective: _EffectivePopulation,
) -> str | None:
    """Choose a deterministic display anchor from the selected population."""

    selected = {*effective.primary, *effective.context}
    rooted = tuple(sorted(population.resolved_roots & selected))
    if kind in {"owner", "closure", "multi-root"} and rooted:
        return rooted[0]
    candidates = effective.primary or effective.context
    return candidates[0] if candidates else None


def _effective_population(
    index: SourceIndex,
    request: ScopeRequest,
    population: _Population,
) -> _EffectivePopulation:
    modules = index.modules
    diagnostics = [*index_diagnostics(index), *population.diagnostics]
    effective_primary, omitted_primary = _primary_population(
        request,
        population,
        diagnostics,
    )
    effective_context, omitted_context, context_attribution = (
        _bounded_context_population(
            request,
            population,
            set(effective_primary),
            modules,
            diagnostics,
        )
    )
    attribution = _effective_attribution(
        population,
        context_attribution,
        set(effective_primary),
        set(effective_context),
    )
    selected_modules = {*effective_primary, *effective_context}
    batches = (
        len(selected_modules) + request.lean_batch_size - 1
    ) // request.lean_batch_size
    return _EffectivePopulation(
        primary=effective_primary,
        context=effective_context,
        external=external_boundaries(selected_modules, modules),
        attribution=attribution,
        diagnostics=tuple(_stable_diagnostics(diagnostics)),
        omitted_primary=omitted_primary,
        omitted_context=omitted_context,
        helper_batches=batches,
    )


def _primary_population(
    request: ScopeRequest,
    population: _Population,
    diagnostics: list[ScopeDiagnostic],
) -> tuple[tuple[str, ...], int]:
    ordered = _ordered_primary(
        population.primary,
        population.resolved_roots,
    )
    effective, omitted = _truncate(ordered, request.max_modules)
    if omitted:
        diagnostics.append(
            _truncation_diagnostic(
                "primary",
                len(effective),
                omitted,
                "max_modules",
            )
        )
    return effective, omitted


def _bounded_context_population(
    request: ScopeRequest,
    population: _Population,
    primary: set[str],
    modules: Mapping[str, LeanModule],
    diagnostics: list[ScopeDiagnostic],
) -> tuple[tuple[str, ...], int, dict[str, set[str]]]:
    raw_context, attribution = _context_population(
        population,
        primary,
        modules,
    )
    effective, omitted = _truncate(
        tuple(sorted(raw_context - primary)),
        request.max_context_modules,
    )
    if omitted:
        diagnostics.append(
            _truncation_diagnostic(
                "context",
                len(effective),
                omitted,
                "max_context_modules",
            )
        )
    return effective, omitted, attribution


def _truncation_diagnostic(
    population: str,
    retained: int,
    omitted: int,
    option: str,
) -> ScopeDiagnostic:
    return ScopeDiagnostic(
        f"scope.{population}_truncated",
        "warning",
        (
            f"{population.title()} scope retained {retained} modules and "
            f"omitted {omitted} because of {option}."
        ),
    )


def _context_population(
    population: _Population,
    primary: set[str],
    modules: Mapping[str, LeanModule],
) -> tuple[set[str], dict[str, set[str]]]:
    if not population.include_direct_context:
        return set(), {}
    return direct_context(primary, modules, population.attribution)


def _effective_attribution(
    population: _Population,
    context_attribution: Mapping[str, set[str]],
    primary: set[str],
    context: set[str],
) -> dict[str, tuple[str, ...]]:
    attribution = {
        module: tuple(sorted(roots_for_module))
        for module, roots_for_module in population.attribution.items()
        if module in primary
    }
    attribution.update(
        {
            module: tuple(sorted(roots_for_module))
            for module, roots_for_module in context_attribution.items()
            if module in context
        }
    )
    return dict(sorted(attribution.items()))


def _scope_fingerprint(
    index: SourceIndex,
    kind: str,
    requested_selection_roots: tuple[str, ...],
    requested_navigation_roots: tuple[str, ...],
    resolved_navigation_roots: tuple[str, ...],
    report_anchor: str | None,
    request: ScopeRequest,
    population: _Population,
    effective: _EffectivePopulation,
) -> str:
    payload = {
        "fingerprintVersion": SCOPE_FINGERPRINT_VERSION,
        "sourceIndexFingerprint": index.fingerprint,
        "kind": kind,
        "selectionRoots": {
            "requested": list(requested_selection_roots),
            "resolved": sorted(population.resolved_roots),
        },
        "navigationRoots": {
            "requested": list(requested_navigation_roots),
            "resolved": list(resolved_navigation_roots),
        },
        "reportAnchor": report_anchor,
        "primary": list(effective.primary),
        "context": list(effective.context),
        "externalBoundaries": list(effective.external),
        "rootAttribution": {
            module: list(roots_for_module)
            for module, roots_for_module in effective.attribution.items()
        },
        "changedAuthority": (
            dict(population.changed_authority)
            if population.changed_authority is not None
            else None
        ),
        "limits": {
            "maxModules": request.max_modules,
            "maxContextModules": request.max_context_modules,
            "leanBatchSize": request.lean_batch_size,
        },
        "omitted": {
            "primary": effective.omitted_primary,
            "context": effective.omitted_context,
        },
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _scope_plan(
    index: SourceIndex,
    requested_kind: str,
    kind: str,
    requested_selection_roots: tuple[str, ...],
    requested_navigation_roots: tuple[str, ...],
    resolved_navigation_roots: tuple[str, ...],
    report_anchor: str | None,
    request: ScopeRequest,
    population: _Population,
    effective: _EffectivePopulation,
    fingerprint: str,
) -> ScopePlan:
    return ScopePlan(
        requested_scope=requested_kind,
        scope_kind=kind,
        requested_roots=(
            requested_navigation_roots
            if kind == "inventory"
            else requested_selection_roots
        ),
        resolved_roots=tuple(sorted(population.resolved_roots)),
        requested_selection_roots=requested_selection_roots,
        resolved_selection_roots=tuple(sorted(population.resolved_roots)),
        requested_navigation_roots=requested_navigation_roots,
        resolved_navigation_roots=resolved_navigation_roots,
        report_anchor=report_anchor,
        primary_modules=effective.primary,
        context_modules=effective.context,
        external_boundaries=effective.external,
        root_attribution=effective.attribution,
        diagnostics=effective.diagnostics,
        inventory_module_count=len(index.modules),
        omitted_primary_count=effective.omitted_primary,
        omitted_context_count=effective.omitted_context,
        truncated=bool(
            effective.omitted_primary or effective.omitted_context
        ),
        helper_batch_size=request.lean_batch_size,
        helper_batch_estimate=effective.helper_batches,
        source_index_fingerprint=index.fingerprint,
        fingerprint=fingerprint,
        inventory_boundary=tuple(dict(row) for row in index.source_roots),
        changed_authority=population.changed_authority,
    )


def _ordered_primary(
    modules: set[str],
    roots: set[str],
) -> tuple[str, ...]:
    root_modules = sorted(module for module in roots if module in modules)
    return (*root_modules, *sorted(modules - set(root_modules)))


def _truncate(
    values: tuple[str, ...],
    limit: int | None,
) -> tuple[tuple[str, ...], int]:
    if limit is None or len(values) <= limit:
        return values, 0
    return values[:limit], len(values) - limit


def _validate_limit(value: int | None, label: str) -> None:
    if value is not None and value <= 0:
        raise ScopePlanningError(f"{label} must be positive when supplied")


def _stable_diagnostics(
    diagnostics: Sequence[ScopeDiagnostic],
) -> list[ScopeDiagnostic]:
    return sorted(
        diagnostics,
        key=lambda row: (
            row.identifier,
            row.subject or "",
            row.message,
            row.severity,
        ),
    )


__all__ = ["plan_analysis_scope", "plan_scope"]
