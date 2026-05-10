"""Text-based Lean module discovery for Ladon's clean-core smoke path.

This module deliberately does not invoke Lake. It gives Ladon a fast, tested
module-DAG input surface while Lean-native declaration extraction is rebuilt in
later packets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ladon.ir import LeanModule


IMPORT_RE = re.compile(r"^import\s+([A-Za-z0-9_.]+)\s*$", re.MULTILINE)
DECL_RE = re.compile(
    r"^\s*(?:@[^\n]+\n\s*)*"
    r"(?:def|theorem|lemma|structure|class|abbrev|instance|inductive)\s+"
    r"([A-Za-z0-9_'.]+)",
    re.MULTILINE,
)


@dataclass(frozen=True)
class ModuleDiscovery:
    """Resolved module inventory for one Ladon clean-core run.

    `analysis_root_file` is the concrete Lean file selected by the CLI.
    `inventory_root` is the top-level namespace/file prefix scanned for the
    module DAG, for example `Quux` or `Mf`.
    """

    repo_root: Path
    analysis_root_file: Path
    analysis_root_module: str
    inventory_root: str
    modules: dict[str, LeanModule]


def module_name(repo_root: Path, file_path: Path) -> str:
    """Return the Lean module name implied by a repo-relative file path."""

    relative = file_path.relative_to(repo_root)
    return ".".join(relative.with_suffix("").parts)


def module_file(repo_root: Path, module: str) -> Path:
    """Return the conventional Lean file path for a module name."""

    return repo_root / Path(*module.split(".")).with_suffix(".lean")


def root_candidates(repo_root: Path, raw_root: str) -> list[Path]:
    """Return accepted file candidates for a CLI root value.

    The clean core accepts both repo-relative paths such as
    `Quux/Semantics/Propagation.lean` and module names such as
    `Quux.Semantics.Propagation`.
    """

    raw_path = Path(raw_root)
    candidates = absolute_or_relative_candidates(repo_root, raw_path)
    if raw_path.suffix != ".lean":
        candidates.append((repo_root / raw_path).with_suffix(".lean"))
        candidates.append(module_file(repo_root, raw_root))
    return unique_paths(candidates)


def absolute_or_relative_candidates(repo_root: Path, raw_path: Path) -> list[Path]:
    """Interpret CLI paths as absolute paths or repo-relative paths."""

    if raw_path.is_absolute():
        return [raw_path]
    return [repo_root / raw_path]


def unique_paths(paths: Sequence[Path]) -> list[Path]:
    """Preserve candidate order while removing duplicate paths."""

    unique: list[Path] = []
    for path in paths:
        if path not in unique:
            unique.append(path)
    return unique


def infer_root_file(repo_root: Path) -> Path:
    """Infer the top-level root file or fail if the choice is ambiguous."""

    top_level = sorted(path for path in repo_root.glob("*.lean") if path.is_file())
    if len(top_level) == 1:
        return top_level[0].resolve()
    if top_level:
        raise ValueError("multiple top-level Lean roots exist; pass --root")
    raise ValueError("no top-level Lean root exists; pass --root")


def resolve_root_file(repo_root: Path, raw_root: str | None) -> Path:
    """Resolve the analysis root to a Lean file inside `repo_root`."""

    if not raw_root:
        return infer_root_file(repo_root)
    existing = [path.resolve() for path in root_candidates(repo_root, raw_root) if path.is_file()]
    if not existing:
        raise ValueError(f"could not resolve analysis root {raw_root!r}")
    return ensure_inside_repo(repo_root, existing[0])


def ensure_inside_repo(repo_root: Path, file_path: Path) -> Path:
    """Validate that a resolved root is a Lean file inside the target repo."""

    try:
        file_path.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"analysis root {file_path} is outside {repo_root}") from exc
    if file_path.suffix != ".lean":
        raise ValueError(f"analysis root {file_path} is not a Lean file")
    return file_path


def inventory_root_for(root_file: Path, repo_root: Path) -> str:
    """Choose the namespace prefix scanned for module-DAG inventory."""

    relative = root_file.relative_to(repo_root)
    if len(relative.parts) > 1:
        return relative.parts[0]
    return relative.with_suffix("").name.split(".")[0]


def inventory_files(repo_root: Path, inventory_root: str) -> list[Path]:
    """Return top-level and nested Lean files for one namespace prefix."""

    files: list[Path] = []
    top_file = repo_root / f"{inventory_root}.lean"
    top_dir = repo_root / inventory_root
    if top_file.is_file():
        files.append(top_file)
    if top_dir.is_dir():
        files.extend(sorted(top_dir.rglob("*.lean")))
    return unique_paths(files)


def parse_lean_module(repo_root: Path, file_path: Path) -> LeanModule:
    """Parse imports and declaration names with text-level regexes only."""

    text = file_path.read_text(encoding="utf-8")
    return LeanModule(
        name=module_name(repo_root, file_path),
        path=str(file_path.relative_to(repo_root)),
        imports=tuple(IMPORT_RE.findall(text)),
        declarations=tuple(DECL_RE.findall(text)),
    )


def discover_modules(repo_root: Path, raw_root: str | None) -> ModuleDiscovery:
    """Discover the clean-core module inventory for one analysis root.

    Missing or ambiguous roots raise `ValueError`; callers decide how to render
    that failure for CLI users.
    """

    root = repo_root.resolve()
    root_file = resolve_root_file(root, raw_root)
    root_module = module_name(root, root_file)
    inventory_root = inventory_root_for(root_file, root)
    modules = {
        module.name: module
        for module in (parse_lean_module(root, path) for path in inventory_files(root, inventory_root))
    }
    return ModuleDiscovery(
        repo_root=root,
        analysis_root_file=root_file,
        analysis_root_module=root_module,
        inventory_root=inventory_root,
        modules=dict(sorted(modules.items())),
    )
