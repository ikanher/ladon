"""Population resolution and graph helpers for :mod:`ladon.scope`."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath
from typing import Any

from ladon.changed_set import (
    ChangedSetManifestSource,
    read_changed_set_manifest,
)
from ladon.ir import LeanModule
from ladon.scope import (
    SCOPE_ALIASES,
    SUPPORTED_SCOPE_KINDS,
    ScopeDiagnostic,
    ScopePlanningError,
    _Population,
)
from ladon.source_index import SourceIndex


def resolve_population(
    kind: str,
    index: SourceIndex,
    roots: tuple[str, ...],
    changed_paths: tuple[str, ...],
    changed_manifest: ChangedSetManifestSource | None,
) -> _Population:
    """Resolve the primary population for one canonical scope kind."""

    if kind == "inventory":
        return _inventory_population(index)
    if kind == "changed-set":
        return _changed_population(index, changed_paths, changed_manifest)
    if not roots:
        return _missing_root_population(kind)
    if kind == "namespace":
        return _namespace_population(index, roots)
    return _rooted_population(kind, index, roots)


def resolve_owner_roots(
    index: SourceIndex,
    roots: Sequence[str],
) -> tuple[set[str], list[ScopeDiagnostic]]:
    """Resolve module names and repository-relative paths through the index."""

    modules = index.modules
    path_to_module = {entry.path: entry.name for entry in index.entries}
    resolved: set[str] = set()
    diagnostics: list[ScopeDiagnostic] = []
    for raw in roots:
        matched = _resolved_root(
            index,
            raw,
            modules=modules,
            path_to_module=path_to_module,
        )
        if isinstance(matched, str):
            resolved.add(matched)
        else:
            diagnostics.append(matched)
    return resolved, diagnostics


def direct_context(
    primary: set[str],
    modules: Mapping[str, LeanModule],
    attribution: Mapping[str, set[str]],
) -> tuple[set[str], dict[str, set[str]]]:
    """Return direct internal imports outside the primary population."""

    context: set[str] = set()
    context_attribution: dict[str, set[str]] = {}
    for module in sorted(primary):
        owner_roots = attribution.get(module, {module})
        for imported in modules[module].imports:
            if imported not in modules or imported in primary:
                continue
            context.add(imported)
            context_attribution.setdefault(imported, set()).update(
                owner_roots
            )
    return context, context_attribution


def external_boundaries(
    selected: set[str],
    modules: Mapping[str, LeanModule],
) -> tuple[str, ...]:
    """Return imports whose targets are outside the indexed inventory."""

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


def canonical_kind(raw: str) -> str:
    """Normalize one supported scope alias."""

    kind = SCOPE_ALIASES.get(raw, raw)
    if kind not in SUPPORTED_SCOPE_KINDS:
        raise ScopePlanningError(
            f"unsupported scope kind {raw!r}; expected "
            + ", ".join(sorted(SUPPORTED_SCOPE_KINDS))
        )
    return kind


def index_diagnostics(index: SourceIndex) -> list[ScopeDiagnostic]:
    """Adapt source-index diagnostics to stable scope diagnostics."""

    return [
        ScopeDiagnostic(
            str(row.get("id", "scope.layout")),
            str(row.get("severity", "warning")),
            str(row.get("message", "Source-index layout diagnostic.")),
            str(row["subject"]) if row.get("subject") is not None else None,
        )
        for row in index.diagnostics
    ]


def _inventory_population(index: SourceIndex) -> _Population:
    result = _Population(primary=set(index.modules))
    result.attribution = {
        module: {"inventory"}
        for module in result.primary
    }
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
    resolved, diagnostics = resolve_owner_roots(index, roots)
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


def _resolved_root(
    index: SourceIndex,
    raw: str,
    *,
    modules: Mapping[str, LeanModule],
    path_to_module: Mapping[str, str],
) -> str | ScopeDiagnostic:
    if raw in modules:
        return raw
    normalized = _normalize_relative_path(raw)
    if normalized is not None and normalized in path_to_module:
        return path_to_module[normalized]
    candidates = _path_prefix_modules(index, normalized)
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        return ScopeDiagnostic(
            "scope.root_ambiguous",
            "error",
            f"Root {raw!r} maps to more than one indexed module.",
            raw,
        )
    return ScopeDiagnostic(
        "scope.root_unresolved",
        "error",
        f"Root {raw!r} does not resolve through the source index.",
        raw,
    )


def _namespace_population(
    index: SourceIndex,
    roots: Sequence[str],
) -> _Population:
    result = _Population(include_direct_context=True)
    for raw in roots:
        matches, resolved_label = _namespace_matches(index, raw)
        if resolved_label is not None:
            result.resolved_roots.add(resolved_label)
        if not matches:
            result.diagnostics.append(_namespace_diagnostic(raw))
            continue
        result.primary.update(matches)
        for module in matches:
            result.attribution.setdefault(module, set()).add(raw)
    return result


def _namespace_matches(
    index: SourceIndex,
    raw: str,
) -> tuple[set[str], str | None]:
    matches = {
        module
        for module in index.modules
        if module == raw or module.startswith(f"{raw}.")
    }
    if matches:
        return matches, raw
    normalized = _normalize_relative_path(raw)
    matches = set(_path_prefix_modules(index, normalized))
    return matches, _namespace_label(matches) if matches else None


def _namespace_diagnostic(raw: str) -> ScopeDiagnostic:
    return ScopeDiagnostic(
        "scope.namespace_unresolved",
        "error",
        (
            f"Namespace or source directory {raw!r} selects no "
            "indexed modules."
        ),
        raw,
    )


def _changed_population(
    index: SourceIndex,
    changed_paths: Sequence[str],
    changed_manifest: ChangedSetManifestSource | None,
) -> _Population:
    paths, authority, diagnostics = _changed_inputs(
        changed_paths,
        changed_manifest,
    )
    normalized_paths, path_diagnostics = _normalized_changed_paths(paths)
    diagnostics.extend(path_diagnostics)
    result = _Population(
        diagnostics=diagnostics,
        changed_authority={
            **authority,
            "paths": sorted(normalized_paths),
        },
        include_direct_context=True,
    )
    _attach_changed_modules(index, normalized_paths, result)
    if not paths:
        result.diagnostics.append(
            ScopeDiagnostic(
                "scope.changed_set_empty",
                "error",
                "Changed-set scope requires caller paths or a versioned manifest.",
            )
        )
    return result


def _changed_inputs(
    changed_paths: Sequence[str],
    changed_manifest: ChangedSetManifestSource | None,
) -> tuple[list[str], dict[str, Any], list[ScopeDiagnostic]]:
    paths = list(changed_paths)
    authority: dict[str, Any] = {
        "kind": "caller_paths",
        "manifestSchema": None,
        "manifestSha256": None,
    }
    diagnostics: list[ScopeDiagnostic] = []
    if changed_manifest is None:
        return paths, authority, diagnostics
    manifest_paths, authority, diagnostics = _read_changed_manifest(
        changed_manifest
    )
    paths.extend(manifest_paths)
    if changed_paths:
        authority = {
            **authority,
            "kind": "caller_paths_and_manifest",
            "additionalPathCount": len(changed_paths),
        }
    return paths, authority, diagnostics


def _normalized_changed_paths(
    paths: Sequence[str],
) -> tuple[set[str], list[ScopeDiagnostic]]:
    normalized_paths: set[str] = set()
    diagnostics: list[ScopeDiagnostic] = []
    for raw in paths:
        normalized = _normalize_relative_path(str(raw))
        if normalized is None:
            diagnostics.append(
                ScopeDiagnostic(
                    "scope.changed_path_invalid",
                    "error",
                    (
                        "Changed-set paths must be repository-relative "
                        "and cannot escape."
                    ),
                    str(raw),
                )
            )
        else:
            normalized_paths.add(normalized)
    return normalized_paths, diagnostics


def _attach_changed_modules(
    index: SourceIndex,
    normalized_paths: set[str],
    result: _Population,
) -> None:
    path_to_module = {entry.path: entry.name for entry in index.entries}
    for path in sorted(normalized_paths):
        module = path_to_module.get(path)
        if module is None:
            result.diagnostics.append(
                ScopeDiagnostic(
                    "scope.changed_path_unmapped",
                    "warning",
                    (
                        f"Changed path {path!r} does not map to an "
                        "indexed Lean module."
                    ),
                    path,
                )
            )
            continue
        result.primary.add(module)
        result.resolved_roots.add(module)
        result.attribution.setdefault(module, set()).add(module)


def _read_changed_manifest(
    source: ChangedSetManifestSource,
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
    return ".".join(common) if common else min(modules)


def _normalize_relative_path(raw: str) -> str | None:
    value = raw.replace("\\", "/")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        return None
    normalized = str(path)
    return None if normalized in {"", "."} else normalized


__all__ = [
    "canonical_kind",
    "direct_context",
    "external_boundaries",
    "index_diagnostics",
    "resolve_owner_roots",
    "resolve_population",
]
