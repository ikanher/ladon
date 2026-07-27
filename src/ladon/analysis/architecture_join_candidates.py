"""Deterministic candidate enumeration for architecture structural joins."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ladon.analysis.architecture_measures import (
    indexed_rows,
    is_facade_member,
    metric_integer,
    nonnegative_integer_value,
    row_string,
)
from ladon.analysis.declaration_graph import declaration_family_suffix
from ladon.analysis.structural_joins import deterministic_graph_path


HOTSPOT_THRESHOLD = 5


@dataclass(frozen=True)
class ImportPressureCandidate:
    closure_index: int
    closure: Mapping[str, Any]
    fan_index: int
    fan_in: Mapping[str, Any]
    path: tuple[str, ...]


@dataclass(frozen=True)
class FacadeFanoutCandidate:
    row_key: str
    index: int
    row: Mapping[str, Any]


@dataclass(frozen=True)
class ProofFamilyCandidate:
    closure_index: int
    closure: Mapping[str, Any]
    family_index: int
    family: Mapping[str, Any]
    joined_members: tuple[tuple[int, Mapping[str, Any]], ...]
    module_paths: tuple[tuple[str, tuple[str, ...]], ...]


def strongest_import_pressure_candidate(
    module_dag: Mapping[str, Any],
) -> ImportPressureCandidate | None:
    """Select the strongest hot fan-in that is actually in a hot closure."""

    candidates = [
        candidate
        for closure_index, closure in indexed_rows(
            module_dag,
            "root_direct_import_closures",
        )
        for candidate in _import_candidates_for_closure(
            module_dag,
            closure_index,
            closure,
        )
    ]
    if not candidates:
        return None
    return min(candidates, key=_import_candidate_order)


def _import_candidates_for_closure(
    module_dag: Mapping[str, Any],
    closure_index: int,
    closure: Mapping[str, Any],
) -> list[ImportPressureCandidate]:
    closure_value = metric_integer(closure, "reachable_module_count")
    direct_import = row_string(closure, "direct_import")
    root = row_string(closure, "root")
    if closure_value < HOTSPOT_THRESHOLD or not direct_import or not root:
        return []
    return [
        ImportPressureCandidate(
            closure_index=closure_index,
            closure=closure,
            fan_index=fan_index,
            fan_in=fan_row,
            path=path,
        )
        for fan_index, fan_row in indexed_rows(module_dag, "top_fan_in")
        for path in [
            _hot_fan_in_path(
                module_dag.get("edges"),
                direct_import,
                fan_row,
            )
        ]
        if path is not None
    ]


def _hot_fan_in_path(
    edges: Any,
    direct_import: str,
    fan_row: Mapping[str, Any],
) -> tuple[str, ...] | None:
    subject = row_string(fan_row, "module")
    if metric_integer(fan_row, "fan_in") < HOTSPOT_THRESHOLD or not subject:
        return None
    return deterministic_graph_path(edges, direct_import, subject)


def _import_candidate_order(
    candidate: ImportPressureCandidate,
) -> tuple[int, int, str, str, str, int, int]:
    return (
        -metric_integer(candidate.fan_in, "fan_in"),
        -metric_integer(candidate.closure, "reachable_module_count"),
        row_string(candidate.closure, "root"),
        row_string(candidate.closure, "direct_import"),
        row_string(candidate.fan_in, "module"),
        candidate.closure_index,
        candidate.fan_index,
    )


def strongest_facade_fanout_candidate(
    module_dag: Mapping[str, Any],
) -> FacadeFanoutCandidate | None:
    """Select a hot row only when canonical metadata proves facade membership."""

    metadata = module_dag.get("module_metadata")
    if not isinstance(metadata, Mapping):
        return None
    candidates = [
        FacadeFanoutCandidate(row_key=row_key, index=index, row=row)
        for row_key in ("top_facade_fan_out", "top_fan_out")
        for index, row in indexed_rows(module_dag, row_key)
        if _hot_facade_row(row, metadata)
    ]
    if not candidates:
        return None
    return min(candidates, key=_facade_candidate_order)


def _hot_facade_row(
    row: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> bool:
    subject = row_string(row, "module")
    return bool(
        metric_integer(row, "fan_out") >= HOTSPOT_THRESHOLD
        and subject
        and is_facade_member(metadata.get(subject))
    )


def _facade_candidate_order(
    candidate: FacadeFanoutCandidate,
) -> tuple[int, str, int, int]:
    return (
        -metric_integer(candidate.row, "fan_out"),
        row_string(candidate.row, "module"),
        0 if candidate.row_key == "top_facade_fan_out" else 1,
        candidate.index,
    )


def strongest_proof_family_candidate(
    module_dag: Mapping[str, Any],
    declaration_graph: Mapping[str, Any],
) -> ProofFamilyCandidate | None:
    """Select the strongest family with enough exact containment witnesses."""

    candidates = [
        candidate
        for closure_index, closure in indexed_rows(
            module_dag,
            "root_direct_import_closures",
        )
        for family_index, family in indexed_rows(
            declaration_graph,
            "declaration_name_families",
        )
        for candidate in [
            _proof_candidate(
                module_dag,
                declaration_graph,
                closure_index=closure_index,
                closure=closure,
                family_index=family_index,
                family=family,
            )
        ]
        if candidate is not None
    ]
    if not candidates:
        return None
    return min(candidates, key=_proof_candidate_order)


def _proof_candidate(
    module_dag: Mapping[str, Any],
    declaration_graph: Mapping[str, Any],
    *,
    closure_index: int,
    closure: Mapping[str, Any],
    family_index: int,
    family: Mapping[str, Any],
) -> ProofFamilyCandidate | None:
    root = row_string(closure, "root")
    direct_import = row_string(closure, "direct_import")
    suffix = row_string(family, "suffix")
    if not _hot_proof_components(closure, family, root, direct_import, suffix):
        return None
    members = exact_family_members(declaration_graph, family)
    if members is None:
        return None
    joined, paths = joined_family_members(
        members,
        root=root,
        direct_import=direct_import,
        edges=module_dag.get("edges"),
    )
    if len(joined) < HOTSPOT_THRESHOLD:
        return None
    return ProofFamilyCandidate(
        closure_index=closure_index,
        closure=closure,
        family_index=family_index,
        family=family,
        joined_members=joined,
        module_paths=paths,
    )


def _hot_proof_components(
    closure: Mapping[str, Any],
    family: Mapping[str, Any],
    root: str,
    direct_import: str,
    suffix: str,
) -> bool:
    return bool(
        metric_integer(closure, "reachable_module_count")
        >= HOTSPOT_THRESHOLD
        and metric_integer(family, "count") >= HOTSPOT_THRESHOLD
        and root
        and direct_import
        and suffix
    )


def _proof_candidate_order(
    candidate: ProofFamilyCandidate,
) -> tuple[int, int, int, str, str, str, int, int]:
    return (
        -len(candidate.joined_members),
        -metric_integer(candidate.family, "count"),
        -metric_integer(candidate.closure, "reachable_module_count"),
        row_string(candidate.family, "suffix"),
        row_string(candidate.closure, "root"),
        row_string(candidate.closure, "direct_import"),
        candidate.closure_index,
        candidate.family_index,
    )


def exact_family_members(
    declaration_graph: Mapping[str, Any],
    family: Mapping[str, Any],
) -> tuple[tuple[int, Mapping[str, Any]], ...] | None:
    """Resolve the entire family against canonical declaration identities."""

    suffix = row_string(family, "suffix")
    expected = nonnegative_integer_value(family.get("count"))
    declarations = _declaration_rows(declaration_graph.get("declarations"))
    if not suffix or expected is None or declarations is None:
        return None
    members = tuple(
        (index, row)
        for index, row in declarations
        if declaration_matches_family(row, suffix)
    )
    if len(members) != expected or not _members_have_identities(members):
        return None
    return members


def _declaration_rows(
    value: Any,
) -> tuple[tuple[int, Mapping[str, Any]], ...] | None:
    if not isinstance(value, list):
        return None
    if any(not isinstance(row, Mapping) for row in value):
        return None
    return tuple(enumerate(value))


def _members_have_identities(
    members: Sequence[tuple[int, Mapping[str, Any]]],
) -> bool:
    return all(
        row_string(row, "declaration") and row_string(row, "module")
        for _, row in members
    )


def declaration_matches_family(
    row: Mapping[str, Any],
    suffix: str,
) -> bool:
    """Return whether a declaration row belongs to one canonical family."""

    declaration = row_string(row, "declaration")
    return bool(
        declaration
        and declaration_family_suffix(declaration) == suffix
    )


def joined_family_members(
    members: Sequence[tuple[int, Mapping[str, Any]]],
    *,
    root: str,
    direct_import: str,
    edges: Any,
) -> tuple[
    tuple[tuple[int, Mapping[str, Any]], ...],
    tuple[tuple[str, tuple[str, ...]], ...],
]:
    """Keep declarations contained by the root or its direct-import closure."""

    joined: list[tuple[int, Mapping[str, Any]]] = []
    paths: dict[str, tuple[str, ...]] = {}
    for index, row in members:
        module = row_string(row, "module")
        path = _member_path(
            module,
            root=root,
            direct_import=direct_import,
            edges=edges,
        )
        if module == root or path is not None:
            joined.append((index, row))
        if path is not None:
            paths[module] = path
    return tuple(joined), tuple(sorted(paths.items()))


def _member_path(
    module: str,
    *,
    root: str,
    direct_import: str,
    edges: Any,
) -> tuple[str, ...] | None:
    if module == root:
        return None
    return deterministic_graph_path(edges, direct_import, module)


__all__ = [
    "FacadeFanoutCandidate",
    "ImportPressureCandidate",
    "ProofFamilyCandidate",
    "strongest_facade_fanout_candidate",
    "strongest_import_pressure_candidate",
    "strongest_proof_family_candidate",
]
