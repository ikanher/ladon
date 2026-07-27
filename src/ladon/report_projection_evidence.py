"""Route-safe evidence closure for projected producer registrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ladon.report_contract import copy_json
from ladon.report_projection_evidence_closure import (
    EvidenceClosure,
    local_pointer_tokens,
    pointer as local_pointer,
)
from ladon.report_projection_routes import selection_strata


_REGISTRY_PATHS = (
    ("module_dag", "declaration_integrity", "producerRegistrations"),
    ("module_dag", "architecture", "producerRegistrations"),
    ("module_dag", "architectureProducerRegistrations"),
    ("module_dag", "architecture_producer_registrations"),
    ("module_dag", "auditProducerRegistrations"),
    ("module_dag", "resourceProducerRegistrations"),
    ("module_dag", "producerRegistrations"),
)
_FINDING_OWNER_REGISTRY_PATHS = frozenset(
    {
        ("module_dag", "architectureProducerRegistrations"),
        ("module_dag", "architecture_producer_registrations"),
    }
)


@dataclass(frozen=True)
class _ProducerOwner:
    """Canonical registry owner for one unambiguous producer identity."""

    path: tuple[str, ...]
    row: Mapping[str, Any]


@dataclass(frozen=True)
class _ProducerIndex:
    """Unambiguous owners plus every finite registry claim by identity."""

    owners: Mapping[str, _ProducerOwner]
    registrations: Mapping[str, frozenset[tuple[str, ...]]]


def reconcile_registered_evidence_routes(
    canonical_sections: Mapping[str, Any],
    projected_sections: Mapping[str, Any],
    *,
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> dict[str, Any]:
    """Align retained region signals, registries, and all local evidence refs."""

    projected = (
        projected_sections
        if isinstance(projected_sections, dict)
        else dict(projected_sections)
    )
    index = _producer_index(canonical_sections)
    if not index.registrations:
        return projected
    closure = EvidenceClosure(
        canonical=canonical_sections,
        projected=projected,
        changed={},
        limit=limit,
    )
    selected = {path: {} for path in _REGISTRY_PATHS}
    integrity_failures = {path: set() for path in _REGISTRY_PATHS}
    for identity, paths in index.registrations.items():
        if identity not in index.owners:
            for path in paths:
                integrity_failures[path].add(identity)
    _reconcile_registered_regions(
        canonical_sections,
        closure,
        index=index,
        selected=selected,
        integrity_failures=integrity_failures,
        omissions=omissions,
        strata=strata,
    )
    _replace_projected_registries(
        canonical_sections,
        projected,
        selected=selected,
        integrity_failures=integrity_failures,
        omissions=omissions,
        strata=strata,
    )
    _refresh_changed_collection_ledgers(
        closure.changed,
        omissions=omissions,
        strata=strata,
    )
    return projected


def _producer_index(
    canonical_sections: Mapping[str, Any],
) -> _ProducerIndex:
    selected: dict[str, _ProducerOwner] = {}
    conflicts: set[str] = set()
    registrations: dict[str, set[tuple[str, ...]]] = {}
    for path in _REGISTRY_PATHS:
        producers = _registry_producers(canonical_sections, path)
        for identity, row in sorted(producers.items()):
            if not isinstance(identity, str):
                continue
            registrations.setdefault(identity, set()).add(path)
            if not isinstance(row, Mapping):
                conflicts.add(identity)
                continue
            owner = _ProducerOwner(path=path, row=row)
            existing = selected.get(identity)
            if existing is not None and existing != owner:
                conflicts.add(identity)
            else:
                selected[identity] = owner
    return _ProducerIndex(
        owners={
            identity: owner
            for identity, owner in selected.items()
            if identity not in conflicts
        },
        registrations={
            identity: frozenset(paths) for identity, paths in registrations.items()
        },
    )


def _reconcile_registered_regions(
    canonical_sections: Mapping[str, Any],
    closure: EvidenceClosure,
    *,
    index: _ProducerIndex,
    selected: dict[tuple[str, ...], dict[str, Any]],
    integrity_failures: dict[tuple[str, ...], set[str]],
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> None:
    canonical_regions = _regions_by_id(canonical_sections.get("review_regions"))
    projected_regions = closure.projected.get("review_regions")
    if not isinstance(projected_regions, list):
        return
    for region_index, region in enumerate(projected_regions):
        if not isinstance(region, dict):
            continue
        if region.get("kind") == "generated_family_candidate_region":
            continue
        signals = region.get("signals")
        if not isinstance(signals, list):
            continue
        reconciled, integrity_omitted = _reconciled_signals(
            signals,
            closure=closure,
            index=index,
            selected=selected,
            integrity_failures=integrity_failures,
        )
        region["signals"] = reconciled
        region["signal_count"] = len(reconciled)
        canonical_region = canonical_regions.get(str(region.get("id", "")))
        _refresh_signal_ledger(
            canonical_region,
            reconciled,
            pointer=f"#/sections/review_regions/{region_index}/signals",
            integrity_omitted=integrity_omitted,
            omissions=omissions,
            strata=strata,
        )


def _reconciled_signals(
    signals: list[Any],
    *,
    closure: EvidenceClosure,
    index: _ProducerIndex,
    selected: dict[tuple[str, ...], dict[str, Any]],
    integrity_failures: dict[tuple[str, ...], set[str]],
) -> tuple[list[Any], int]:
    reconciled: list[Any] = []
    integrity_omitted = 0
    for signal in signals:
        identity = signal.get("id") if isinstance(signal, Mapping) else None
        if not isinstance(identity, str) or identity not in index.registrations:
            reconciled.append(signal)
            continue
        owner = index.owners.get(identity)
        if owner is None:
            integrity_omitted += 1
            continue
        producer = _reconciled_producer(
            owner.row,
            identity=identity,
            owner_path=owner.path,
            closure=closure,
        )
        if producer is None:
            integrity_failures[owner.path].add(identity)
            integrity_omitted += 1
            continue
        selected[owner.path][identity] = producer
        reconciled.append(_signal_with_evidence(signal, producer))
    return reconciled, integrity_omitted


def _reconciled_producer(
    value: Mapping[str, Any],
    *,
    identity: str,
    owner_path: tuple[str, ...],
    closure: EvidenceClosure,
) -> dict[str, Any] | None:
    references = value.get("evidenceRefs")
    if not isinstance(references, list) or not references:
        return None
    finding_owner = _canonical_finding_owner(
        identity,
        owner_path=owner_path,
        canonical_sections=closure.canonical,
    )
    if owner_path in _FINDING_OWNER_REGISTRY_PATHS and finding_owner is None:
        return None
    canonical_references: list[str] = []
    for reference in references:
        if not isinstance(reference, str):
            return None
        canonical_references.append(
            _finding_owner_reference(
                reference,
                finding_owner=finding_owner,
            )
        )
    if not closure.can_rebase_all(canonical_references):
        return None
    rebased: list[str] = []
    for canonical_reference in canonical_references:
        projected = closure.rebase(canonical_reference)
        if projected is None:
            return None
        rebased.append(projected)
    return {**copy_json(value), "evidenceRefs": list(dict.fromkeys(rebased))}


def _canonical_finding_owner(
    identity: str,
    *,
    owner_path: tuple[str, ...],
    canonical_sections: Mapping[str, Any],
) -> int | None:
    """Resolve a pre-canonical architecture registration by stable identity."""

    if owner_path not in _FINDING_OWNER_REGISTRY_PATHS:
        return None
    suffix = ".review"
    if not identity.endswith(suffix):
        return None
    stable_key = identity[: -len(suffix)]
    findings = canonical_sections.get("findings")
    if not stable_key or not isinstance(findings, list):
        return None
    matches = [
        index
        for index, row in enumerate(findings)
        if isinstance(row, Mapping) and row.get("stable_key") == stable_key
    ]
    return matches[0] if len(matches) == 1 else None


def _finding_owner_reference(
    reference: str,
    *,
    finding_owner: int | None,
) -> str:
    """Replace a stale findings index while preserving its nested suffix."""

    if finding_owner is None:
        return reference
    tokens = local_pointer_tokens(reference)
    if tokens is None or len(tokens) < 2 or tokens[0] != "findings":
        return reference
    try:
        index = int(tokens[1])
    except ValueError:
        return reference
    if index < 0 or str(index) != tokens[1]:
        return reference
    return local_pointer(["findings", str(finding_owner), *tokens[2:]])


def _signal_with_evidence(
    signal: Mapping[str, Any],
    producer: Mapping[str, Any],
) -> dict[str, Any]:
    references = list(producer["evidenceRefs"])
    return {
        **copy_json(signal),
        "evidenceRefs": references,
        "evidenceRefCount": len(references),
        "omittedEvidenceRefCount": 0,
    }


def _replace_projected_registries(
    canonical_sections: Mapping[str, Any],
    projected_sections: dict[str, Any],
    *,
    selected: Mapping[tuple[str, ...], Mapping[str, Any]],
    integrity_failures: Mapping[tuple[str, ...], set[str]],
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> None:
    for path in _REGISTRY_PATHS:
        canonical = _mapping_at(canonical_sections, path)
        projected = _mutable_mapping_at(projected_sections, path)
        if canonical is None or projected is None:
            continue
        canonical_producers = canonical.get("producers")
        if not isinstance(canonical_producers, Mapping):
            continue
        producers = dict(selected[path])
        projected["producers"] = producers
        pointer = (
            f"#/sections/{'/'.join(_pointer_token(part) for part in path)}/producers"
        )
        _prune_ledger_subtree(omissions, strata, pointer)
        _record_split_omission(
            omissions,
            pointer=pointer,
            total=len(canonical_producers),
            visible=len(producers),
            integrity_omitted=len(integrity_failures[path]),
        )


def _refresh_signal_ledger(
    canonical_region: Mapping[str, Any] | None,
    selected: list[Any],
    *,
    pointer: str,
    integrity_omitted: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> None:
    _prune_exact_ledger(omissions, strata, pointer)
    _prune_evidence_ref_ledgers(omissions, strata, pointer)
    canonical = (
        canonical_region.get("signals")
        if isinstance(canonical_region, Mapping)
        else None
    )
    if not isinstance(canonical, list):
        return
    _record_split_omission(
        omissions,
        pointer=pointer,
        total=len(canonical),
        visible=len(selected),
        integrity_omitted=integrity_omitted,
    )
    strata.extend(
        selection_strata(
            _mapping_rows(canonical),
            _mapping_rows(selected),
            pointer=pointer,
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


def refresh_evidence_closure_ledgers(
    changed: Mapping[str, tuple[Any, Any]],
    *,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> None:
    """Refresh projection accounting after another route-safe closure pass."""

    _refresh_changed_collection_ledgers(
        changed,
        omissions=omissions,
        strata=strata,
    )


def _registry_producers(
    sections: Mapping[str, Any],
    path: tuple[str, ...],
) -> Mapping[str, Any]:
    registry = _mapping_at(sections, path)
    producers = registry.get("producers") if registry is not None else None
    return producers if isinstance(producers, Mapping) else {}


def _mapping_at(
    value: Mapping[str, Any],
    path: tuple[str, ...],
) -> Mapping[str, Any] | None:
    current: Any = value
    for token in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(token)
    return current if isinstance(current, Mapping) else None


def _mutable_mapping_at(
    value: dict[str, Any],
    path: tuple[str, ...],
) -> dict[str, Any] | None:
    current: Any = value
    for token in path:
        if not isinstance(current, dict):
            return None
        current = current.get(token)
    return current if isinstance(current, dict) else None


def _regions_by_id(value: Any) -> dict[str, Mapping[str, Any]]:
    if not isinstance(value, list):
        return {}
    return {
        str(row["id"]): row
        for row in value
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    }


def _mapping_rows(value: list[Any]) -> list[Mapping[str, Any]]:
    return [row for row in value if isinstance(row, Mapping)]


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _prune_ledger_subtree(
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    pointer: str,
) -> None:
    omissions[:] = [
        row for row in omissions if not _pointer_is_within(row.get("pointer"), pointer)
    ]
    strata[:] = [
        row for row in strata if not _pointer_is_within(row.get("pointer"), pointer)
    ]


def _prune_exact_ledger(
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    pointer: str,
) -> None:
    omissions[:] = [row for row in omissions if row.get("pointer") != pointer]
    strata[:] = [row for row in strata if row.get("pointer") != pointer]


def _prune_evidence_ref_ledgers(
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    pointer: str,
) -> None:
    marker = "/evidenceRefs"
    omissions[:] = [
        row
        for row in omissions
        if not (
            _pointer_is_within(row.get("pointer"), pointer)
            and marker in str(row.get("pointer"))[len(pointer) :]
        )
    ]
    strata[:] = [
        row
        for row in strata
        if not (
            _pointer_is_within(row.get("pointer"), pointer)
            and marker in str(row.get("pointer"))[len(pointer) :]
        )
    ]


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
    selection = omitted - integrity
    _record_omission(
        omissions,
        pointer=pointer,
        total=selection,
        visible=0,
    )
    _record_omission(
        omissions,
        pointer=pointer,
        total=integrity,
        visible=0,
        reason="projection_evidence_unavailable",
    )


def _pointer_is_within(candidate: Any, parent: str) -> bool:
    return isinstance(candidate, str) and (
        candidate == parent or candidate.startswith(f"{parent}/")
    )


__all__ = [
    "reconcile_registered_evidence_routes",
    "refresh_evidence_closure_ledgers",
]
