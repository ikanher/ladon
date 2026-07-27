"""Lake-declared Lean source roots and module-to-file mapping.

Discovery reads Lake configuration without executing target code.  Declared
library ``srcDir`` values take precedence; a visible conventional fallback is
used only when no usable declaration exists.
"""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


LEAN_LIBRARY_RE = re.compile(r"^\s*lean_lib\s+(?P<name>[A-Za-z0-9_.]+)")
SOURCE_DIR_RE = re.compile(r'\bsrcDir\s*:=\s*"(?P<path>[^"]+)"')
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


def discover_lean_source_map(repo_root: Path) -> LeanSourceMap:
    """Prefer usable Lake declarations, otherwise expose fallback status."""

    root = repo_root.resolve()
    roots, diagnostics = declared_source_roots(root)
    if roots:
        modules, mapping_diagnostics = modules_from_roots(root, roots)
        return LeanSourceMap(
            modules,
            roots,
            "lake_declared",
            tuple([*diagnostics, *mapping_diagnostics]),
        )
    fallback = LeanSourceRoot(root, "conventional", "conventional_fallback")
    modules, mapping_diagnostics = modules_from_roots(root, (fallback,))
    status = "conventional_fallback" if not diagnostics else "fallback_unsupported_lake"
    fallback_diagnostic = {
        "id": "lean.layout.conventional_fallback",
        "severity": "warning",
        "message": (
            "No usable Lake library source roots were found; Ladon used the "
            "repository-relative conventional module layout."
        ),
    }
    return LeanSourceMap(
        modules,
        (fallback,),
        status,
        tuple([*diagnostics, fallback_diagnostic, *mapping_diagnostics]),
    )


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
        body = "\n".join(lines[index:index + 12])
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
    roots: Iterable[LeanSourceRoot],
) -> tuple[dict[str, Path], list[dict[str, Any]]]:
    """Scan declared roots and reject ambiguous module ownership visibly."""

    modules: dict[str, Path] = {}
    diagnostics: list[dict[str, Any]] = []
    for root in roots:
        if not root.path.is_dir():
            diagnostics.append(layout_diagnostic(root.path, "declared source root is absent"))
            continue
        for path in lean_paths_under_root(root.path):
            if ignored_source_path(path, root.path):
                continue
            name = module_name_under_root(root.path, path)
            if not selected_by_module_roots(name, root.module_roots):
                continue
            previous = modules.get(name)
            if previous is not None and previous != path:
                diagnostics.append(ambiguous_module_diagnostic(name, previous, path))
                continue
            modules[name] = path
    return dict(sorted(modules.items())), diagnostics


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
