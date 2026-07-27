"""Route-safe closure for evidence embedded in canonical projected rows."""

from __future__ import annotations

from typing import Any, Mapping

from ladon.finding_evidence import resolve_local_json_pointer
from ladon.report_contract import copy_json
from ladon.report_projection_evidence_closure import EvidenceClosure
from ladon.report_projection_routes import selection_strata


_IMPORT_BOUNDARY_POINTER = "#/sections/module_dag/import_boundaries"


def reconcile_intrinsic_evidence_routes(
    canonical_sections: Mapping[str, Any],
    projected_sections: Mapping[str, Any],
    *,
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> dict[str, Any]:
    """Retain exact owners for local evidence pointers embedded in data rows."""

    projected = (
        projected_sections
        if isinstance(projected_sections, dict)
        else dict(projected_sections)
    )
    collections = _import_boundary_collections(canonical_sections, projected)
    if collections is None:
        return projected
    canonical_rows, projected_rows = collections
    canonical_by_id = _unique_rows_by_id(canonical_rows)
    closure = EvidenceClosure(
        canonical=canonical_sections,
        projected=projected,
        changed={},
        limit=limit,
    )
    reconciled, integrity_omitted = _reconciled_rows(
        projected_rows,
        canonical_by_id=canonical_by_id,
        closure=closure,
    )
    projected_rows[:] = reconciled
    _refresh_boundary_ledger(
        canonical_rows,
        reconciled,
        integrity_omitted=integrity_omitted,
        omissions=omissions,
        strata=strata,
    )
    _refresh_changed_collection_ledgers(
        closure.changed,
        omissions=omissions,
        strata=strata,
    )
    return projected


def _import_boundary_collections(
    canonical_sections: Mapping[str, Any],
    projected_sections: Mapping[str, Any],
) -> tuple[list[Any], list[Any]] | None:
    canonical_dag = canonical_sections.get("module_dag")
    projected_dag = projected_sections.get("module_dag")
    if not isinstance(canonical_dag, Mapping) or not isinstance(
        projected_dag,
        Mapping,
    ):
        return None
    canonical_rows = canonical_dag.get("import_boundaries")
    projected_rows = projected_dag.get("import_boundaries")
    if not isinstance(canonical_rows, list) or not isinstance(
        projected_rows,
        list,
    ):
        return None
    return canonical_rows, projected_rows


def _reconciled_rows(
    projected_rows: list[Any],
    *,
    canonical_by_id: Mapping[str, Mapping[str, Any]],
    closure: EvidenceClosure,
) -> tuple[list[Any], int]:
    reconciled: list[Any] = []
    integrity_omitted = 0
    for row in list(projected_rows):
        identity = row.get("id") if isinstance(row, Mapping) else None
        canonical_row = (
            canonical_by_id.get(identity) if isinstance(identity, str) else None
        )
        if (
            canonical_row is None
            or (
                routed := _routed_row(
                    row,
                    canonical_row=canonical_row,
                    closure=closure,
                )
            )
            is None
        ):
            integrity_omitted += 1
            continue
        reconciled.append(routed)
    return reconciled, integrity_omitted


def _routed_row(
    row: Mapping[str, Any],
    *,
    canonical_row: Mapping[str, Any],
    closure: EvidenceClosure,
) -> dict[str, Any] | None:
    if not _canonical_routes_valid(
        canonical_row,
        canonical_sections=closure.canonical,
    ):
        return None
    routes = _projected_routes(row, canonical_row=canonical_row)
    if routes is None:
        return None
    references, pointers = routes
    if not closure.can_rebase_all(pointers):
        return None
    routed_references = _rebased_references(
        references,
        pointers=pointers,
        closure=closure,
    )
    if routed_references is None:
        return None
    return {**copy_json(row), "evidenceRefs": routed_references}


def _projected_routes(
    row: Mapping[str, Any],
    *,
    canonical_row: Mapping[str, Any],
) -> tuple[list[Any], list[str]] | None:
    references = row.get("evidenceRefs")
    canonical_references = canonical_row.get("evidenceRefs")
    if (
        not isinstance(references, list)
        or not references
        or not isinstance(canonical_references, list)
    ):
        return None
    canonical_routes = {
        (reference.get("type"), reference.get("pointer"))
        for reference in canonical_references
        if isinstance(reference, Mapping)
    }
    pointers: list[str] = []
    for reference in references:
        if not isinstance(reference, Mapping):
            return None
        pointer = reference.get("pointer")
        if (
            not isinstance(pointer, str)
            or (
                reference.get("type"),
                pointer,
            )
            not in canonical_routes
        ):
            return None
        pointers.append(pointer)
    return references, pointers


def _rebased_references(
    references: list[Any],
    *,
    pointers: list[str],
    closure: EvidenceClosure,
) -> list[dict[str, Any]] | None:
    routed: list[dict[str, Any]] = []
    for reference, pointer in zip(references, pointers, strict=True):
        routed_pointer = closure.rebase(pointer)
        if routed_pointer is None or not isinstance(reference, Mapping):
            return None
        routed.append(
            {
                **copy_json(reference),
                "pointer": routed_pointer,
            }
        )
    return routed


def _canonical_routes_valid(
    row: Mapping[str, Any],
    *,
    canonical_sections: Mapping[str, Any],
) -> bool:
    identity = row.get("id")
    target_module = row.get("targetModule")
    references = row.get("evidenceRefs")
    if (
        not isinstance(identity, str)
        or not isinstance(target_module, str)
        or not isinstance(references, list)
    ):
        return False
    report = {"sections": canonical_sections}
    if not all(
        _canonical_reference_valid(
            reference,
            report=report,
            boundary_id=identity,
        )
        for reference in references
    ):
        return False
    inventory_ref = _single_inventory_reference(references)
    if inventory_ref is None:
        return False
    return _inventory_reference_valid(
        inventory_ref,
        target_module=target_module,
        report=report,
    ) and _unique_membership_owner(
        canonical_sections,
        target_module=target_module,
    )


def _canonical_reference_valid(
    reference: Any,
    *,
    report: Mapping[str, Any],
    boundary_id: str,
) -> bool:
    pointer = reference.get("pointer") if isinstance(reference, Mapping) else None
    if not isinstance(pointer, str) or not pointer.startswith("#/sections/"):
        return False
    owner = _resolved_owner(report, pointer)
    if owner is None:
        return False
    return reference.get("type") != "source" or (
        isinstance(owner, Mapping) and owner.get("id") == boundary_id
    )


def _single_inventory_reference(
    references: list[Any],
) -> Mapping[str, Any] | None:
    candidates = [
        reference
        for reference in references
        if isinstance(reference, Mapping)
        and reference.get("type") == "source_index_inventory"
    ]
    return candidates[0] if len(candidates) == 1 else None


def _inventory_reference_valid(
    reference: Mapping[str, Any],
    *,
    target_module: str,
    report: Mapping[str, Any],
) -> bool:
    pointer = reference.get("pointer")
    membership = _resolved_owner(report, pointer) if isinstance(pointer, str) else None
    if (
        reference.get("module") != target_module
        or not isinstance(membership, Mapping)
        or membership.get("module") != target_module
    ):
        return False
    fields = (
        ("fingerprint", "sourceIndexFingerprint"),
        ("present", "present"),
        ("indexEntryStatus", "indexEntryStatus"),
    )
    return all(
        reference.get(reference_field) == membership.get(membership_field)
        for reference_field, membership_field in fields
    )


def _resolved_owner(
    report: Mapping[str, Any],
    pointer: str,
) -> Any | None:
    try:
        return resolve_local_json_pointer(report, pointer)
    except (IndexError, KeyError, TypeError, ValueError):
        return None


def _unique_membership_owner(
    canonical_sections: Mapping[str, Any],
    *,
    target_module: str,
) -> bool:
    dag = canonical_sections.get("module_dag")
    source_index = dag.get("source_index") if isinstance(dag, Mapping) else None
    membership = (
        source_index.get("boundaryMembershipEvidence")
        if isinstance(source_index, Mapping)
        else None
    )
    return (
        isinstance(membership, list)
        and sum(
            isinstance(row, Mapping) and row.get("module") == target_module
            for row in membership
        )
        == 1
    )


def _unique_rows_by_id(value: list[Any]) -> dict[str, Mapping[str, Any]]:
    rows: dict[str, Mapping[str, Any]] = {}
    ambiguous: set[str] = set()
    for row in value:
        identity = row.get("id") if isinstance(row, Mapping) else None
        if not isinstance(identity, str) or not identity:
            continue
        if identity in rows:
            ambiguous.add(identity)
        else:
            rows[identity] = row
    return {
        identity: row for identity, row in rows.items() if identity not in ambiguous
    }


def _refresh_boundary_ledger(
    canonical: list[Any],
    projected: list[Any],
    *,
    integrity_omitted: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> None:
    _prune_exact_ledger(omissions, strata, _IMPORT_BOUNDARY_POINTER)
    _record_split_omission(
        omissions,
        pointer=_IMPORT_BOUNDARY_POINTER,
        total=len(canonical),
        visible=len(projected),
        integrity_omitted=integrity_omitted,
    )
    strata.extend(
        selection_strata(
            _mapping_rows(canonical),
            _mapping_rows(projected),
            pointer=_IMPORT_BOUNDARY_POINTER,
        )
    )


def _refresh_changed_collection_ledgers(
    changed: Mapping[str, tuple[Any, Any]],
    *,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> None:
    for pointer, (canonical, projected) in sorted(changed.items()):
        _prune_exact_ledger(omissions, strata, pointer)
        if not isinstance(canonical, (list, Mapping)) or not isinstance(
            projected,
            (list, Mapping),
        ):
            continue
        _record_omission(
            omissions,
            pointer=pointer,
            total=len(canonical),
            visible=len(projected),
        )
        if isinstance(canonical, list) and isinstance(projected, list):
            strata.extend(
                selection_strata(
                    _mapping_rows(canonical),
                    _mapping_rows(projected),
                    pointer=pointer,
                )
            )


def _prune_exact_ledger(
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    pointer: str,
) -> None:
    omissions[:] = [row for row in omissions if row.get("pointer") != pointer]
    strata[:] = [row for row in strata if row.get("pointer") != pointer]


def _record_split_omission(
    omissions: list[dict[str, Any]],
    *,
    pointer: str,
    total: int,
    visible: int,
    integrity_omitted: int,
) -> None:
    omitted = max(total - visible, 0)
    integrity = min(max(integrity_omitted, 0), omitted)
    _record_omission(
        omissions,
        pointer=pointer,
        total=omitted - integrity,
        visible=0,
    )
    _record_omission(
        omissions,
        pointer=pointer,
        total=integrity,
        visible=0,
        reason="projection_evidence_unavailable",
    )


def _record_omission(
    omissions: list[dict[str, Any]],
    *,
    pointer: str,
    total: int,
    visible: int,
    reason: str = "projection_collection_limit",
) -> None:
    if total > visible:
        omissions.append(
            {
                "pointer": pointer,
                "reason": reason,
                "omitted_count": total - visible,
            }
        )


def _mapping_rows(value: list[Any]) -> list[Mapping[str, Any]]:
    return [row for row in value if isinstance(row, Mapping)]


__all__ = ["reconcile_intrinsic_evidence_routes"]
