"""Lean parser-helper extraction for Ladon's clean-core backend seam.

This module runs the bundled Lean helper only when the user explicitly selects
the `lean` backend. It normalizes helper JSON into `LeanModule` so downstream
analysis remains backend-agnostic.
"""

from __future__ import annotations

import json
import hashlib
import subprocess
from collections.abc import Callable, Mapping
from importlib import resources
from pathlib import Path
from typing import Any

from ladon.extraction import ModuleDiscovery, module_name
from ladon.ir import ExtractionBundle, LeanDeclaration, LeanModule


DEFAULT_HELPER = Path(str(resources.files("ladon").joinpath("lean", "ladon_parser_helper.lean")))
HelperRunner = Callable[[Path, Path, Path], dict[str, Any]]


def extract_with_lean_helper(
    discovery: ModuleDiscovery,
    *,
    helper_path: Path = DEFAULT_HELPER,
    scope: str = "root",
    cache_dir: Path | None = None,
) -> ExtractionBundle:
    """Run parser-helper extraction for selected files in the inventory."""

    modules: dict[str, LeanModule] = {}
    declarations: dict[str, LeanDeclaration] = {}
    counters = {"lean_cache_hits": 0, "lean_cache_misses": 0}
    for file_path in selected_helper_files(discovery, scope):
        module, module_declarations = extract_file(
            discovery.repo_root,
            file_path,
            helper_path,
            cache_dir=cache_dir,
            counters=counters,
        )
        modules[module.name] = module
        declarations.update(module_declarations)
    return ExtractionBundle(modules=modules, declarations=declarations, counters=counters)


def selected_helper_files(discovery: ModuleDiscovery, scope: str) -> list[Path]:
    """Select root-only or full-inventory files for parser-helper extraction."""

    if scope == "root":
        return [discovery.analysis_root_file]
    if scope == "inventory":
        return [discovery.repo_root / module.path for module in discovery.modules.values()]
    raise ValueError(f"unsupported Lean extraction scope: {scope}")


def extract_file(
    repo_root: Path,
    file_path: Path,
    helper_path: Path,
    *,
    cache_dir: Path | None = None,
    counters: dict[str, int] | None = None,
) -> tuple[LeanModule, dict[str, LeanDeclaration]]:
    """Run the Lean helper for one file and normalize its JSON payload."""

    payload = helper_payload(repo_root, file_path, helper_path, cache_dir, counters)
    module = module_from_helper_payload(repo_root, file_path, payload)
    return module, declarations_from_helper_payload(module, payload)


def helper_payload(
    repo_root: Path,
    file_path: Path,
    helper_path: Path,
    cache_dir: Path | None,
    counters: dict[str, int] | None,
) -> dict[str, Any]:
    """Return helper JSON, using the optional content-addressed cache."""

    if cache_dir is None:
        increment_counter(counters, "lean_cache_misses")
        return run_helper(repo_root, file_path, helper_path)
    return cached_or_run_helper(repo_root, file_path, helper_path, cache_dir, counters, run_helper)


def run_helper(repo_root: Path, file_path: Path, helper_path: Path) -> dict[str, Any]:
    """Invoke `lake env lean --run` for the bundled helper."""

    relative = str(file_path.relative_to(repo_root))
    proc = subprocess.run(
        ["lake", "env", "lean", "--run", str(helper_path), "--", relative],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(helper_error(relative, proc.stdout, proc.stderr))
    return json.loads(proc.stdout)


def cached_or_run_helper(
    repo_root: Path,
    file_path: Path,
    helper_path: Path,
    cache_dir: Path,
    counters: dict[str, int] | None,
    runner: HelperRunner,
) -> dict[str, Any]:
    """Read a cached helper payload or run and store one."""

    path = cache_entry_path(repo_root, file_path, helper_path, cache_dir)
    if path.exists():
        increment_counter(counters, "lean_cache_hits")
        return json.loads(path.read_text(encoding="utf-8"))
    increment_counter(counters, "lean_cache_misses")
    payload = runner(repo_root, file_path, helper_path)
    write_cache_entry(path, payload)
    return payload


def cache_entry_path(
    repo_root: Path,
    file_path: Path,
    helper_path: Path,
    cache_dir: Path,
) -> Path:
    """Return the cache file for one repo/source/helper content tuple."""

    key = "\n".join(
        [
            str(repo_root.resolve()),
            str(file_path.relative_to(repo_root)),
            file_digest(file_path),
            file_digest(helper_path),
        ]
    )
    return cache_dir / f"{hashlib.sha256(key.encode()).hexdigest()}.json"


def file_digest(path: Path) -> str:
    """Return a SHA-256 digest for one local file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_cache_entry(path: Path, payload: Mapping[str, Any]) -> None:
    """Write one helper payload to its cache path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def increment_counter(counters: dict[str, int] | None, key: str) -> None:
    """Increment an optional integer counter map."""

    if counters is not None:
        counters[key] = counters.get(key, 0) + 1


def helper_error(relative_path: str, stdout: str, stderr: str) -> str:
    """Build a concise parser-helper failure message."""

    details = (stderr or stdout).strip()
    return f"Lean parser helper failed for {relative_path}: {details}"


def module_from_helper_payload(
    repo_root: Path,
    file_path: Path,
    payload: Mapping[str, Any],
) -> LeanModule:
    """Normalize parser-helper JSON into the stable `LeanModule` IR."""

    return LeanModule(
        name=module_name(repo_root, file_path),
        path=str(file_path.relative_to(repo_root)),
        imports=helper_imports(payload),
        declarations=helper_declarations(payload),
    )


def declarations_from_helper_payload(
    module: LeanModule,
    payload: Mapping[str, Any],
) -> dict[str, LeanDeclaration]:
    """Normalize parser-helper declaration commands into declaration IR."""

    declarations = [
        declaration_from_command(module, command)
        for command in payload.get("commands", [])
        if command.get("isDeclarationLike")
    ]
    return {declaration.name: declaration for declaration in declarations if declaration}


def declaration_from_command(
    module: LeanModule,
    command: Mapping[str, Any],
) -> LeanDeclaration | None:
    """Convert one helper command to `LeanDeclaration` when named."""

    name = command.get("declarationFullName") or command.get("declarationName")
    if not name:
        return None
    return LeanDeclaration(
        name=name,
        module=module.name,
        kind=command.get("declarationKind"),
        references=tuple(command.get("referenceCandidates", [])),
    )


def helper_imports(payload: Mapping[str, Any]) -> tuple[str, ...]:
    """Extract imported module names from helper JSON."""

    header = payload.get("header", {})
    return tuple(entry["module"] for entry in header.get("imports", []))


def helper_declarations(payload: Mapping[str, Any]) -> tuple[str, ...]:
    """Extract declaration names, preferring fully qualified helper names."""

    names = [
        command.get("declarationFullName") or command.get("declarationName")
        for command in payload.get("commands", [])
        if command.get("isDeclarationLike")
    ]
    return tuple(name for name in names if name)
