"""Pure analysis-scope planning over a reusable Ladon source index.

Planning is intentionally non-executing: it projects already indexed source
facts and may read an explicitly supplied changed-set manifest, but never
invokes Lake, Lean, Git, target code, or an analysis pass.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from ladon.changed_set import (
    CHANGED_SET_MANIFEST_SCHEMA,
    read_changed_set_manifest,
)
from ladon.ir import LeanModule
from ladon.source_index import SourceIndex


SCOPE_PLAN_SCHEMA = "ladon-scope-plan-v1"
SCOPE_FINGERPRINT_VERSION = "ladon-scope-fingerprint-v1"
SUPPORTED_SCOPE_KINDS = frozenset(
    {"owner", "closure", "namespace", "multi-root", "changed-set", "inventory"}
)
SCOPE_ALIASES = {
    "import-closure": "closure",
    "import_closure": "closure",
    "multi_root": "multi-root",
    "changed_set": "changed-set",
    "full-inventory": "inventory",
    "full_inventory": "inventory",
}


class ScopePlanningError(ValueError):
    """Raised for malformed scope requests rather than repository findings."""


@dataclass(frozen=True)
class ScopeDiagnostic:
    """One stable scope-resolution or truncation diagnostic."""

    identifier: str
    severity: str
    message: str
    subject: str | None = None

    def to_payload(self) -> dict[str, Any]:
        """Return a stable JSON-compatible diagnostic."""

        payload: dict[str, Any] = {
            "id": self.identifier,
            "severity": self.severity,
            "message": self.message,
        }
        if self.subject is not None:
            payload["subject"] = self.subject
        return payload


@dataclass(frozen=True)
class ScopeRequest:
    """Caller-supplied inputs for one deterministic scope plan."""

    kind: str
    roots: tuple[str, ...] = ()
    changed_paths: tuple[str, ...] = ()
    changed_manifest: str | Path | Mapping[str, Any] | None = None
    max_modules: int | None = None
    max_context_modules: int | None = None
    lean_batch_size: int = 8


@dataclass(frozen=True)
class ScopePlan:
    """Resolved primary/context populations without executing analysis."""

    requested_scope: str
    scope_kind: str
    requested_roots: tuple[str, ...]
    resolved_roots: tuple[str, ...]
    primary_modules: tuple[str, ...]
    context_modules: tuple[str, ...]
    external_boundaries: tuple[str, ...]
    root_attribution: Mapping[str, tuple[str, ...]]
    diagnostics: tuple[ScopeDiagnostic, ...]
    inventory_module_count: int
    omitted_primary_count: int
    omitted_context_count: int
    truncated: bool
    helper_batch_size: int
    helper_batch_estimate: int
    source_index_fingerprint: str
    fingerprint: str
    inventory_boundary: tuple[Mapping[str, Any], ...]
    changed_authority: Mapping[str, Any] | None = None
    schema: str = SCOPE_PLAN_SCHEMA

    @property
    def selected_modules(self) -> tuple[str, ...]:
        """Return the deduplicated effective helper population."""

        return tuple(sorted({*self.primary_modules, *self.context_modules}))

    @property
    def completeness(self) -> str:
        """Classify whether the requested population is usable and complete."""

        if any(row.severity == "error" for row in self.diagnostics):
            return "invalid"
        return "truncated" if self.truncated else "complete"

    def to_payload(self) -> dict[str, Any]:
        """Return the machine-readable, schema-versioned preview."""

        return {
            "schema": self.schema,
            "scopeFingerprintVersion": SCOPE_FINGERPRINT_VERSION,
            "fingerprint": self.fingerprint,
            "sourceIndexFingerprint": self.source_index_fingerprint,
            "requestedScope": self.requested_scope,
            "effectiveScope": self.scope_kind,
            "requestedRoots": list(self.requested_roots),
            "resolvedRoots": list(self.resolved_roots),
            "primaryPopulation": {
                "modules": list(self.primary_modules),
                "selectedCount": len(self.primary_modules),
                "omittedCount": self.omitted_primary_count,
            },
            "contextPopulation": {
                "modules": list(self.context_modules),
                "selectedCount": len(self.context_modules),
                "omittedCount": self.omitted_context_count,
                "authority": "local_import_context",
            },
            "externalBoundaries": list(self.external_boundaries),
            "rootAttribution": {
                module: list(roots)
                for module, roots in sorted(self.root_attribution.items())
            },
            "inventoryBoundary": {
                "moduleCount": self.inventory_module_count,
                "omittedCount": (
                    self.inventory_module_count - len(self.selected_modules)
                ),
                "sourceRoots": [dict(row) for row in self.inventory_boundary],
            },
            "truncated": self.truncated,
            "completeness": self.completeness,
            "leanHelperPlan": {
                "batchSize": self.helper_batch_size,
                "selectedModules": len(self.selected_modules),
                "expectedBatches": self.helper_batch_estimate,
            },
            "changedAuthority": (
                dict(self.changed_authority)
                if self.changed_authority is not None
                else None
            ),
            "diagnostics": [row.to_payload() for row in self.diagnostics],
            "nonclaim": (
                "Scope planning is review routing, not a claim that a selected "
                "module is the mathematically correct proof root."
            ),
        }


@dataclass
class _Population:
    primary: set[str] = field(default_factory=set)
    attribution: dict[str, set[str]] = field(default_factory=dict)
    resolved_roots: set[str] = field(default_factory=set)
    diagnostics: list[ScopeDiagnostic] = field(default_factory=list)
    changed_authority: Mapping[str, Any] | None = None
    include_direct_context: bool = False


@dataclass(frozen=True)
class _EffectivePopulation:
    primary: tuple[str, ...]
    context: tuple[str, ...]
    external: tuple[str, ...]
    attribution: Mapping[str, tuple[str, ...]]
    diagnostics: tuple[ScopeDiagnostic, ...]
    omitted_primary: int
    omitted_context: int
    helper_batches: int


def plan_scope(
    index: SourceIndex,
    request: ScopeRequest | None = None,
    *,
    kind: str | None = None,
    roots: Sequence[str] = (),
    changed_paths: Sequence[str | Path] = (),
    changed_manifest: str | Path | Mapping[str, Any] | None = None,
    max_modules: int | None = None,
    max_context_modules: int | None = None,
    lean_batch_size: int = 8,
) -> ScopePlan:
    """Resolve one scope from indexed facts without starting external work."""

    selected = _coerce_request(
        request,
        kind=kind,
        roots=roots,
        changed_paths=changed_paths,
        changed_manifest=changed_manifest,
        max_modules=max_modules,
        max_context_modules=max_context_modules,
        lean_batch_size=lean_batch_size,
    )
    canonical_kind = _canonical_kind(selected.kind)
    _validate_request(selected)
    requested_roots = tuple(sorted(set(selected.roots)))
    population = _resolve_population(
        canonical_kind,
        index,
        requested_roots,
        selected.changed_paths,
        selected.changed_manifest,
    )
    effective = _effective_population(index, selected, population)
    fingerprint = _scope_fingerprint(
        index,
        canonical_kind,
        requested_roots,
        selected,
        population,
        effective,
    )
    return _scope_plan(
        index,
        selected.kind,
        canonical_kind,
        requested_roots,
        selected,
        population,
        effective,
        fingerprint,
    )


def _coerce_request(
    request: ScopeRequest | None,
    *,
    kind: str | None,
    roots: Sequence[str],
    changed_paths: Sequence[str | Path],
    changed_manifest: str | Path | Mapping[str, Any] | None,
    max_modules: int | None,
    max_context_modules: int | None,
    lean_batch_size: int,
) -> ScopeRequest:
    if request is not None:
        supplied_keywords = (
            kind is not None,
            bool(roots),
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
        return request
    if kind is None:
        raise ScopePlanningError("scope kind is required")
    return ScopeRequest(
        kind=kind,
        roots=tuple(str(row) for row in roots),
        changed_paths=tuple(str(row) for row in changed_paths),
        changed_manifest=changed_manifest,
        max_modules=max_modules,
        max_context_modules=max_context_modules,
        lean_batch_size=lean_batch_size,
    )


def _validate_request(request: ScopeRequest) -> None:
    _validate_limit(request.max_modules, "max_modules")
    _validate_limit(request.max_context_modules, "max_context_modules")
    if request.lean_batch_size <= 0:
        raise ScopePlanningError("lean_batch_size must be positive")


def _effective_population(
    index: SourceIndex,
    request: ScopeRequest,
    population: _Population,
) -> _EffectivePopulation:
    modules = index.modules
    diagnostics = [*_index_diagnostics(index), *population.diagnostics]
    ordered_primary = _ordered_primary(
        population.primary,
        population.resolved_roots,
    )
    effective_primary, omitted_primary = _truncate(
        ordered_primary,
        request.max_modules,
    )
    if omitted_primary:
        diagnostics.append(_truncation_diagnostic(
            "primary",
            len(effective_primary),
            omitted_primary,
            "max_modules",
        ))
    raw_context, context_attribution = _context_population(
        population,
        set(effective_primary),
        modules,
    )
    effective_context, omitted_context = _truncate(
        tuple(sorted(raw_context - set(effective_primary))),
        request.max_context_modules,
    )
    if omitted_context:
        diagnostics.append(_truncation_diagnostic(
            "context",
            len(effective_context),
            omitted_context,
            "max_context_modules",
        ))
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
        external=_external_boundaries(selected_modules, modules),
        attribution=attribution,
        diagnostics=tuple(_stable_diagnostics(diagnostics)),
        omitted_primary=omitted_primary,
        omitted_context=omitted_context,
        helper_batches=batches,
    )


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
    return _direct_context(primary, modules, population.attribution)


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
    requested_roots: tuple[str, ...],
    request: ScopeRequest,
    population: _Population,
    effective: _EffectivePopulation,
) -> str:
    payload = {
        "fingerprintVersion": SCOPE_FINGERPRINT_VERSION,
        "sourceIndexFingerprint": index.fingerprint,
        "kind": kind,
        "requestedRoots": list(requested_roots),
        "resolvedRoots": sorted(population.resolved_roots),
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
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def _scope_plan(
    index: SourceIndex,
    requested_kind: str,
    kind: str,
    requested_roots: tuple[str, ...],
    request: ScopeRequest,
    population: _Population,
    effective: _EffectivePopulation,
    fingerprint: str,
) -> ScopePlan:
    return ScopePlan(
        requested_scope=requested_kind,
        scope_kind=kind,
        requested_roots=requested_roots,
        resolved_roots=tuple(sorted(population.resolved_roots)),
        primary_modules=effective.primary,
        context_modules=effective.context,
        external_boundaries=effective.external,
        root_attribution=effective.attribution,
        diagnostics=effective.diagnostics,
        inventory_module_count=len(index.modules),
        omitted_primary_count=effective.omitted_primary,
        omitted_context_count=effective.omitted_context,
        truncated=bool(effective.omitted_primary or effective.omitted_context),
        helper_batch_size=request.lean_batch_size,
        helper_batch_estimate=effective.helper_batches,
        source_index_fingerprint=index.fingerprint,
        fingerprint=fingerprint,
        inventory_boundary=tuple(dict(row) for row in index.source_roots),
        changed_authority=population.changed_authority,
    )


def plan_analysis_scope(
    index: SourceIndex,
    request: ScopeRequest,
) -> ScopePlan:
    """Explicit-request spelling for callers that persist scope inputs."""

    return plan_scope(index, request)


def _resolve_population(
    kind: str,
    index: SourceIndex,
    roots: tuple[str, ...],
    changed_paths: tuple[str, ...],
    changed_manifest: str | Path | Mapping[str, Any] | None,
) -> _Population:
    if kind == "inventory":
        return _inventory_population(index, roots)
    if kind == "changed-set":
        return _changed_population(index, changed_paths, changed_manifest)
    if not roots:
        return _missing_root_population(kind)
    if kind == "namespace":
        return _namespace_population(index, roots)
    return _rooted_population(kind, index, roots)


def _inventory_population(
    index: SourceIndex,
    roots: tuple[str, ...],
) -> _Population:
    result = _Population(primary=set(index.modules))
    result.attribution = {
        module: {"inventory"}
        for module in result.primary
    }
    if roots:
        result.diagnostics.append(
            ScopeDiagnostic(
                "scope.inventory_roots_ignored",
                "warning",
                "Inventory scope selects every indexed module; roots are ignored.",
            )
        )
    return result


def _missing_root_population(kind: str) -> _Population:
    return _Population(
        diagnostics=[
            ScopeDiagnostic(
                "scope.root_required",
                "error",
                f"{kind} scope requires at least one explicit root.",
            )
        ]
    )


def _rooted_population(
    kind: str,
    index: SourceIndex,
    roots: tuple[str, ...],
) -> _Population:
    resolved, diagnostics = _resolve_owner_roots(index, roots)
    result = _Population(
        resolved_roots=set(resolved),
        diagnostics=diagnostics,
    )
    if kind == "owner":
        return _owner_population(result, resolved)
    if kind == "multi-root" and len(resolved) < 2:
        result.diagnostics.append(
            ScopeDiagnostic(
                "scope.multi_root_requires_two",
                "error",
                "Multi-root scope requires at least two resolved roots.",
            )
        )
    return _closure_population(result, resolved, index.modules)


def _owner_population(
    result: _Population,
    resolved: set[str],
) -> _Population:
    result.primary.update(resolved)
    result.include_direct_context = True
    result.attribution = {
        module: {module}
        for module in resolved
    }
    return result


def _closure_population(
    result: _Population,
    resolved: set[str],
    modules: Mapping[str, LeanModule],
) -> _Population:
    for root in resolved:
        closure = _local_closure(root, modules)
        result.primary.update(closure)
        for module in closure:
            result.attribution.setdefault(module, set()).add(root)
    return result


def _resolve_owner_roots(
    index: SourceIndex,
    roots: Sequence[str],
) -> tuple[set[str], list[ScopeDiagnostic]]:
    modules = index.modules
    path_to_module = {entry.path: entry.name for entry in index.entries}
    resolved: set[str] = set()
    diagnostics: list[ScopeDiagnostic] = []
    for raw in roots:
        if raw in modules:
            resolved.add(raw)
            continue
        normalized = _normalize_relative_path(raw)
        if normalized is not None and normalized in path_to_module:
            resolved.add(path_to_module[normalized])
            continue
        candidates = _path_prefix_modules(index, normalized) if normalized else ()
        if len(candidates) == 1:
            resolved.add(candidates[0])
            continue
        if len(candidates) > 1:
            diagnostics.append(
                ScopeDiagnostic(
                    "scope.root_ambiguous",
                    "error",
                    f"Root {raw!r} maps to more than one indexed module.",
                    raw,
                )
            )
        else:
            diagnostics.append(
                ScopeDiagnostic(
                    "scope.root_unresolved",
                    "error",
                    f"Root {raw!r} does not resolve through the source index.",
                    raw,
                )
            )
    return resolved, diagnostics


def _namespace_population(
    index: SourceIndex,
    roots: Sequence[str],
) -> _Population:
    modules = index.modules
    result = _Population(include_direct_context=True)
    for raw in roots:
        matches = {
            module
            for module in modules
            if module == raw or module.startswith(f"{raw}.")
        }
        if matches:
            result.resolved_roots.add(raw)
        else:
            normalized = _normalize_relative_path(raw)
            matches = set(_path_prefix_modules(index, normalized))
            if matches:
                result.resolved_roots.add(_namespace_label(matches))
        if not matches:
            result.diagnostics.append(
                ScopeDiagnostic(
                    "scope.namespace_unresolved",
                    "error",
                    (
                        f"Namespace or source directory {raw!r} selects no "
                        "indexed modules."
                    ),
                    raw,
                )
            )
            continue
        result.primary.update(matches)
        for module in matches:
            result.attribution.setdefault(module, set()).add(raw)
    return result


def _changed_population(
    index: SourceIndex,
    changed_paths: Sequence[str],
    changed_manifest: str | Path | Mapping[str, Any] | None,
) -> _Population:
    paths = list(changed_paths)
    authority: dict[str, Any] = {
        "kind": "caller_paths",
        "manifestSchema": None,
        "manifestSha256": None,
    }
    diagnostics: list[ScopeDiagnostic] = []
    if changed_manifest is not None:
        manifest_paths, manifest_authority, manifest_diagnostics = (
            _read_changed_manifest(changed_manifest)
        )
        paths.extend(manifest_paths)
        authority = manifest_authority
        diagnostics.extend(manifest_diagnostics)
        if changed_paths:
            authority = {
                **authority,
                "kind": "caller_paths_and_manifest",
                "additionalPathCount": len(changed_paths),
            }
    normalized_paths: set[str] = set()
    for raw in paths:
        normalized = _normalize_relative_path(str(raw))
        if normalized is None:
            diagnostics.append(
                ScopeDiagnostic(
                    "scope.changed_path_invalid",
                    "error",
                    "Changed-set paths must be repository-relative and cannot escape.",
                    str(raw),
                )
            )
        else:
            normalized_paths.add(normalized)
    path_to_module = {entry.path: entry.name for entry in index.entries}
    result = _Population(
        diagnostics=diagnostics,
        changed_authority={
            **authority,
            "paths": sorted(normalized_paths),
        },
        include_direct_context=True,
    )
    for path in sorted(normalized_paths):
        module = path_to_module.get(path)
        if module is None:
            result.diagnostics.append(
                ScopeDiagnostic(
                    "scope.changed_path_unmapped",
                    "warning",
                    f"Changed path {path!r} does not map to an indexed Lean module.",
                    path,
                )
            )
            continue
        result.primary.add(module)
        result.resolved_roots.add(module)
        result.attribution.setdefault(module, set()).add(module)
    if not paths:
        result.diagnostics.append(
            ScopeDiagnostic(
                "scope.changed_set_empty",
                "error",
                "Changed-set scope requires caller paths or a versioned manifest.",
            )
        )
    return result


def _read_changed_manifest(
    source: str | Path | Mapping[str, Any],
) -> tuple[list[str], dict[str, Any], list[ScopeDiagnostic]]:
    manifest = read_changed_set_manifest(source)
    diagnostics = [
        ScopeDiagnostic(
            str(row.get("id", "scope.changed_manifest_invalid")),
            str(row.get("severity", "error")),
            str(row.get("message", "Changed-set manifest is invalid.")),
            str(row["subject"]) if row.get("subject") is not None else None,
        )
        for row in manifest.diagnostics
    ]
    return list(manifest.paths), dict(manifest.authority), diagnostics


def _local_closure(
    root: str,
    modules: Mapping[str, LeanModule],
) -> set[str]:
    visited: set[str] = set()
    pending = [root]
    while pending:
        current = pending.pop()
        if current in visited or current not in modules:
            continue
        visited.add(current)
        pending.extend(
            sorted(
                (
                    imported
                    for imported in modules[current].imports
                    if imported in modules
                ),
                reverse=True,
            )
        )
    return visited


def _direct_context(
    primary: set[str],
    modules: Mapping[str, LeanModule],
    attribution: Mapping[str, set[str]],
) -> tuple[set[str], dict[str, set[str]]]:
    context: set[str] = set()
    context_attribution: dict[str, set[str]] = {}
    for module in sorted(primary):
        owner_roots = attribution.get(module, {module})
        for imported in modules[module].imports:
            if imported not in modules or imported in primary:
                continue
            context.add(imported)
            context_attribution.setdefault(imported, set()).update(owner_roots)
    return context, context_attribution


def _external_boundaries(
    selected: set[str],
    modules: Mapping[str, LeanModule],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                imported
                for module in selected
                for imported in modules[module].imports
                if imported not in modules
            }
        )
    )


def _path_prefix_modules(
    index: SourceIndex,
    normalized: str | None,
) -> tuple[str, ...]:
    if normalized is None:
        return ()
    prefix = normalized.rstrip("/")
    lean_prefix = prefix.removesuffix(".lean")
    matches = {
        entry.name
        for entry in index.entries
        if entry.path == normalized
        or entry.path.startswith(f"{prefix}/")
        or entry.path.removesuffix(".lean") == lean_prefix
        or entry.path.removesuffix(".lean").startswith(f"{lean_prefix}/")
    }
    return tuple(sorted(matches))


def _namespace_label(modules: set[str]) -> str:
    split = [module.split(".") for module in sorted(modules)]
    common: list[str] = []
    for segments in zip(*split):
        if len(set(segments)) != 1:
            break
        common.append(segments[0])
    return ".".join(common) if common else sorted(modules)[0]


def _normalize_relative_path(raw: str) -> str | None:
    value = raw.replace("\\", "/")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        return None
    normalized = str(path)
    return None if normalized in {"", "."} else normalized


def _ordered_primary(
    modules: set[str],
    roots: set[str],
) -> tuple[str, ...]:
    root_modules = sorted(module for module in roots if module in modules)
    return tuple([*root_modules, *sorted(modules - set(root_modules))])


def _truncate(
    values: tuple[str, ...],
    limit: int | None,
) -> tuple[tuple[str, ...], int]:
    if limit is None or len(values) <= limit:
        return values, 0
    return values[:limit], len(values) - limit


def _canonical_kind(raw: str) -> str:
    kind = SCOPE_ALIASES.get(raw, raw)
    if kind not in SUPPORTED_SCOPE_KINDS:
        raise ScopePlanningError(
            f"unsupported scope kind {raw!r}; expected "
            + ", ".join(sorted(SUPPORTED_SCOPE_KINDS))
        )
    return kind


def _validate_limit(value: int | None, label: str) -> None:
    if value is not None and value <= 0:
        raise ScopePlanningError(f"{label} must be positive when supplied")


def _index_diagnostics(index: SourceIndex) -> list[ScopeDiagnostic]:
    return [
        ScopeDiagnostic(
            str(row.get("id", "scope.layout")),
            str(row.get("severity", "warning")),
            str(row.get("message", "Source-index layout diagnostic.")),
            str(row["subject"]) if row.get("subject") is not None else None,
        )
        for row in index.diagnostics
    ]


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
