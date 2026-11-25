"""Lake-declared Lean source roots and module-to-file mapping.

Discovery reads Lake configuration without executing target code.  Declared
library ``srcDir`` values take precedence; a visible conventional fallback is
used only when no usable declaration exists.
"""

from __future__ import annotations

import os
import re
import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LEAN_LIBRARY_RE = re.compile(r"^\s*lean_lib\s+(?P<name>[A-Za-z0-9_.]+)")
SOURCE_DIR_RE = re.compile(r'\bsrcDir\s*:=\s*"(?P<path>[^"]+)"')
SOURCE_LAYOUT_CONFIG = ".ladon/source-layout.toml"
FATAL_OWNERSHIP_DIAGNOSTICS = frozenset({
    "lean.layout.ambiguous_source", "lean.layout.invalid_source_owner",
})
GENERATED_KEYS = ("generatedRoots", "generated_roots", "generatedSrcDirs")
IGNORED_SOURCE_PARTS = frozenset({".git", ".lake", ".venv", "__pycache__", "temp"})


@dataclass(frozen=True)
class LeanSourceRoot:
    """One normalized source root declared by Lake."""

    path: Path
    library: str
    origin: str
    generated: bool = False
    module_roots: tuple[str, ...] = ()

    def to_dict(self, repo_root: Path) -> dict[str, Any]:
        """Return stable report-facing root metadata."""

        return {
            "path": str(self.path.relative_to(repo_root)),
            "library": self.library,
            "origin": self.origin,
            "generated": self.generated,
            "moduleRoots": list(self.module_roots),
        }


@dataclass(frozen=True)
class LeanSourceMap:
    """Discovered module paths plus explicit authority and diagnostics."""

    modules: dict[str, Path]
    roots: tuple[LeanSourceRoot, ...]
    status: str
    diagnostics: tuple[dict[str, Any], ...] = ()
    owners: dict[str, LeanSourceRoot] = field(default_factory=dict)


def discover_lean_source_map(
    repo_root: Path, *, resolve_paths: bool = False,
) -> LeanSourceMap:
    """Prefer usable Lake declarations, otherwise expose fallback status."""

    root = repo_root.resolve()
    roots, diagnostics = declared_source_roots(root)
    if roots:
        status = "lake_declared"
    else:
        roots = (LeanSourceRoot(root, "conventional", "conventional_fallback"),)
        status = "conventional_fallback" if not diagnostics else "fallback_unsupported_lake"
        diagnostics.append({
            "id": "lean.layout.conventional_fallback",
            "severity": "warning",
            "message": (
                "No usable Lake library source roots were found; Ladon used the "
                "repository-relative conventional module layout."
            ),
        })
    return modules_from_roots(root, roots, status, diagnostics, resolve_paths=resolve_paths)


def declared_source_roots(
    repo_root: Path,
) -> tuple[tuple[LeanSourceRoot, ...], list[dict[str, Any]]]:
    """Read TOML first, then bounded ``lakefile.lean`` declarations."""

    toml_path = repo_root / "lakefile.toml"
    if toml_path.is_file():
        try:
            payload = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            return (), [layout_diagnostic(toml_path, str(exc))]
        roots = toml_source_roots(repo_root, payload, toml_path)
        if roots:
            return roots, []
        return (), [layout_diagnostic(toml_path, "no supported [[lean_lib]] entries")]
    lean_path = repo_root / "lakefile.lean"
    if lean_path.is_file():
        roots = lean_file_source_roots(repo_root, lean_path)
        if roots:
            return roots, []
        return (), [layout_diagnostic(lean_path, "no bounded lean_lib declaration found")]
    return (), []


def toml_source_roots(
    repo_root: Path,
    payload: Mapping[str, Any],
    source: Path,
) -> tuple[LeanSourceRoot, ...]:
    """Normalize Lake TOML library and generated source directories."""

    package_src = mapping_text(payload.get("package"), "srcDir") or "."
    libraries = payload.get("lean_lib", [])
    if not isinstance(libraries, list):
        return ()
    roots: list[LeanSourceRoot] = []
    for index, library in enumerate(libraries):
        if not isinstance(library, Mapping):
            continue
        name = str(library.get("name") or f"lean_lib[{index}]")
        source_dir = str(library.get("srcDir") or package_src)
        module_roots = declared_module_roots(library.get("roots"), name)
        roots.append(
            source_root(
                repo_root,
                source_dir,
                name,
                source,
                module_roots=module_roots,
            )
        )
        roots.extend(
            generated_source_roots(
                repo_root,
                library,
                name,
                source,
                module_roots=module_roots,
            )
        )
    return unique_source_roots(roots)


def declared_module_roots(value: Any, library: str) -> tuple[str, ...]:
    """Return explicit Lake roots or the library-name default."""

    if not isinstance(value, list):
        return (library,)
    roots = tuple(
        str(root)
        for root in value
        if isinstance(root, str) and root
    )
    return roots or (library,)


def mapping_text(value: Any, key: str) -> str | None:
    """Read one non-empty string from an optional mapping."""

    if not isinstance(value, Mapping):
        return None
    result = value.get(key)
    return str(result) if isinstance(result, str) and result else None


def generated_source_roots(
    repo_root: Path,
    library: Mapping[str, Any],
    name: str,
    source: Path,
    *,
    module_roots: tuple[str, ...],
) -> list[LeanSourceRoot]:
    """Read supported additive generated-root declarations."""

    values = next(
        (library.get(key) for key in GENERATED_KEYS if library.get(key) is not None),
        [],
    )
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []
    return [
        source_root(
            repo_root,
            value,
            name,
            source,
            generated=True,
            module_roots=module_roots,
        )
        for value in values
        if isinstance(value, str) and value
    ]


def lean_file_source_roots(
    repo_root: Path,
    source: Path,
) -> tuple[LeanSourceRoot, ...]:
    """Parse a conservative subset of Lake DSL ``lean_lib`` blocks."""

    lines = source.read_text(encoding="utf-8").splitlines()
    roots: list[LeanSourceRoot] = []
    for index, line in enumerate(lines):
        match = LEAN_LIBRARY_RE.match(line)
        if not match:
            continue
        indent = len(line) - len(line.lstrip())
        block = [line]
        for continuation in lines[index + 1:index + 12]:
            if continuation.strip() and not continuation.lstrip().startswith("--"):
                if len(continuation) - len(continuation.lstrip()) <= indent:
                    break
                block.append(continuation)
        body = "\n".join(block)
        src_match = SOURCE_DIR_RE.search(body)
        source_dir = src_match.group("path") if src_match else "."
        name = match.group("name")
        roots.append(
            source_root(
                repo_root,
                source_dir,
                name,
                source,
                module_roots=(name,),
            )
        )
    return unique_source_roots(roots)


def source_root(
    repo_root: Path,
    raw_path: str,
    library: str,
    source: Path,
    *,
    generated: bool = False,
    module_roots: tuple[str, ...] = (),
) -> LeanSourceRoot:
    """Resolve one declared path without permitting repository escape."""

    path = (repo_root / raw_path).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(
            f"Lake source root {raw_path!r} from {source} escapes {repo_root}"
        ) from exc
    return LeanSourceRoot(
        path,
        library,
        str(source.relative_to(repo_root)),
        generated,
        module_roots,
    )


def unique_source_roots(
    roots: Iterable[LeanSourceRoot],
) -> tuple[LeanSourceRoot, ...]:
    """Preserve declaration order while removing duplicate path/role roots."""

    unique: list[LeanSourceRoot] = []
    seen: set[tuple[Path, bool, tuple[str, ...]]] = set()
    for root in roots:
        key = (root.path, root.generated, root.module_roots)
        if key not in seen:
            unique.append(root)
            seen.add(key)
    return tuple(unique)


def modules_from_roots(
    repo_root: Path,
    roots: tuple[LeanSourceRoot, ...],
    status: str,
    diagnostics: list[dict[str, Any]],
    *, resolve_paths: bool,
) -> LeanSourceMap:
    """Resolve candidate names before producing a source inventory."""

    selections = source_owner_selections(repo_root, diagnostics)
    unused = set(selections)
    modules: dict[str, Path] = {}
    owners: dict[str, LeanSourceRoot] = {}
    for path, choices in source_candidates(roots, diagnostics, resolve_paths=resolve_paths).items():
        matches = matching_source_names(repo_root, path, selections)
        unused.difference_update(rule for rule, _ in matches)
        selected = matches[0][1] if matches else None
        name = confirmed_source_name(repo_root, path, choices, selected, diagnostics)
        if name is None:
            continue
        previous = modules.get(name)
        if previous is not None and previous != path:
            diagnostics.append(ambiguous_module_diagnostic(name, previous, path))
        else:
            modules[name] = path
            owners[name] = choices[name]
    for rule in sorted(unused):
        diagnostics.append(invalid_source_owner(
            SOURCE_LAYOUT_CONFIG, f"owner rule {rule!r} matched no source",
        ))
    return LeanSourceMap(dict(sorted(modules.items())), roots, status, tuple(diagnostics), owners)


def source_candidates(
    roots: tuple[LeanSourceRoot, ...], diagnostics: list[dict[str, Any]],
    *, resolve_paths: bool,
) -> dict[Path, dict[str, LeanSourceRoot]]:
    """Collect every discovered name under the consumer’s path identity."""

    candidates: dict[Path, dict[str, LeanSourceRoot]] = {}
    for root in roots:
        if not root.path.is_dir():
            diagnostics.append(layout_diagnostic(root.path, "declared source root is absent"))
            continue
        for path in lean_paths_under_root(root.path):
            if ignored_source_path(path, root.path):
                continue
            name = module_name_under_root(root.path, path)
            if selected_by_module_roots(name, root.module_roots):
                source = path.resolve() if resolve_paths else path
                candidates.setdefault(source, {}).setdefault(name, root)

    return candidates


def confirmed_source_name(
    repo_root: Path, path: Path, choices: Mapping[str, LeanSourceRoot],
    selected: str | None, diagnostics: list[dict[str, Any]],
) -> str | None:
    if selected is not None and selected not in choices:
        diagnostics.append(source_owner_diagnostic(
            repo_root, path, choices, selected=selected, invalid=True,
        ))
        return None
    if len(choices) > 1:
        diagnostics.append(source_owner_diagnostic(repo_root, path, choices, selected=selected))
        return selected
    return next(iter(choices))


def source_owner_selections(
    repo_root: Path, diagnostics: list[dict[str, Any]],
) -> dict[str, str]:
    """Read literal file names and module-prefix rules from project configuration."""

    path = repo_root / SOURCE_LAYOUT_CONFIG
    if not path.exists() and not path.is_symlink():
        return {}
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        diagnostics.append(invalid_source_owner(SOURCE_LAYOUT_CONFIG, str(exc)))
        return {}
    rules = payload.get("module_owners")
    if not isinstance(rules, dict) or set(payload) != {"module_owners"}:
        diagnostics.append(invalid_source_owner(
            SOURCE_LAYOUT_CONFIG, "expected a [module_owners] table",
        ))
        return {}
    result = {}
    for raw, owner in rules.items():
        if not valid_source_owner_rule(raw, owner):
            diagnostics.append(invalid_source_owner(
                SOURCE_LAYOUT_CONFIG, f"invalid owner rule {raw!r}",
            ))
        else:
            result[raw] = owner
    return result


def valid_source_owner_rule(path: str, owner: Any) -> bool:
    name = path.removesuffix("/")
    return (
        (path.endswith("/") or name.endswith(".lean"))
        and not any(part in {"", ".", ".."} for part in name.split("/"))
        and isinstance(owner, str)
        and bool(owner.strip())
    )


def matching_source_names(
    repo_root: Path, path: Path, selections: Mapping[str, str],
) -> list[tuple[str, str]]:
    """Return the file rule first, then matching directory rules deepest first."""

    if not selections or not path.is_relative_to(repo_root):
        return []
    relative = path.relative_to(repo_root)
    name = relative.as_posix()
    matches = [(name, selections[name])] if name in selections else []
    for parent in relative.parents:
        rule = f"{parent.as_posix()}/"
        if rule in selections:
            suffix = module_name_under_root(parent, relative)
            matches.append((rule, f"{selections[rule]}.{suffix}"))
    return matches


def invalid_source_owner(subject: str, reason: str) -> dict[str, Any]:
    return {
        "id": "lean.layout.invalid_source_owner",
        "severity": "error",
        "message": f"Could not use {SOURCE_LAYOUT_CONFIG}: {reason}",
        "subject": subject,
    }


def source_owner_diagnostic(
    repo_root: Path, path: Path, choices: Mapping[str, LeanSourceRoot], *,
    selected: str | None = None, invalid: bool = False,
) -> dict[str, Any]:
    subject = path.relative_to(repo_root).as_posix() if path.is_relative_to(repo_root) else str(path)
    names = sorted(choices)
    candidates = ", ".join(names)
    if invalid:
        result = invalid_source_owner(
            subject, f"{selected!r} is not a candidate for {subject}: {candidates}",
        )
    elif selected is None:
        result = {
            "id": "lean.layout.ambiguous_source",
            "severity": "error",
            "message": f"Source {subject} has competing module names: {candidates}",
            "subject": subject,
        }
    else:
        result = {
            "id": "lean.layout.source_owner_selected",
            "severity": "info",
            "message": f"Selected {selected} for {subject} from: {candidates}",
            "subject": subject,
        }
    result["candidateModules"] = names
    if selected is not None:
        result["selectedModule"] = selected
    return result


def lean_paths_under_root(source_root: Path) -> tuple[Path, ...]:
    """Return globally ordered Lean paths without entering ignored trees."""

    paths: list[Path] = []
    for directory, dirnames, filenames in os.walk(
        source_root,
        topdown=True,
        onerror=_raise_walk_error,
        followlinks=False,
    ):
        dirnames[:] = sorted(
            name for name in dirnames if name not in IGNORED_SOURCE_PARTS
        )
        parent = Path(directory)
        paths.extend(
            parent / name for name in dirnames if name.endswith(".lean")
        )
        paths.extend(
            parent / name for name in sorted(filenames) if name.endswith(".lean")
        )
    return tuple(sorted(paths))


def _raise_walk_error(error: OSError) -> None:
    """Preserve source-discovery failures instead of hiding unreadable trees."""

    raise error


def selected_by_module_roots(
    module: str,
    roots: tuple[str, ...],
) -> bool:
    """Apply Lake library roots without scanning unrelated repository trees."""

    return not roots or any(
        module == root or module.startswith(f"{root}.")
        for root in roots
    )


def ignored_source_path(path: Path, source_root: Path) -> bool:
    """Exclude build, VCS, cache, and user-temporary trees."""

    return bool(set(path.relative_to(source_root).parts) & IGNORED_SOURCE_PARTS)


def module_name_under_root(source_root: Path, path: Path) -> str:
    """Derive a Lean module from its declared source-root-relative path."""

    return ".".join(path.relative_to(source_root).with_suffix("").parts)


def root_for_path(
    path: Path,
    roots: Iterable[LeanSourceRoot],
) -> LeanSourceRoot | None:
    """Return the most-specific declared source root containing ``path``."""

    candidates = [
        root
        for root in roots
        if path == root.path or path.is_relative_to(root.path)
    ]
    return max(candidates, key=lambda root: len(root.path.parts), default=None)


def layout_diagnostic(path: Path, reason: str) -> dict[str, Any]:
    """Build one actionable unsupported-layout diagnostic."""

    return {
        "id": "lean.layout.unsupported",
        "severity": "warning",
        "message": f"Could not use Lake layout from {path}: {reason}",
        "subject": str(path),
    }


def ambiguous_module_diagnostic(
    module: str,
    first: Path,
    second: Path,
) -> dict[str, Any]:
    """Build one duplicate-module diagnostic rather than guessing ownership."""

    return {
        "id": "lean.layout.ambiguous_module",
        "severity": "error",
        "message": f"Module {module} maps to both {first} and {second}",
        "subject": module,
    }
