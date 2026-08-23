"""Lean parser-helper extraction for Ladon's clean-core backend seam.

This module runs the bundled Lean helper only when the user explicitly selects
the `lean` backend. It normalizes helper JSON into `LeanModule` so downstream
analysis remains backend-agnostic.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Callable, Mapping
from importlib import resources
from pathlib import Path
from typing import Any

from ladon.extraction import ModuleDiscovery, module_name
from ladon.ir import BoundedStrings, ExtractionBundle, LeanDeclaration, LeanModule
from ladon.lean_runtime import (
    DEFAULT_LEAN_BATCH_SIZE,
    DEFAULT_LEAN_BATCH_TIMEOUT_SECONDS,
    LeanRuntimeConfig,
    RequestedModule,
    execute_lean_runtime,
)
from ladon.process_supervisor import run_target_process
from ladon.semantic_lean_execution import prepare_direct_lean_execution

DEFAULT_HELPER = Path(str(resources.files("ladon").joinpath("lean", "ladon_parser_helper.lean")))
HelperRunner = Callable[[Path, Path, Path], dict[str, Any]]


def extract_with_lean_helper(
    discovery: ModuleDiscovery,
    *,
    helper_path: Path = DEFAULT_HELPER,
    scope: str = "root",
    cache_dir: Path | None = None,
    batch_size: int = DEFAULT_LEAN_BATCH_SIZE,
    timeout_seconds: float = DEFAULT_LEAN_BATCH_TIMEOUT_SECONDS,
    strict: bool = False,
    cancel_event: threading.Event | None = None,
    build_requested: bool = False,
) -> ExtractionBundle:
    """Run bounded parser-helper batches for selected inventory modules."""

    modules: dict[str, LeanModule] = {}
    declarations: dict[str, LeanDeclaration] = {}
    requested = selected_helper_modules(discovery, scope)
    runtime = execute_lean_runtime(
        repo_root=discovery.repo_root,
        helper_path=helper_path,
        requested=requested,
        modules=discovery.modules,
        cache_dir=cache_dir,
        config=LeanRuntimeConfig(
            batch_size=batch_size,
            timeout_seconds=timeout_seconds,
            strict=strict,
            cancel_event=cancel_event,
        ),
        build_requested=build_requested,
    )
    requested_by_module = {row.module: row for row in requested}
    for module_name_value, payload in runtime.payloads.items():
        request = requested_by_module[module_name_value]
        file_path = discovery.repo_root / request.file
        module = module_from_helper_payload(
            discovery.repo_root,
            file_path,
            payload,
            module_override=module_name_value,
        )
        module_declarations = declarations_from_helper_payload(
            module,
            payload,
            source_content_hash=source_content_hash(file_path),
        )
        modules[module.name] = module
        declarations.update(module_declarations)
    return ExtractionBundle(
        modules=modules,
        declarations=declarations,
        counters=dict(runtime.counters),
        diagnostics=runtime.diagnostics,
        runtime=dict(runtime.provenance),
    )


def selected_helper_modules(
    discovery: ModuleDiscovery,
    scope: str,
) -> tuple[RequestedModule, ...]:
    """Select ordered module/file identities without re-inventing names."""

    if scope == "root":
        module = discovery.modules.get(discovery.analysis_root_module)
        path = (
            module.path
            if module is not None
            else str(discovery.analysis_root_file.relative_to(discovery.repo_root))
        )
        return (RequestedModule(discovery.analysis_root_module, path),)
    if scope == "inventory":
        return tuple(
            RequestedModule(module.name, module.path)
            for module in discovery.modules.values()
        )
    raise ValueError(f"unsupported Lean extraction scope: {scope}")


def selected_helper_files(discovery: ModuleDiscovery, scope: str) -> list[Path]:
    """Select root-only or full-inventory files for parser-helper extraction."""

    return [
        discovery.repo_root / request.file
        for request in selected_helper_modules(discovery, scope)
    ]


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
    return module, declarations_from_helper_payload(
        module,
        payload,
        source_content_hash=source_content_hash(file_path),
    )


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
    """Invoke the legacy single-file helper with a finite supervised deadline."""

    relative = str(file_path.relative_to(repo_root))
    execution = prepare_direct_lean_execution(
        repo_root,
        module_name(repo_root, file_path),
        None,
        require_compiled_module=True,
    )
    result = run_target_process(
        [*execution.command, "--run", str(helper_path), "--", relative],
        cwd=repo_root,
        env=execution.environment,
        timeout_seconds=DEFAULT_LEAN_BATCH_TIMEOUT_SECONDS,
    )
    if not result.succeeded:
        raise RuntimeError(helper_error(relative, result.stdout, result.stderr))
    return json.loads(result.stdout)


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


def source_content_hash(path: Path) -> str:
    """Return the report-facing source content hash for one local file."""

    return f"sha256:{file_digest(path)}"


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
    *,
    module_override: str | None = None,
) -> LeanModule:
    """Normalize parser-helper JSON into the stable `LeanModule` IR."""

    return LeanModule(
        name=module_override or module_name(repo_root, file_path),
        path=str(file_path.relative_to(repo_root)),
        imports=helper_imports(payload),
        declarations=helper_declarations(payload),
    )


def declarations_from_helper_payload(
    module: LeanModule,
    payload: Mapping[str, Any],
    *,
    source_content_hash: str | None = None,
) -> dict[str, LeanDeclaration]:
    """Normalize parser-helper declaration commands into declaration IR."""

    declarations = [
        declaration_from_command(
            module,
            command,
            source_content_hash=source_content_hash,
            extractor_version=str(payload.get("version", "")) or None,
        )
        for command in payload.get("commands", [])
        if command.get("isDeclarationLike")
    ]
    return {declaration.name: declaration for declaration in declarations if declaration}


def declaration_from_command(
    module: LeanModule,
    command: Mapping[str, Any],
    *,
    source_content_hash: str | None = None,
    extractor_version: str | None = None,
) -> LeanDeclaration | None:
    """Convert one helper command to `LeanDeclaration` when named."""

    name = command.get("declarationFullName") or command.get("declarationName")
    if not name:
        return None
    source_range = normalize_helper_range(command.get("range"))
    references = tuple(
        str(candidate)
        for candidate in command.get("referenceCandidates", [])
    )
    return LeanDeclaration(
        name=name,
        module=module.name,
        kind=command.get("declarationKind"),
        references=references,
        source_path=module.path,
        source_range=source_range,
        selection_range=normalize_helper_range(command.get("selectionRange")),
        content_hash=source_content_hash,
        extraction_backend="lean_parser_helper",
        extractor_version=extractor_version,
        name_resolution_method=name_resolution_method(command),
        confidence="parser_source_range" if source_range else "parser_decl_name",
        parser_candidates=bounded_parser_candidates(references),
    )


def bounded_parser_candidates(
    references: tuple[str, ...],
    *,
    cap: int = 64,
) -> BoundedStrings:
    """Retain finite parser candidates without claiming elaborated authority."""

    items = tuple(sorted(set(references)))
    visible = items[:cap]
    return BoundedStrings(
        items=visible,
        total=len(items),
        truncated=len(items) > len(visible),
        status="complete",
        reason=None,
        authority="lean_parser",
    )


def name_resolution_method(command: Mapping[str, Any]) -> str:
    """Return the helper method used to attach a declaration name."""

    if command.get("declarationFullName"):
        return "parser_namespace_stack"
    return "parser_decl_name"


def normalize_helper_range(value: Any) -> dict[str, int] | None:
    """Normalize helper ranges to report-facing line and column fields."""

    if not isinstance(value, Mapping):
        return None
    start = helper_position(value.get("start"))
    finish = helper_position(value.get("finish"))
    if start is None or finish is None:
        return None
    return {
        "startLine": start["line"],
        "startColumn": start["column"],
        "endLine": finish["line"],
        "endColumn": finish["column"],
    }


def helper_position(value: Any) -> dict[str, int] | None:
    """Normalize one helper position object."""

    if not isinstance(value, Mapping):
        return None
    try:
        line = int(value.get("line", 0))
        column = int(value.get("column", 0))
    except (TypeError, ValueError):
        return None
    if line <= 0 or column <= 0:
        return None
    return {"line": line, "column": column}


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
