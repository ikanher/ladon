"""Bounded summary/review projections over canonical report sections."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping, Sequence

from ladon.coverage import CollectionCoverage, CoverageCause
from ladon.report_contract import copy_json
from ladon.report_declaration_compaction import (
    compact_declaration_rows,
    is_compact_declaration_container,
    is_raw_declaration_container,
)
from ladon.report_projection_evidence import (
    reconcile_registered_evidence_routes,
    refresh_evidence_closure_ledgers,
)
from ladon.report_projection_generated import (
    reconcile_generated_family_routes,
)
from ladon.report_projection_inspection import select_inspection_signals
from ladon.report_projection_intrinsic_evidence import (
    reconcile_intrinsic_evidence_routes,
)
from ladon.report_projection_routes import (
    INSPECTION_REGION_ROUTES,
    inspection_owner_pointers,
    inspection_region_noun,
    mapping_rows,
    pointer_is_within,
    regions_by_id,
    routed_inspection_signal,
    selection_strata,
)
from ladon.report_stratification import stratified_selection


_RECORD_SHAPE_KEYS = frozenset(
    {
        "artifactKind",
        "command",
        "declaration",
        "id",
        "kind",
        "module",
        "name",
        "schema",
        "schemaVersion",
        "start",
        "status",
        "summary",
    }
)
_GENERATED_FAMILY_BASE = "#/sections/module_dag/generated_family_candidates"
_INLINE_COVERAGE_FIELDS = (
    ("members", "memberCoverage"),
    ("features", "featureCoverage"),
    ("representatives", "representativeCoverage"),
)


def project_sections(
    sections: Mapping[str, Any],
    *,
    projection: str,
    summary_item_limit: int,
    review_item_limit: int,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    int | None,
    list[dict[str, Any]],
]:
    """Materialize one explicit projection and its omission ledger."""

    omissions: list[dict[str, Any]] = []
    strata: list[dict[str, Any]] = []
    projected = {
        name: _project_section(
            name,
            sections[name],
            projection=projection,
            summary_item_limit=summary_item_limit,
            review_item_limit=review_item_limit,
            omissions=omissions,
            strata=strata,
        )
        for name in sorted(sections)
    }
    item_limit = {
        "summary": summary_item_limit,
        "review": review_item_limit,
        "full": None,
    }[projection]
    if projection == "review":
        projected = reconcile_intrinsic_evidence_routes(
            sections,
            projected,
            limit=review_item_limit,
            omissions=omissions,
            strata=strata,
        )
        projected = reconcile_generated_family_routes(
            sections,
            projected,
            limit=review_item_limit,
            omissions=omissions,
            strata=strata,
            bound_value=_bounded_value,
        )
        projected = _reconcile_inspection_region_routes(
            sections,
            projected,
            limit=review_item_limit,
            omissions=omissions,
            strata=strata,
        )
        projected = reconcile_registered_evidence_routes(
            sections,
            projected,
            limit=review_item_limit,
            omissions=omissions,
            strata=strata,
        )
    omissions.sort(key=lambda row: (row["pointer"], row["reason"]))
    return projected, omissions, item_limit, strata


def _project_section(
    name: str,
    value: Any,
    *,
    projection: str,
    summary_item_limit: int,
    review_item_limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> Any:
    """Apply one projection policy to one canonical section."""

    pointer = f"#/sections/{_pointer_token(name)}"
    if projection == "full":
        return value
    if projection == "review":
        if isinstance(value, Mapping):
            return _bounded_section_mapping(
                value,
                limit=review_item_limit,
                pointer=pointer,
                omissions=omissions,
                strata=strata,
            )
        return _bounded_value(
            value,
            limit=review_item_limit,
            pointer=pointer,
            omissions=omissions,
            strata=strata,
        )
    return _summary_value(
        value,
        limit=summary_item_limit,
        pointer=pointer,
        omissions=omissions,
        preserve_rows=name == "findings",
        strata=strata,
    )


def _bounded_section_mapping(
    value: Mapping[str, Any],
    *,
    limit: int,
    pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> dict[str, Any]:
    """Project every field of a section object while bounding its populations."""

    if is_raw_declaration_container(value):
        return _bounded_raw_declaration_container(
            value,
            limit=limit,
            pointer=pointer,
            omissions=omissions,
            strata=strata,
        )
    if is_compact_declaration_container(value):
        return _bounded_declaration_container(
            value,
            limit=limit,
            pointer=pointer,
            omissions=omissions,
            strata=strata,
        )
    return {
        key: _bounded_value(
            item,
            limit=limit,
            pointer=f"{pointer}/{_pointer_token(key)}",
            omissions=omissions,
            strata=strata,
        )
        for key, item in sorted(value.items())
    }


def _reconcile_inspection_region_routes(
    canonical_sections: Mapping[str, Any],
    projected_sections: Mapping[str, Any],
    *,
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> dict[str, Any]:
    """Align retained audit/resource signals with projected owner rows."""

    projected = (
        projected_sections
        if isinstance(projected_sections, dict)
        else dict(projected_sections)
    )
    regions = projected.get("review_regions")
    canonical_regions = canonical_sections.get("review_regions")
    if not isinstance(regions, list) or not isinstance(canonical_regions, list):
        return projected
    canonical_by_id = regions_by_id(canonical_regions)
    canonical_owners = inspection_owner_pointers(canonical_sections)
    selected_by_region, changed = select_inspection_signals(
        regions,
        canonical_by_id=canonical_by_id,
        canonical_owners=canonical_owners,
        canonical_sections=canonical_sections,
        projected_sections=projected,
        limit=limit,
    )
    refresh_evidence_closure_ledgers(
        changed,
        omissions=omissions,
        strata=strata,
    )
    projected_owners = inspection_owner_pointers(projected)
    selected_producers = {"audits": set(), "resources": set()}
    reconciled: list[Any] = []
    for index, region in enumerate(regions):
        identity = region.get("id") if isinstance(region, Mapping) else None
        routed, selected = _reconciled_inspection_region(
            region,
            canonical_by_id=canonical_by_id,
            canonical_owners=canonical_owners,
            projected_owners=projected_owners,
            selected_signals=selected_by_region.get(str(identity), ()),
            index=index,
            limit=limit,
            omissions=omissions,
            strata=strata,
        )
        reconciled.append(routed)
        noun = inspection_region_noun(routed)
        if noun is not None:
            selected_producers[noun].update(
                signal["id"] for signal in selected if isinstance(signal.get("id"), str)
            )
    result = {**projected, "review_regions": reconciled}
    return _align_inspection_registrations(
        canonical_sections,
        result,
        selected_producers=selected_producers,
        limit=limit,
        omissions=omissions,
        strata=strata,
    )


def _reconciled_inspection_region(
    region: Any,
    *,
    canonical_by_id: Mapping[str, Mapping[str, Any]],
    canonical_owners: Mapping[str, Mapping[str, str]],
    projected_owners: Mapping[str, Mapping[str, str]],
    selected_signals: Sequence[Mapping[str, Any]],
    index: int,
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> tuple[Any, list[Mapping[str, Any]]]:
    """Return one route-safe region and its retained producer signals."""

    noun = inspection_region_noun(region)
    if noun is None or not isinstance(region, Mapping):
        return region, []
    identity = region.get("id")
    canonical = canonical_by_id.get(identity) if isinstance(identity, str) else None
    if canonical is None:
        return region, []
    canonical_signals = mapping_rows(canonical.get("signals"))
    candidates = [
        routed
        for signal in selected_signals
        if (
            routed := routed_inspection_signal(
                signal,
                noun=noun,
                canonical_owners=canonical_owners[noun],
                projected_owners=projected_owners[noun],
            )
        )
        is not None
    ]
    pointer = f"#/sections/review_regions/{index}/signals"
    selected = candidates
    nested_omissions: list[dict[str, Any]] = []
    nested_strata: list[dict[str, Any]] = []
    projected_signals = [
        _bounded_value(
            signal,
            limit=limit,
            pointer=f"{pointer}/{signal_index}",
            omissions=nested_omissions,
            strata=nested_strata,
        )
        for signal_index, signal in enumerate(selected)
    ]
    _replace_signal_projection_ledger(
        omissions,
        strata,
        pointer=pointer,
        canonical=canonical_signals,
        selected=selected,
        nested_omissions=nested_omissions,
        nested_strata=nested_strata,
    )
    action = canonical.get("inspectionAction")
    return (
        {
            **region,
            "signals": projected_signals,
            "signal_count": len(projected_signals),
            "inspectionAction": copy_json(action),
        },
        selected,
    )


def _replace_signal_projection_ledger(
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    *,
    pointer: str,
    canonical: list[Mapping[str, Any]],
    selected: list[Mapping[str, Any]],
    nested_omissions: list[dict[str, Any]],
    nested_strata: list[dict[str, Any]],
) -> None:
    """Replace generic signal accounting with owner-resolvable selection."""

    _prune_projection_ledger(omissions, strata, pointer=pointer)
    if len(canonical) > len(selected):
        _record_omission(omissions, pointer, len(canonical) - len(selected))
    strata.extend(selection_strata(canonical, selected, pointer=pointer))
    omissions.extend(nested_omissions)
    strata.extend(nested_strata)


def _align_inspection_registrations(
    canonical_sections: Mapping[str, Any],
    projected_sections: Mapping[str, Any],
    *,
    selected_producers: Mapping[str, set[Any]],
    limit: int,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> dict[str, Any]:
    """Retain exactly the producer rows backing projected region actions."""

    canonical_dag = canonical_sections.get("module_dag")
    projected_dag = projected_sections.get("module_dag")
    if not isinstance(canonical_dag, Mapping) or not isinstance(
        projected_dag,
        Mapping,
    ):
        return dict(projected_sections)
    dag = dict(projected_dag)
    for noun, _, registration_key in INSPECTION_REGION_ROUTES.values():
        dag[registration_key] = _aligned_registration(
            canonical_dag.get(registration_key),
            dag.get(registration_key),
            selected=selected_producers[noun],
            limit=limit,
            pointer=f"#/sections/module_dag/{registration_key}/producers",
            omissions=omissions,
            strata=strata,
        )
    return {**projected_sections, "module_dag": dag}


def _aligned_registration(
    canonical: Any,
    projected: Any,
    *,
    selected: set[Any],
    limit: int,
    pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> Any:
    """Return one bounded registration envelope aligned to retained signals."""

    canonical_producers = _registration_producers(canonical)
    if canonical_producers is None:
        return projected
    _prune_projection_ledger(omissions, strata, pointer=pointer)
    producers = _selected_registration_producers(
        canonical_producers,
        selected=selected,
        limit=limit,
        pointer=pointer,
        omissions=omissions,
        strata=strata,
    )
    _record_population_omission(
        omissions,
        pointer=pointer,
        total=len(canonical_producers),
        visible=len(producers),
    )
    envelope = dict(projected) if isinstance(projected, Mapping) else {}
    return {**envelope, "producers": producers}


def _registration_producers(value: Any) -> Mapping[str, Any] | None:
    """Return the canonical producer map from a registration envelope."""

    if not isinstance(value, Mapping):
        return None
    producers = value.get("producers")
    return producers if isinstance(producers, Mapping) else None


def _selected_registration_producers(
    canonical: Mapping[str, Any],
    *,
    selected: set[Any],
    limit: int,
    pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> dict[str, Any]:
    """Project the exact producer rows retained by routed region signals."""

    producers: dict[str, Any] = {}
    for identity in sorted(str(item) for item in selected):
        raw = canonical.get(identity)
        if raw is None:
            continue
        producers[identity] = _bounded_value(
            raw,
            limit=limit,
            pointer=f"{pointer}/{_pointer_token(identity)}",
            omissions=omissions,
            strata=strata,
        )
    return producers


def _record_population_omission(
    omissions: list[dict[str, Any]],
    *,
    pointer: str,
    total: int,
    visible: int,
) -> None:
    """Record the omitted share of one projected keyed population."""

    if total > visible:
        _record_omission(omissions, pointer, total - visible)


def _prune_projection_ledger(
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
    *,
    pointer: str,
) -> None:
    """Remove stale ledger entries below one recomputed projection owner."""

    omissions[:] = [
        row for row in omissions if not pointer_is_within(row["pointer"], pointer)
    ]
    strata[:] = [
        row for row in strata if not pointer_is_within(row["pointer"], pointer)
    ]


def _bounded_value(
    value: Any,
    *,
    limit: int,
    pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> Any:
    """Recursively copy a review value with deterministic collection bounds."""

    if isinstance(value, list):
        return _bounded_list(
            value,
            limit=limit,
            pointer=pointer,
            omissions=omissions,
            strata=strata,
        )
    if not isinstance(value, Mapping):
        return copy_json(value)
    if is_raw_declaration_container(value):
        return _bounded_raw_declaration_container(
            value,
            limit=limit,
            pointer=pointer,
            omissions=omissions,
            strata=strata,
        )
    if is_compact_declaration_container(value):
        return _bounded_declaration_container(
            value,
            limit=limit,
            pointer=pointer,
            omissions=omissions,
            strata=strata,
        )
    return _bounded_mapping(
        value,
        limit=limit,
        pointer=pointer,
        omissions=omissions,
        strata=strata,
    )


def _bounded_list(
    value: list[Any],
    *,
    limit: int,
    pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> list[Any]:
    """Bound one list after deterministic stratum selection."""

    preserve_all = (
        pointer == "#/sections/review_regions"
        or pointer.endswith("/inspectionAction/arguments")
        or _generated_family_feature_relationship(pointer)
    )
    selection_limit = len(value) if preserve_all else limit
    selected = _bounded_list_selection(
        value,
        limit=selection_limit,
        pointer=pointer,
        strata=strata,
    )
    omitted = len(value) - len(selected)
    if omitted > 0:
        _record_omission(
            omissions,
            pointer,
            omitted,
        )
    return [
        _bounded_value(
            item,
            limit=limit,
            pointer=f"{pointer}/{index}",
            omissions=omissions,
            strata=strata,
        )
        for index, item in enumerate(selected)
    ]


def _bounded_list_selection(
    value: list[Any],
    *,
    limit: int,
    pointer: str,
    strata: list[dict[str, Any]],
) -> list[Any]:
    """Select rows without reindexing canonical generated-family relations."""

    if not _generated_family_relationship(pointer):
        return stratified_selection(
            value,
            limit=limit,
            pointer=pointer,
            strata=strata,
        )
    selected = value[:limit]
    strata.extend(
        selection_strata(
            mapping_rows(value),
            mapping_rows(selected),
            pointer=pointer,
        )
    )
    return selected


def _generated_family_relationship(pointer: str) -> bool:
    """Return whether array indices are cited by producer evidence refs."""

    if not pointer.startswith(f"{_GENERATED_FAMILY_BASE}/"):
        return False
    relative = pointer.removeprefix(f"{_GENERATED_FAMILY_BASE}/")
    parts = relative.split("/")
    return relative in {"candidates", "partitions"} or (
        len(parts) == 3
        and parts[0] == "partitions"
        and parts[1].isdigit()
        and parts[2] == "features"
    )


def _generated_family_feature_relationship(pointer: str) -> bool:
    """Keep the detector's independently bounded witness-key collection."""

    if not pointer.startswith(f"{_GENERATED_FAMILY_BASE}/"):
        return False
    parts = pointer.removeprefix(f"{_GENERATED_FAMILY_BASE}/").split("/")
    return (
        len(parts) == 3
        and parts[0] == "partitions"
        and parts[1].isdigit()
        and parts[2] == "features"
    )


def _bounded_mapping(
    value: Mapping[str, Any],
    *,
    limit: int,
    pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> dict[str, Any]:
    """Bound dictionary-like populations while preserving record objects."""

    keys = sorted(value)
    bound = len(keys) > limit and not _looks_like_record(value)
    selected_keys = keys[:limit] if bound else keys
    if bound:
        _record_omission(omissions, pointer, len(keys) - limit)
    projected = {
        key: _bounded_value(
            value[key],
            limit=limit,
            pointer=f"{pointer}/{_pointer_token(key)}",
            omissions=omissions,
            strata=strata,
        )
        for key in selected_keys
    }
    return _synchronize_inline_coverage(
        projected,
        pointer=pointer,
        limit=limit,
    )


def _synchronize_inline_coverage(
    value: dict[str, Any],
    *,
    pointer: str,
    limit: int,
) -> dict[str, Any]:
    """Rebase embedded coverage after nested review collections are bounded."""

    result = value
    for collection_key, coverage_key in _INLINE_COVERAGE_FIELDS:
        collection = result.get(collection_key)
        raw_coverage = result.get(coverage_key)
        if not isinstance(collection, list) or not isinstance(
            raw_coverage,
            Mapping,
        ):
            continue
        coverage = CollectionCoverage.from_mapping(raw_coverage)
        target_pointer = f"{pointer}/{_pointer_token(collection_key)}"
        if len(collection) < coverage.visible:
            coverage = coverage.projected(
                identity=coverage.identity,
                pointer=target_pointer,
                visible=len(collection),
                cause=CoverageCause(
                    kind="projection",
                    identifier="projection.review_inline_collection_limit",
                    detail=(
                        "review projection bounded an inline canonical "
                        f"{collection_key} collection"
                    ),
                    controlling_cap=limit,
                ),
            )
        elif coverage.pointer != target_pointer:
            coverage = replace(coverage, pointer=target_pointer)
        result[coverage_key] = coverage.to_dict()
    return result


def _bounded_declaration_container(
    value: Mapping[str, Any],
    *,
    limit: int,
    pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> dict[str, Any]:
    """Bound declaration rows while retaining every referenced evidence entry."""

    selected_rows = _bounded_value(
        value["declarations"],
        limit=limit,
        pointer=f"{pointer}/declarations",
        omissions=omissions,
        strata=strata,
    )
    references = _evidence_references(selected_rows)
    evidence = value["_declarationEvidence"]
    selected_evidence = {
        key: _bounded_value(
            evidence[key],
            limit=limit,
            pointer=(f"{pointer}/_declarationEvidence/{_pointer_token(key)}"),
            omissions=omissions,
            strata=strata,
        )
        for key in sorted(references)
        if key in evidence
    }
    omitted_evidence = len(evidence) - len(selected_evidence)
    if omitted_evidence:
        _record_omission(
            omissions,
            f"{pointer}/_declarationEvidence",
            omitted_evidence,
        )
    result = _bounded_container_fields(
        value,
        limit=limit,
        pointer=pointer,
        omissions=omissions,
        strata=strata,
    )
    result["declarations"] = selected_rows
    result["_declarationEvidence"] = selected_evidence
    return result


def _bounded_raw_declaration_container(
    value: Mapping[str, Any],
    *,
    limit: int,
    pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> dict[str, Any]:
    """Select raw declaration rows before minting final evidence pointers."""

    raw_rows = value["declarations"]
    selected = _bounded_list_selection(
        raw_rows,
        limit=limit,
        pointer=f"{pointer}/declarations",
        strata=strata,
    )
    omitted = len(raw_rows) - len(selected)
    if omitted:
        _record_omission(
            omissions,
            f"{pointer}/declarations",
            omitted,
        )
    compacted_rows, evidence = compact_declaration_rows(
        selected,
        evidence_pointer=f"{pointer}/_declarationEvidence",
    )
    rows = [
        _bounded_value(
            row,
            limit=limit,
            pointer=f"{pointer}/declarations/{index}",
            omissions=omissions,
            strata=strata,
        )
        for index, row in enumerate(compacted_rows)
    ]
    references = _evidence_references(rows)
    selected_evidence = {
        key: _bounded_value(
            evidence[key],
            limit=limit,
            pointer=f"{pointer}/_declarationEvidence/{_pointer_token(key)}",
            omissions=omissions,
            strata=strata,
        )
        for key in sorted(references)
        if key in evidence
    }
    result = _bounded_container_fields(
        value,
        limit=limit,
        pointer=pointer,
        omissions=omissions,
        strata=strata,
    )
    result["declarations"] = rows
    result["_declarationEvidence"] = selected_evidence
    return result


def _evidence_references(rows: Any) -> set[str]:
    """Return compact evidence-table keys referenced by selected rows."""

    if not isinstance(rows, list):
        return set()
    return {
        str(row["evidenceRef"])
        .rsplit("/", maxsplit=1)[-1]
        .replace("~1", "/")
        .replace("~0", "~")
        for row in rows
        if isinstance(row, Mapping) and isinstance(row.get("evidenceRef"), str)
    }


def _bounded_container_fields(
    value: Mapping[str, Any],
    *,
    limit: int,
    pointer: str,
    omissions: list[dict[str, Any]],
    strata: list[dict[str, Any]],
) -> dict[str, Any]:
    """Project non-declaration fields in a compact declaration container."""

    return {
        key: _bounded_value(
            item,
            limit=limit,
            pointer=f"{pointer}/{_pointer_token(key)}",
            omissions=omissions,
            strata=strata,
        )
        for key, item in sorted(value.items())
        if key not in {"declarations", "_declarationEvidence"}
    }


def _summary_value(
    value: Any,
    *,
    limit: int,
    pointer: str,
    omissions: list[dict[str, Any]],
    preserve_rows: bool,
    strata: list[dict[str, Any]],
) -> Any:
    """Return a bounded section summary with explicit collection counts."""

    if preserve_rows:
        return _bounded_value(
            value,
            limit=limit,
            pointer=pointer,
            omissions=omissions,
            strata=strata,
        )
    if isinstance(value, list):
        if value:
            _record_omission(omissions, pointer, len(value))
        return {"kind": "array", "count": len(value)}
    if not isinstance(value, Mapping):
        return copy_json(value)
    return _summary_mapping(value, pointer=pointer, omissions=omissions)


def _summary_mapping(
    value: Mapping[str, Any],
    *,
    pointer: str,
    omissions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Split scalar summary fields from omitted nested collections."""

    scalars: dict[str, Any] = {}
    collections: dict[str, dict[str, Any]] = {}
    for key in sorted(value):
        item = value[key]
        if isinstance(item, Mapping):
            collections[key] = {"kind": "object", "count": len(item)}
            _record_nonempty_collection(omissions, pointer, key, item)
        elif isinstance(item, list):
            collections[key] = {"kind": "array", "count": len(item)}
            _record_nonempty_collection(omissions, pointer, key, item)
        else:
            scalars[key] = copy_json(item)
    return {"scalars": scalars, "collections": collections}


def _record_nonempty_collection(
    omissions: list[dict[str, Any]],
    pointer: str,
    key: str,
    value: Mapping[str, Any] | list[Any],
) -> None:
    """Record a summary omission only for a non-empty collection."""

    if value:
        _record_omission(
            omissions,
            f"{pointer}/{_pointer_token(key)}",
            len(value),
        )


def _record_omission(
    omissions: list[dict[str, Any]],
    pointer: str,
    omitted_count: int,
) -> None:
    """Append one deterministic projection omission."""

    omissions.append(
        {
            "pointer": pointer,
            "reason": "projection_collection_limit",
            "omitted_count": omitted_count,
        }
    )


def _pointer_token(value: str) -> str:
    """Escape one RFC 6901 JSON-pointer token."""

    return str(value).replace("~", "~0").replace("/", "~1")


def _looks_like_record(value: Mapping[str, Any]) -> bool:
    """Avoid truncating ordinary object fields as dictionary populations."""

    keys = set(value)
    return bool(keys & _RECORD_SHAPE_KEYS) or {
        "line",
        "column",
        "offset",
    }.issubset(keys)
