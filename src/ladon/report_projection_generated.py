"""Stable-ID reconciliation for projected generated-family relationships."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from ladon.report_contract import copy_json
from ladon.report_projection_routes import (
    mapping_rows,
    pointer_is_within,
    selection_strata,
)


GENERATED_FAMILY_BASE = "#/sections/module_dag/generated_family_candidates"
BoundValue = Callable[..., Any]


@dataclass(frozen=True)
class _SurfaceInputs:
    """Validated canonical and projected generated-family owners."""

    canonical_dag: Mapping[str, Any]
    projected_dag: Mapping[str, Any]
    canonical: Mapping[str, Any]
    projected: Mapping[str, Any]
    canonical_candidates: list[Mapping[str, Any]]
    canonical_partitions: list[Mapping[str, Any]]
    retained_candidates: list[Mapping[str, Any]]


def reconcile_generated_family_routes(
    canonical_sections: Mapping[str, Any],
    projected_sections: Mapping[str, Any],
    *,
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    bound_value: BoundValue,
) -> dict[str, Any]:
    """Reindex retained candidate relationships from stable identities."""

    inputs = _surface_inputs(canonical_sections, projected_sections)
    if inputs is None:
        return dict(projected_sections)
    retained_partitions = _retained_candidate_partitions(
        inputs.canonical_partitions,
        required=_required_partition_ids(inputs.retained_candidates),
        limit=limit,
    )
    candidate_pointer = f"{GENERATED_FAMILY_BASE}/candidates"
    partition_pointer = f"{GENERATED_FAMILY_BASE}/partitions"
    producer_pointer = f"{GENERATED_FAMILY_BASE}/producerRegistry/producers"
    _prune_relation_ledgers(
        omissions,
        strata,
        pointers=(candidate_pointer, partition_pointer, producer_pointer),
    )
    candidates = _project_relation_rows(
        inputs.retained_candidates,
        pointer=candidate_pointer,
        limit=limit,
        omissions=omissions,
        strata=strata,
        bound_value=bound_value,
    )
    candidates, module_metadata = _align_candidate_members(
        inputs.canonical_dag,
        inputs.projected_dag,
        inputs.canonical_candidates,
        candidates,
        omissions=omissions,
        strata=strata,
    )
    partitions = _project_relation_rows(
        retained_partitions,
        pointer=partition_pointer,
        limit=limit,
        omissions=omissions,
        strata=strata,
        bound_value=bound_value,
    )
    _record_population(
        inputs.canonical_candidates,
        candidates,
        pointer=candidate_pointer,
        omissions=omissions,
        strata=strata,
    )
    _record_population(
        inputs.canonical_partitions,
        partitions,
        pointer=partition_pointer,
        omissions=omissions,
        strata=strata,
    )
    producers = _reindexed_candidate_producers(
        inputs.canonical,
        candidates,
        partitions,
        pointer=producer_pointer,
        limit=limit,
        omissions=omissions,
        strata=strata,
        bound_value=bound_value,
    )
    result = _replace_generated_surface(
        projected_sections,
        inputs,
        candidates=candidates,
        partitions=partitions,
        producers=producers,
        module_metadata=module_metadata,
    )
    return _reconcile_generated_family_region(
        canonical_sections,
        result,
        producers=producers,
        limit=limit,
        omissions=omissions,
        strata=strata,
        bound_value=bound_value,
    )


def _surface_inputs(
    canonical_sections: Mapping[str, Any],
    projected_sections: Mapping[str, Any],
) -> _SurfaceInputs | None:
    envelopes = _surface_envelopes(canonical_sections, projected_sections)
    if envelopes is None:
        return None
    canonical_dag, projected_dag, canonical, projected = envelopes
    canonical_candidates = _identified_rows(canonical.get("candidates"))
    canonical_partitions = _identified_rows(canonical.get("partitions"))
    projected_candidates = _identified_rows(projected.get("candidates"))
    if None in (
        canonical_candidates,
        canonical_partitions,
        projected_candidates,
    ):
        return None
    assert canonical_candidates is not None
    assert canonical_partitions is not None
    assert projected_candidates is not None
    retained = _retained_candidates(canonical_candidates, projected_candidates)
    return _SurfaceInputs(
        canonical_dag,
        projected_dag,
        canonical,
        projected,
        canonical_candidates,
        canonical_partitions,
        retained,
    )


def _surface_envelopes(
    canonical_sections: Mapping[str, Any],
    projected_sections: Mapping[str, Any],
) -> (
    tuple[
        Mapping[str, Any],
        Mapping[str, Any],
        Mapping[str, Any],
        Mapping[str, Any],
    ]
    | None
):
    canonical_dag = canonical_sections.get("module_dag")
    projected_dag = projected_sections.get("module_dag")
    if not isinstance(canonical_dag, Mapping) or not isinstance(
        projected_dag,
        Mapping,
    ):
        return None
    canonical = canonical_dag.get("generated_family_candidates")
    projected = projected_dag.get("generated_family_candidates")
    if not isinstance(canonical, Mapping) or not isinstance(projected, Mapping):
        return None
    return canonical_dag, projected_dag, canonical, projected


def _identified_rows(value: Any) -> list[Mapping[str, Any]] | None:
    """Return mapping rows with unique stable IDs, or reject malformed input."""

    if not isinstance(value, list):
        return None
    rows = [
        row
        for row in value
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    ]
    if len(rows) != len(value):
        return None
    return rows if len({row["id"] for row in rows}) == len(rows) else None


def _retained_candidates(
    canonical: list[Mapping[str, Any]],
    projected: list[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    by_id = {str(row["id"]): row for row in canonical}
    return [
        by_id[identity]
        for row in projected
        for identity in [str(row["id"])]
        if identity in by_id
    ]


def _required_partition_ids(
    candidates: list[Mapping[str, Any]],
) -> set[str]:
    return {
        str(row["partitionId"])
        for row in candidates
        if isinstance(row.get("partitionId"), str)
    }


def _retained_candidate_partitions(
    canonical: list[Mapping[str, Any]],
    *,
    required: set[str],
    limit: int,
) -> list[Mapping[str, Any]]:
    selected_ids = set(required)
    for row in canonical:
        if len(selected_ids) >= limit:
            break
        selected_ids.add(str(row["id"]))
    return [row for row in canonical if str(row["id"]) in selected_ids]


def _prune_relation_ledgers(
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    *,
    pointers: tuple[str, ...],
) -> None:
    for pointer in pointers:
        _prune_projection_ledger(omissions, strata, pointer=pointer)


def _project_relation_rows(
    rows: list[Mapping[str, Any]],
    *,
    pointer: str,
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    bound_value: BoundValue,
) -> list[dict[str, Any]]:
    return [
        _project_relation_row(
            row,
            pointer=f"{pointer}/{index}",
            limit=limit,
            omissions=omissions,
            strata=strata,
            bound_value=bound_value,
        )
        for index, row in enumerate(rows)
    ]


def _project_relation_row(
    row: Mapping[str, Any],
    *,
    pointer: str,
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    bound_value: BoundValue,
) -> dict[str, Any]:
    projected = bound_value(
        row,
        limit=limit,
        pointer=pointer,
        omissions=omissions,
        strata=strata,
    )
    if not isinstance(projected, dict):
        raise AssertionError("generated-family relation row did not remain an object")
    projected["canonicalRef"] = pointer
    return projected


def _record_population(
    canonical: list[Mapping[str, Any]],
    selected: list[Mapping[str, Any]],
    *,
    pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> None:
    _record_population_omission(
        omissions,
        pointer=pointer,
        total=len(canonical),
        visible=len(selected),
    )
    strata.extend(selection_strata(canonical, selected, pointer=pointer))


def _align_candidate_members(
    canonical_dag: Mapping[str, Any],
    projected_dag: Mapping[str, Any],
    canonical_candidates: list[Mapping[str, Any]],
    candidates: list[Mapping[str, Any]],
    *,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> tuple[list[Mapping[str, Any]], Mapping[str, Any] | None]:
    """Retain exact metadata owners for every visible candidate member."""

    canonical_metadata = canonical_dag.get("module_metadata")
    projected_metadata = projected_dag.get("module_metadata")
    if not isinstance(canonical_metadata, Mapping) or not isinstance(
        projected_metadata,
        Mapping,
    ):
        return candidates, None
    canonical_by_id = {
        str(row["id"]): row
        for row in canonical_candidates
        if isinstance(row.get("id"), str)
    }
    metadata = dict(projected_metadata)
    aligned: list[Mapping[str, Any]] = []
    for candidate in candidates:
        raw = canonical_by_id.get(str(candidate.get("id", "")))
        rebuilt = _candidate_with_exact_members(
            candidate,
            raw,
            canonical_metadata=canonical_metadata,
            metadata=metadata,
            index=len(aligned),
            omissions=omissions,
            strata=strata,
        )
        if rebuilt is not None:
            aligned.append(rebuilt)
    pointer = "#/sections/module_dag/module_metadata"
    _prune_projection_ledger(omissions, strata, pointer=pointer)
    _record_population_omission(
        omissions,
        pointer=pointer,
        total=len(canonical_metadata),
        visible=len(metadata),
    )
    return aligned, metadata


def _candidate_with_exact_members(
    candidate: Mapping[str, Any],
    canonical: Mapping[str, Any] | None,
    *,
    canonical_metadata: Mapping[str, Any],
    metadata: dict[str, Any],
    index: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Rebuild one candidate's parallel member identities and references."""

    if canonical is None:
        return None
    if not isinstance(canonical.get("memberRefs"), list):
        return dict(candidate)
    identities = _candidate_member_identities(candidate)
    if identities is None:
        return None
    if not _retain_member_metadata(
        identities,
        canonical=canonical_metadata,
        projected=metadata,
    ):
        return None
    pointer = f"{GENERATED_FAMILY_BASE}/candidates/{index}"
    _refresh_candidate_member_ledgers(
        canonical,
        visible=len(identities),
        candidate_pointer=pointer,
        omissions=omissions,
        strata=strata,
    )
    return {
        **candidate,
        "canonicalRef": pointer,
        "memberIds": identities,
        "memberRefs": [
            f"#/sections/module_dag/module_metadata/{_pointer_token(identity)}"
            for identity in identities
        ],
    }


def _candidate_member_identities(
    candidate: Mapping[str, Any],
) -> list[str] | None:
    """Return unique stable IDs for every retained embedded member row."""

    members = mapping_rows(candidate.get("members"))
    identities = [
        str(row.get("id") or row.get("module"))
        for row in members
        if isinstance(row.get("id") or row.get("module"), str)
    ]
    if len(identities) != len(members) or len(set(identities)) != len(identities):
        return None
    return identities


def _retain_member_metadata(
    identities: list[str],
    *,
    canonical: Mapping[str, Any],
    projected: dict[str, Any],
) -> bool:
    """Copy every exact member owner needed by retained candidate routes."""

    if any(identity not in canonical for identity in identities):
        return False
    for identity in identities:
        projected.setdefault(identity, copy_json(canonical[identity]))
    return True


def _refresh_candidate_member_ledgers(
    canonical: Mapping[str, Any],
    *,
    visible: int,
    candidate_pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> None:
    """Replace independent member-ID/reference projection ledgers."""

    for field in ("memberIds", "memberRefs"):
        _refresh_member_ledger(
            canonical,
            field,
            visible=visible,
            pointer=f"{candidate_pointer}/{field}",
            omissions=omissions,
            strata=strata,
        )


def _refresh_member_ledger(
    canonical: Mapping[str, Any],
    field: str,
    *,
    visible: int,
    pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> None:
    _prune_projection_ledger(omissions, strata, pointer=pointer)
    raw = canonical.get(field)
    total = len(raw) if isinstance(raw, list) else visible
    _record_population_omission(
        omissions,
        pointer=pointer,
        total=total,
        visible=visible,
    )


def _reindexed_candidate_producers(
    canonical_surface: Mapping[str, Any],
    candidates: list[Mapping[str, Any]],
    partitions: list[Mapping[str, Any]],
    *,
    pointer: str,
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    bound_value: BoundValue,
) -> dict[str, Any]:
    canonical = _registration_producers(canonical_surface.get("producerRegistry"))
    if canonical is None:
        return {}
    partition_indexes = {str(row["id"]): index for index, row in enumerate(partitions)}
    producers: dict[str, Any] = {}
    for candidate_index, candidate in enumerate(candidates):
        projected = _candidate_producer(
            canonical,
            candidate,
            candidate_index=candidate_index,
            partitions=partitions,
            partition_indexes=partition_indexes,
            pointer=pointer,
            limit=limit,
            omissions=omissions,
            strata=strata,
            bound_value=bound_value,
        )
        if projected is not None:
            producer_id, row = projected
            producers[producer_id] = row
    _record_population_omission(
        omissions,
        pointer=pointer,
        total=len(canonical),
        visible=len(producers),
    )
    return producers


def _candidate_producer(
    canonical: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    candidate_index: int,
    partitions: list[Mapping[str, Any]],
    partition_indexes: Mapping[str, int],
    pointer: str,
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    bound_value: BoundValue,
) -> tuple[str, dict[str, Any]] | None:
    identity = str(candidate["id"])
    producer_id = f"{identity}.review"
    raw = canonical.get(producer_id)
    partition_id = candidate.get("partitionId")
    if not isinstance(raw, Mapping) or not isinstance(partition_id, str):
        return None
    partition_index = partition_indexes.get(partition_id)
    if partition_index is None:
        return None
    feature_indexes = _feature_indexes(partitions[partition_index])
    feature_ids = _required_feature_ids(candidate, feature_indexes)
    if feature_ids is None:
        return None
    projected = bound_value(
        raw,
        limit=limit,
        pointer=f"{pointer}/{_pointer_token(producer_id)}",
        omissions=omissions,
        strata=strata,
    )
    if not isinstance(projected, dict):
        return None
    _prune_projection_ledger(
        omissions,
        strata,
        pointer=(f"{pointer}/{_pointer_token(producer_id)}/evidenceRefs"),
    )
    projected["evidenceRefs"] = _candidate_evidence_refs(
        candidate_index,
        partition_index,
        feature_ids,
        feature_indexes,
    )
    return producer_id, projected


def _feature_indexes(partition: Mapping[str, Any]) -> dict[str, int]:
    return {
        str(row["id"]): index
        for index, row in enumerate(mapping_rows(partition.get("features")))
        if isinstance(row.get("id"), str)
    }


def _required_feature_ids(
    candidate: Mapping[str, Any],
    feature_indexes: Mapping[str, int],
) -> tuple[str, str] | None:
    values = (
        candidate.get("importFeatureId"),
        candidate.get("lexicalFeatureId"),
    )
    if any(
        not isinstance(value, str) or value not in feature_indexes for value in values
    ):
        return None
    return str(values[0]), str(values[1])


def _candidate_evidence_refs(
    candidate_index: int,
    partition_index: int,
    feature_ids: tuple[str, str],
    feature_indexes: Mapping[str, int],
) -> list[str]:
    candidate_ref = f"{GENERATED_FAMILY_BASE}/candidates/{candidate_index}"
    partition_ref = f"{GENERATED_FAMILY_BASE}/partitions/{partition_index}"
    return [
        candidate_ref,
        partition_ref,
        f"{candidate_ref}/members",
        *[
            f"{partition_ref}/features/{feature_indexes[feature_id]}"
            for feature_id in feature_ids
        ],
    ]


def _registration_producers(value: Any) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    producers = value.get("producers")
    return producers if isinstance(producers, Mapping) else None


def _replace_generated_surface(
    sections: Mapping[str, Any],
    inputs: _SurfaceInputs,
    *,
    candidates: list[Mapping[str, Any]],
    partitions: list[Mapping[str, Any]],
    producers: Mapping[str, Any],
    module_metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    raw_registry = inputs.projected.get("producerRegistry")
    registry = dict(raw_registry) if isinstance(raw_registry, Mapping) else {}
    surface = {
        **inputs.projected,
        "candidates": candidates,
        "partitions": partitions,
        "producerRegistry": {**registry, "producers": producers},
    }
    dag = {**inputs.projected_dag, "generated_family_candidates": surface}
    if module_metadata is not None:
        dag["module_metadata"] = module_metadata
    return {**sections, "module_dag": dag}


def _reconcile_generated_family_region(
    canonical_sections: Mapping[str, Any],
    projected_sections: Mapping[str, Any],
    *,
    producers: Mapping[str, Any],
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    bound_value: BoundValue,
) -> dict[str, Any]:
    region_inputs = _generated_region_inputs(
        canonical_sections,
        projected_sections,
    )
    if region_inputs is None:
        return dict(projected_sections)
    canonical_signals, regions = region_inputs
    for index, region in enumerate(regions):
        if not _is_generated_region(region):
            continue
        regions[index] = _project_generated_region(
            region,
            region_index=index,
            canonical_signals=canonical_signals,
            producers=producers,
            limit=limit,
            omissions=omissions,
            strata=strata,
            bound_value=bound_value,
        )
    return {**projected_sections, "review_regions": regions}


def _generated_region_inputs(
    canonical_sections: Mapping[str, Any],
    projected_sections: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], list[Any]] | None:
    canonical_regions = canonical_sections.get("review_regions")
    projected_regions = projected_sections.get("review_regions")
    if not isinstance(canonical_regions, list) or not isinstance(
        projected_regions,
        list,
    ):
        return None
    canonical = next(
        (row for row in canonical_regions if _is_generated_region(row)),
        None,
    )
    if not isinstance(canonical, Mapping):
        return None
    signals = {
        str(row["id"]): row
        for row in mapping_rows(canonical.get("signals"))
        if isinstance(row.get("id"), str)
    }
    return signals, list(projected_regions)


def _is_generated_region(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and value.get("kind") == "generated_family_candidate_region"
    )


def _project_generated_region(
    region: Mapping[str, Any],
    *,
    region_index: int,
    canonical_signals: Mapping[str, Mapping[str, Any]],
    producers: Mapping[str, Any],
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    bound_value: BoundValue,
) -> dict[str, Any]:
    pointer = f"#/sections/review_regions/{region_index}/signals"
    _prune_projection_ledger(omissions, strata, pointer=pointer)
    selected = _project_generated_signals(
        canonical_signals,
        producers,
        pointer=pointer,
        limit=limit,
        omissions=omissions,
        strata=strata,
        bound_value=bound_value,
    )
    _record_population_omission(
        omissions,
        pointer=pointer,
        total=len(canonical_signals),
        visible=len(selected),
    )
    strata.extend(
        selection_strata(
            list(canonical_signals.values()),
            selected,
            pointer=pointer,
        )
    )
    return {**region, "signals": selected, "signal_count": len(selected)}


def _project_generated_signals(
    canonical: Mapping[str, Mapping[str, Any]],
    producers: Mapping[str, Any],
    *,
    pointer: str,
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    bound_value: BoundValue,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for identity in producers:
        raw = canonical.get(identity)
        producer = producers[identity]
        if raw is None or not isinstance(producer, Mapping):
            continue
        row = _project_generated_signal(
            raw,
            producer,
            pointer=f"{pointer}/{len(selected)}",
            limit=limit,
            omissions=omissions,
            strata=strata,
            bound_value=bound_value,
        )
        if row is not None:
            selected.append(row)
    return selected


def _project_generated_signal(
    raw: Mapping[str, Any],
    producer: Mapping[str, Any],
    *,
    pointer: str,
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    bound_value: BoundValue,
) -> dict[str, Any] | None:
    evidence_refs = producer.get("evidenceRefs")
    if not isinstance(evidence_refs, list):
        return None
    projected = bound_value(
        raw,
        limit=limit,
        pointer=pointer,
        omissions=omissions,
        strata=strata,
    )
    if not isinstance(projected, dict):
        return None
    _prune_projection_ledger(
        omissions,
        strata,
        pointer=f"{pointer}/evidenceRefs",
    )
    projected["evidenceRefs"] = list(evidence_refs)
    projected["evidenceRefCount"] = len(evidence_refs)
    projected["omittedEvidenceRefCount"] = 0
    return projected


def _prune_projection_ledger(
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    *,
    pointer: str,
) -> None:
    omissions[:] = [
        row for row in omissions if not pointer_is_within(row["pointer"], pointer)
    ]
    strata[:] = [
        row for row in strata if not pointer_is_within(row["pointer"], pointer)
    ]


def _record_population_omission(
    omissions: list[dict[str, Any]],
    *,
    pointer: str,
    total: int,
    visible: int,
) -> None:
    if total > visible:
        omissions.append(
            {
                "pointer": pointer,
                "reason": "projection_collection_limit",
                "omitted_count": total - visible,
            }
        )


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


__all__ = ["reconcile_generated_family_routes"]
