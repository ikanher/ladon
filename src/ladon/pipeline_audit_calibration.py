"""Lexical audit extraction, ownership joins, and result enrichment."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from ladon.analysis.audit_ownership import attach_lexical_audit_candidates
from ladon.analysis.audit_registrations import (
    attach_audit_producer_registrations,
)
from ladon.analysis.audit_surface import audit_surface_from_index
from ladon.audit_enrichment import apply_audit_query
from ladon.ir import LeanAuditQuery, LeanModule
from ladon.pipeline_declaration_calibration import (
    attach_declaration_populations,
)
from ladon.pipeline_models import RunContext
from ladon.source_index_models import SourceIndex


def attach_audit_surfaces(
    context: RunContext,
    dag: dict[str, Any],
    modules: Mapping[str, LeanModule],
) -> None:
    """Attach lexical audit commands and resource directives to their owners."""

    rows: list[dict[str, Any]] = []
    metadata = dag.get("module_metadata", {})
    for module in modules.values():
        # Keep deterministic drift-injection timing without reopening the
        # source: every row below is already owned by the source index.
        if context.snapshot_read_hook is not None:
            context.snapshot_read_hook(context, module)
        surface = _audit_surface_for_module(module)
        if surface is None:
            continue
        row = surface.to_dict()
        attach_audit_query_results(row, context.lean_audit_queries)
        rows.append(row)
        _attach_audit_metadata(metadata.get(module.name), surface)
    dag["audit_surfaces"] = rows
    dag["audit_summary"] = _audit_surface_summary(rows)


def _audit_surface_for_module(
    module: LeanModule,
) -> Any | None:
    surface = audit_surface_from_index(
        module.name,
        module.path,
        declaration_count=len(module.declarations),
        audit_commands=module.audit_commands,
        resource_settings=module.resource_settings,
    )
    if not surface.commands and not surface.resource_directives:
        return None
    return surface


def _attach_audit_metadata(module_row: Any, surface: Any) -> None:
    """Attach bounded audit counts to an existing module metadata row."""

    if not isinstance(module_row, dict):
        return
    module_row["commandOnly"] = surface.command_only
    module_row["auditCommandCount"] = len(surface.commands)
    module_row["resourceDirectiveCount"] = len(surface.resource_directives)


def _audit_surface_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate lexical audit populations without changing row authority."""

    return {
        "modules": len(rows),
        "commandOnlyModules": sum(1 for row in rows if bool(row.get("commandOnly"))),
        "auditCommands": sum(
            int(row.get("summary", {}).get("auditCommands", 0)) for row in rows
        ),
        "resourceDirectives": sum(
            int(row.get("summary", {}).get("resourceDirectives", 0)) for row in rows
        ),
        "backend": "text",
        "authority": "lexical_text",
    }


def attach_audit_query_results(
    surface: dict[str, Any],
    queries: Mapping[str, LeanAuditQuery],
) -> None:
    """Join helper results to stable lexical command identifiers."""

    for command in surface.get("auditCommands", []):
        if isinstance(command, dict):
            apply_audit_query(
                command,
                queries.get(str(command.get("id", ""))),
            )


def enrich_audit_and_declaration_populations(
    dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
    source_index: SourceIndex | None = None,
    source_pattern_policy: Mapping[str, Any] | None = None,
    source_pattern_policy_identity: Mapping[str, Any] | None = None,
) -> None:
    """Join optional Lean declaration identity and calibrated ownership."""

    declarations = _declaration_rows(declaration_graph)
    by_name = {
        str(row.get("declaration")): row
        for row in declarations
        if row.get("declaration")
    }
    if declaration_graph is not None:
        attach_declaration_populations(dag, declaration_graph, declarations)
    attach_lexical_audit_candidates(
        dag.get("audit_surfaces", []),
        source_index,
    )
    _enrich_audit_surfaces(dag.get("audit_surfaces", []), by_name)
    attach_audit_producer_registrations(
        dag,
        source_index,
        declaration_graph,
        source_pattern_policy,
        source_pattern_policy_identity,
    )


def _declaration_rows(
    declaration_graph: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Return typed declaration rows from an optional graph."""

    if declaration_graph is None:
        return []
    return [
        row
        for row in declaration_graph.get("declarations", [])
        if isinstance(row, dict)
    ]


def _enrich_audit_surfaces(
    surfaces: Any,
    declarations: Mapping[str, dict[str, Any]],
) -> None:
    """Enrich typed audit commands while ignoring malformed compatibility rows."""

    if not isinstance(surfaces, Sequence):
        return
    for surface in surfaces:
        if not isinstance(surface, dict):
            continue
        for command in surface.get("auditCommands", []):
            if isinstance(command, dict):
                enrich_audit_command(command, declarations)


def enrich_audit_command(
    command: dict[str, Any],
    by_name: Mapping[str, dict[str, Any]],
) -> None:
    """Attach exact identity candidates without claiming command resolution."""

    referenced = str(command.get("referencedDeclaration") or "").strip()
    if not referenced:
        return
    declaration = by_name.get(referenced)
    if declaration is None:
        _mark_missing_query_result(command)
        return
    command["referencedDeclaration"] = declaration.get("declaration")
    command["referencedOwner"] = declaration.get("module")
    command["referencedPopulation"] = declaration.get("population")
    command["referencedBackend"] = declaration.get("extractionBackend")
    if command.get("queryResult") is None:
        command["resultStatus"] = "unavailable"
        command["resultReason"] = (
            "An exact extracted declaration identity exists, but no "
            "command-specific Lean resolution or query result was captured."
        )


def _mark_missing_query_result(command: dict[str, Any]) -> None:
    if command.get("queryResult") is not None:
        return
    command["resultStatus"] = "unavailable"
    command["resultReason"] = (
        "No command-specific Lean resolution result was captured; "
        "lexical subjects are not resolved by suffix matching."
    )


__all__ = [
    "attach_audit_query_results",
    "attach_audit_surfaces",
    "enrich_audit_and_declaration_populations",
    "enrich_audit_command",
]
