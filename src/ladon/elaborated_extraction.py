"""Side-effect boundary for the packaged Lean elaborated-surface helper."""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Mapping
from dataclasses import replace
from importlib import resources
from pathlib import Path
from typing import Any

from ladon.audit_enrichment import (
    audit_queries_from_elaborated_payload,
    unavailable_audit_queries,
)
from ladon.declaration_surface import (
    declarations_from_elaborated_payload,
    join_declaration_inventories,
)
from ladon.extraction import ModuleDiscovery, module_name
from ladon.ir import ExtractionBundle, LeanAuditQuery, LeanDeclaration
from ladon.process_supervisor import ProcessCancelled, run_target_process
from ladon.semantic_lean_execution import prepare_direct_lean_execution

DEFAULT_ELABORATED_HELPER = Path(
    str(resources.files("ladon").joinpath("lean", "ladon_elaborated_helper.lean"))
)


def augment_with_elaborated_surfaces(
    discovery: ModuleDiscovery,
    bundle: ExtractionBundle,
    *,
    helper_path: Path = DEFAULT_ELABORATED_HELPER,
    scope: str = "root",
    timeout_seconds: float = 120.0,
    cancel_event: threading.Event | None = None,
) -> ExtractionBundle:
    """Add Lean-environment surfaces to an existing parser extraction bundle."""

    declarations = dict(bundle.declarations or {})
    elaborated_count = 0
    failures = 0
    diagnostics = list(bundle.diagnostics)
    audit_queries = dict(bundle.audit_queries)
    selected_files = selected_surface_files(discovery, scope)
    for index, file_path in enumerate(selected_files):
        module = module_name(discovery.repo_root, file_path)
        source_path = str(file_path.relative_to(discovery.repo_root))
        source_text = readable_source(file_path)
        parser_rows = declarations_for_module(declarations, module)
        try:
            payload = run_elaborated_helper(
                discovery.repo_root,
                file_path,
                module,
                helper_path=helper_path,
                timeout_seconds=timeout_seconds,
                cancel_event=cancel_event,
            )
        except ProcessCancelled as error:
            reason = str(error)
            declarations = mark_module_surface_unavailable(
                declarations,
                module,
                reason,
            )
            diagnostics.append(
                {
                    "id": "lean.elaborated_surface_cancelled",
                    "severity": "warning",
                    "message": reason,
                    "subject": module,
                }
            )
            audit_queries.update(
                failed_audit_queries(
                    discovery,
                    selected_files[index:],
                    reason,
                )
            )
            failures += len(selected_files) - index
            break
        except RuntimeError as error:
            reason = str(error)
            declarations = mark_module_surface_unavailable(
                declarations,
                module,
                reason,
            )
            diagnostics.append(
                {
                    "id": "lean.elaborated_surface_unavailable",
                    "severity": "warning",
                    "message": reason,
                    "subject": module,
                }
            )
            audit_queries.update(
                unavailable_audit_queries(
                    module,
                    source_path,
                    source_text,
                    reason,
                )
            )
            failures += 1
            continue
        normalized = declarations_from_elaborated_payload(
            module,
            source_path,
            payload,
            parser_declarations=parser_rows,
            source_content_hash=source_hash(file_path),
            restrict_to_parser_inventory=True,
        )
        declarations = join_declaration_inventories(declarations, normalized)
        audit_queries.update(
            audit_queries_from_elaborated_payload(
                module,
                source_path,
                source_text,
                payload,
            )
        )
        elaborated_count += sum(
            1 for row in normalized.values() if not row.is_imported_stub
        )
    counters = dict(bundle.counters)
    counters["elaborated_declarations"] = elaborated_count
    counters["elaborated_imported_stubs"] = sum(
        1 for row in declarations.values() if row.is_imported_stub
    )
    counters["elaborated_failed"] = failures
    counters.update(audit_query_counters(audit_queries))
    return ExtractionBundle(
        modules=bundle.modules,
        declarations=declarations,
        counters=counters,
        diagnostics=tuple(diagnostics),
        runtime=bundle.runtime,
        audit_queries=audit_queries,
    )


def run_elaborated_helper(
    repo_root: Path,
    file_path: Path,
    module: str,
    *,
    helper_path: Path = DEFAULT_ELABORATED_HELPER,
    timeout_seconds: float = 120.0,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """Run the elaborated helper and parse its JSON suffix."""

    relative = str(file_path.relative_to(repo_root))
    execution = prepare_direct_lean_execution(
        repo_root,
        module,
        None,
        require_compiled_module=True,
    )
    process = run_target_process(
        [
            *execution.command,
            "--run",
            str(helper_path),
            module,
            relative,
        ],
        cwd=repo_root,
        env=execution.environment,
        timeout_seconds=timeout_seconds,
        cancel_event=cancel_event,
    )
    if not process.succeeded:
        details = (process.stderr or process.stdout).strip()
        outcome = "timed out" if process.timed_out else "failed"
        raise RuntimeError(
            f"Lean elaborated helper {outcome} for {relative}: {details}"
        )
    return parse_helper_json_suffix(process.stdout)


def parse_helper_json_suffix(stdout: str) -> dict[str, Any]:
    """Parse JSON after any Lean warning text emitted by the frontend."""

    starts = [
        index
        for marker in ('{"version"', "{\n \"version\"")
        for index in [stdout.find(marker)]
        if index >= 0
    ]
    if not starts:
        raise RuntimeError("Lean elaborated helper emitted no JSON payload")
    try:
        payload = json.loads(stdout[min(starts):])
    except json.JSONDecodeError as error:
        raise RuntimeError("Lean elaborated helper emitted invalid JSON") from error
    if not isinstance(payload, dict):
        raise TypeError("Lean elaborated helper payload must be an object")
    return payload


def mark_module_surface_unavailable(
    declarations: Mapping[str, LeanDeclaration],
    module: str,
    reason: str,
) -> dict[str, LeanDeclaration]:
    """Attach an explicit helper-failure state to parser rows in one module."""

    updated = dict(declarations)
    for name, declaration in declarations.items():
        if declaration.module != module or declaration.is_imported_stub:
            continue
        updated[name] = replace(
            declaration,
            type_dependencies=replace(
                declaration.type_dependencies,
                status="unavailable",
                reason=reason,
            ),
            value_dependencies=replace(
                declaration.value_dependencies,
                status="unavailable",
                reason=reason,
            ),
            surface=replace(
                declaration.surface,
                status="unavailable",
                reason=reason,
            ),
        )
    return updated


def selected_surface_files(
    discovery: ModuleDiscovery,
    scope: str,
) -> list[Path]:
    """Select root-only or inventory elaboration files deterministically."""

    if scope == "root":
        return [discovery.analysis_root_file]
    if scope == "inventory":
        return [
            discovery.repo_root / module.path
            for module in sorted(discovery.modules.values(), key=lambda row: row.name)
        ]
    raise TypeError(f"unsupported elaborated extraction scope: {scope}")


def declarations_for_module(
    declarations: Mapping[str, LeanDeclaration],
    module: str,
) -> dict[str, LeanDeclaration]:
    """Return parser rows owned by one module."""

    return {
        name: declaration
        for name, declaration in declarations.items()
        if declaration.module == module and not declaration.is_imported_stub
    }


def failed_audit_queries(
    discovery: ModuleDiscovery,
    files: list[Path],
    reason: str,
) -> dict[str, LeanAuditQuery]:
    """Return explicit failure rows for every cancelled helper target."""

    queries: dict[str, LeanAuditQuery] = {}
    for file_path in files:
        queries.update(
            unavailable_audit_queries(
                module_name(discovery.repo_root, file_path),
                str(file_path.relative_to(discovery.repo_root)),
                readable_source(file_path),
                reason,
            )
        )
    return queries


def audit_query_counters(
    queries: Mapping[str, LeanAuditQuery],
) -> dict[str, int]:
    """Return bounded query-result counters for extraction telemetry."""

    counters = {"audit_queries": len(queries)}
    for status in (
        "complete",
        "partial",
        "unresolved",
        "unavailable",
        "timeout",
    ):
        counters[f"audit_queries_{status}"] = sum(
            1 for row in queries.values() if row.status == status
        )
    return counters


def readable_source(path: Path) -> str:
    """Return source text when the later lexical boundary can also read it."""

    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def source_hash(path: Path) -> str:
    """Return the declaration source's report-facing content hash."""

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"
