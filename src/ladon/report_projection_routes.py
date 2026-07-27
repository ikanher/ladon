"""Stable route joins for bounded report review regions."""

from __future__ import annotations

from typing import Any, Mapping

from ladon.report_contract import copy_json
from ladon.report_stratification import stratified_selection


INSPECTION_REGION_ROUTES = {
    "audit_surface_region": (
        "audits",
        "auditCommands",
        "auditProducerRegistrations",
    ),
    "option_resource_region": (
        "resources",
        "resourceDirectives",
        "resourceProducerRegistrations",
    ),
}


def routed_inspection_signal(
    signal: Mapping[str, Any],
    *,
    noun: str,
    canonical_owners: Mapping[str, str],
    projected_owners: Mapping[str, str],
) -> dict[str, Any] | None:
    """Rewrite one exact-row route when that owner survived projection."""

    target = _exact_inspection_target(signal.get("inspectionAction"), noun)
    if target is None:
        return None
    canonical_pointer = canonical_owners.get(target)
    projected_pointer = projected_owners.get(target)
    references = signal.get("evidenceRefs")
    if (
        canonical_pointer is None
        or projected_pointer is None
        or not isinstance(references, list)
        or canonical_pointer not in references
    ):
        return None
    rewritten = [
        projected_pointer if reference == canonical_pointer else reference
        for reference in references
    ]
    return {**copy_json(signal), "evidenceRefs": rewritten}


def inspection_owner_pointers(
    sections: Mapping[str, Any],
) -> dict[str, dict[str, str]]:
    """Index projected audit/resource rows by their stable inspection IDs."""

    result = {"audits": {}, "resources": {}}
    module_dag = sections.get("module_dag")
    if not isinstance(module_dag, Mapping):
        return result
    surfaces = module_dag.get("audit_surfaces")
    if not isinstance(surfaces, list):
        return result
    ambiguous = {"audits": set(), "resources": set()}
    collections = {
        "audits": "auditCommands",
        "resources": "resourceDirectives",
    }
    for surface_index, surface in enumerate(surfaces):
        if not isinstance(surface, Mapping):
            continue
        for noun, collection in collections.items():
            _index_inspection_rows(
                result[noun],
                ambiguous[noun],
                surface.get(collection),
                pointer=(
                    f"#/sections/module_dag/audit_surfaces/{surface_index}/{collection}"
                ),
            )
    for noun in result:
        for identity in ambiguous[noun]:
            result[noun].pop(identity, None)
    return result


def inspection_region_noun(region: Any) -> str | None:
    """Return the routed inspection noun for a registered region kind."""

    if not isinstance(region, Mapping):
        return None
    route = INSPECTION_REGION_ROUTES.get(region.get("kind"))
    if route is None:
        return None
    action = region.get("inspectionAction")
    if not isinstance(action, Mapping) or action.get("command") != "ladon":
        return None
    arguments = action.get("arguments")
    if not isinstance(arguments, list) or arguments[:2] != ["inspect", route[0]]:
        return None
    return route[0]


def regions_by_id(value: list[Any]) -> dict[str, Mapping[str, Any]]:
    """Index canonical region records by stable identity."""

    return {
        str(row["id"]): row
        for row in value
        if isinstance(row, Mapping) and isinstance(row.get("id"), str) and row["id"]
    }


def mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    """Return mapping rows from a JSON array."""

    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def selection_strata(
    canonical: list[Mapping[str, Any]],
    selected: list[Mapping[str, Any]],
    *,
    pointer: str,
) -> list[dict[str, Any]]:
    """Return canonical totals with visibility from the route-safe subset."""

    totals: list[dict[str, Any]] = []
    visible: list[dict[str, Any]] = []
    stratified_selection(canonical, limit=0, pointer=pointer, strata=totals)
    stratified_selection(
        selected,
        limit=len(selected),
        pointer=pointer,
        strata=visible,
    )
    visible_by_descriptor = {
        _descriptor_key(row["descriptor"]): row["visible"] for row in visible
    }
    return [
        {
            **row,
            "visible": visible_by_descriptor.get(
                _descriptor_key(row["descriptor"]),
                0,
            ),
        }
        for row in totals
    ]


def pointer_is_within(candidate: Any, parent: str) -> bool:
    """Return whether one JSON pointer is the parent or its descendant."""

    return isinstance(candidate, str) and (
        candidate == parent or candidate.startswith(f"{parent}/")
    )


def _index_inspection_rows(
    pointers: dict[str, str],
    ambiguous: set[str],
    value: Any,
    *,
    pointer: str,
) -> None:
    """Add unambiguous stable row IDs from one audit-surface collection."""

    if not isinstance(value, list):
        return
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            continue
        identity = row.get("id")
        if not isinstance(identity, str) or not identity:
            continue
        if identity in pointers:
            ambiguous.add(identity)
        else:
            pointers[identity] = f"{pointer}/{index}"


def _exact_inspection_target(value: Any, noun: str) -> str | None:
    """Return the stable ID from a complete exact-row inspection action."""

    if not isinstance(value, Mapping) or value.get("command") != "ladon":
        return None
    arguments = value.get("arguments")
    if (
        not isinstance(arguments, list)
        or len(arguments) != 4
        or arguments[:3] != ["inspect", noun, "--id"]
        or not isinstance(arguments[3], str)
        or not arguments[3]
    ):
        return None
    return arguments[3]


def _descriptor_key(value: Any) -> tuple[tuple[str, str], ...]:
    """Return a hashable stable form of one stratum descriptor."""

    if not isinstance(value, Mapping):
        return ()
    return tuple(sorted((str(key), str(item)) for key, item in value.items()))
