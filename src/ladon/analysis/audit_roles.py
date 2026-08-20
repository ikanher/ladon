"""Finalize module roles after canonical lexical audit evidence is attached."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any

AUDIT_SURFACE_ROLE = "audit_surface"
COMMAND_ONLY_AUDIT_FACADE = "command_only_audit_facade"
GENERATED_AGGREGATION_SUBTYPE = "generated_all"


def finalize_audit_roles(dag: dict[str, Any]) -> None:
    """Reclassify command-only audit modules from source and graph evidence.

    The module-DAG owner has already applied its ordinary facade predicate.
    This pass consumes that result rather than inventing a second facade rule:
    an audit-only module is an audit facade exactly when its pre-audit subtype
    was facade-qualified.  Generated aggregation retains its owning subtype.
    """

    metadata = _mapping(dag.get("module_metadata"))
    surfaces = _audit_surfaces(dag.get("audit_surfaces"))
    for module, surface in surfaces.items():
        row = metadata.get(module)
        if not isinstance(row, dict):
            continue
        row["auditRoleClassification"] = {
            "commandOnly": True,
            "auditCommandCount": len(surface.get("auditCommands", [])),
            "preAuditFacadeSubtype": str(row.get("facadeSubtype", "")),
            "authority": "lexical_audit_commands_and_module_import_graph",
            "nonclaim": (
                "A source-navigation role only; not a Lean elaboration, "
                "proof-correctness, theorem-truth, or public-API verdict."
            ),
        }
        _classify_command_only_row(row)
    _refresh_facade_views(dag, metadata)


def _audit_surfaces(raw: Any) -> dict[str, dict[str, Any]]:
    """Return command-only surfaces with at least one parsed lexical command."""

    if not isinstance(raw, list):
        return {}
    return {
        str(row.get("module")): row
        for row in raw
        if isinstance(row, dict)
        and bool(row.get("commandOnly"))
        and bool(row.get("auditCommands"))
        and row.get("module")
    }


def _mapping(raw: Any) -> dict[str, Any]:
    """Return a mutable string-key mapping or an empty mapping."""

    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items()}


def _classify_command_only_row(row: dict[str, Any]) -> None:
    """Apply the post-audit role transition to one module metadata row."""

    original = str(row.get("facadeSubtype", ""))
    if original == GENERATED_AGGREGATION_SUBTYPE:
        row["roles"] = _roles("facade", original, AUDIT_SURFACE_ROLE)
        return
    if original:
        row["facadeSubtype"] = COMMAND_ONLY_AUDIT_FACADE
        row["roles"] = _roles(
            "facade",
            COMMAND_ONLY_AUDIT_FACADE,
            AUDIT_SURFACE_ROLE,
        )
        return
    row["facadeSubtype"] = ""
    row["roles"] = [AUDIT_SURFACE_ROLE]


def _roles(*roles: str) -> list[str]:
    """Return unique roles in owning-rule order."""

    return list(dict.fromkeys(role for role in roles if role))


def _refresh_facade_views(
    dag: dict[str, Any],
    metadata: Mapping[str, Any],
) -> None:
    """Rebuild every facade projection from the finalized metadata."""

    facade_rows = [
        {
            "module": module,
            "path": str(row.get("path", "")),
            "fan_out": int(row.get("importCount", 0)),
            "declarationCount": int(row.get("declarationCount", 0)),
            "subtype": str(row.get("facadeSubtype", "")),
            "tags": list(row.get("tags", [])),
        }
        for module, row in metadata.items()
        if isinstance(row, dict) and row.get("facadeSubtype")
    ]
    facade_rows.sort(
        key=lambda row: (-int(row["fan_out"]), str(row["module"]))
    )
    subtypes = Counter(str(row["subtype"]) for row in facade_rows)
    names = sorted(str(row["module"]) for row in facade_rows)
    dag["facade_modules"] = names[:20]
    dag["facade_module_count"] = len(names)
    dag["facade_subtype_summary"] = dict(sorted(subtypes.items()))
    dag["top_facade_like_modules"] = facade_rows[:20]
