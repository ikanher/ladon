"""Deterministic structural-join plans and graph witnesses.

The helpers in this module prove only relationships between canonical Ladon
analysis rows.  They do not model Lean name resolution, elaboration, theorem
truth, or proof validity.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from ladon.finding_evidence import (
    json_pointer_token,
    resolve_local_json_pointer,
)


JOIN_SCHEMA = "ladon-structural-join-v1"
JOIN_NONCLAIM = (
    "This is a deterministic relationship between Ladon graph or identity "
    "rows; it is not Lean elaboration, theorem truth, proof failure, or defect "
    "confirmation."
)


@dataclass(frozen=True)
class StructuralJoinPlan:
    """One registered relationship required by an existing composite kind."""

    finding_kind: str
    join_kind: str
    component_metrics: tuple[str, ...]
    relationships: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return an inspectable plan descriptor."""

        return {
            "findingKind": self.finding_kind,
            "joinKind": self.join_kind,
            "componentMetrics": list(self.component_metrics),
            "relationships": list(self.relationships),
        }


STRUCTURAL_JOIN_PLANS: Mapping[str, StructuralJoinPlan] = MappingProxyType(
    {
        plan.finding_kind: plan
        for plan in (
            StructuralJoinPlan(
                finding_kind="composite_import_pressure",
                join_kind="root_import_closure_membership",
                component_metrics=(
                    "root_import_closure",
                    "module_fan_in",
                ),
                relationships=(
                    "closure_membership",
                    "deterministic_graph_path",
                ),
            ),
            StructuralJoinPlan(
                finding_kind="facade_fanout_pressure",
                join_kind="facade_population_membership",
                component_metrics=(
                    "facade_module_count",
                    "module_facade_fan_out",
                ),
                relationships=(
                    "same_subject",
                    "population_membership",
                    "containment",
                ),
            ),
            StructuralJoinPlan(
                finding_kind="root_scope_pressure",
                join_kind="root_reachability_population_subset",
                component_metrics=(
                    "module_count",
                    "unreachable_modules",
                ),
                relationships=(
                    "population_membership",
                    "subset",
                ),
            ),
            StructuralJoinPlan(
                finding_kind="proof_family_import_pressure",
                join_kind="declaration_family_in_root_import_closure",
                component_metrics=(
                    "root_import_closure",
                    "declaration_family_size",
                ),
                relationships=(
                    "identity_membership",
                    "containment",
                    "closure_membership",
                    "deterministic_graph_path",
                ),
            ),
        )
    }
)


def structural_join_plan(finding_kind: str) -> StructuralJoinPlan:
    """Return the registered join plan for one composite finding kind."""

    try:
        return STRUCTURAL_JOIN_PLANS[finding_kind]
    except KeyError as exc:
        raise ValueError(
            f"no structural join plan is registered for {finding_kind}"
        ) from exc


def deterministic_graph_path(
    raw_edges: Any,
    start: str,
    target: str,
) -> tuple[str, ...] | None:
    """Return the lexicographically deterministic shortest graph path."""

    edges = normalized_edges(raw_edges)
    if edges is None or start not in edges or target not in edges:
        return None
    parents: dict[str, str | None] = {start: None}
    queue: deque[str] = deque((start,))
    while queue:
        source = queue.popleft()
        if source == target:
            return _restore_path(parents, target)
        for neighbor in edges[source]:
            if neighbor not in parents:
                parents[neighbor] = source
                queue.append(neighbor)
    return None


def normalized_edges(
    raw_edges: Any,
) -> dict[str, tuple[str, ...]] | None:
    """Validate and normalize one canonical adjacency mapping."""

    if not isinstance(raw_edges, Mapping):
        return None
    edges: dict[str, tuple[str, ...]] = {}
    for source, targets in raw_edges.items():
        normalized = _normalized_edge_row(source, targets)
        if normalized is None:
            return None
        edges[source] = normalized
    if not _all_targets_known(edges):
        return None
    return edges


def _normalized_edge_row(
    source: Any,
    targets: Any,
) -> tuple[str, ...] | None:
    if not isinstance(source, str) or not source:
        return None
    if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes)):
        return None
    if any(not isinstance(target, str) or not target for target in targets):
        return None
    return tuple(sorted(set(targets)))


def _all_targets_known(
    edges: Mapping[str, Sequence[str]],
) -> bool:
    return all(
        target in edges
        for targets in edges.values()
        for target in targets
    )


def graph_path_witness(
    raw_edges: Any,
    path: Sequence[str],
) -> dict[str, Any] | None:
    """Build exact edge pointers for a previously validated graph path."""

    edges = normalized_edges(raw_edges)
    if edges is None or not path:
        return None
    raw_mapping = raw_edges
    if not isinstance(raw_mapping, Mapping):
        return None
    edge_refs: list[dict[str, Any]] = []
    for source, target in zip(path, path[1:]):
        raw_targets = raw_mapping.get(source)
        if (
            not isinstance(raw_targets, Sequence)
            or isinstance(raw_targets, (str, bytes))
            or target not in raw_targets
        ):
            return None
        index = raw_targets.index(target)
        edge_refs.append(
            {
                "source": source,
                "target": target,
                "pointer": (
                    "#/sections/module_dag/edges/"
                    f"{json_pointer_token(source)}/{index}"
                ),
            }
        )
    return {
        "type": "deterministic-graph-path",
        "pointer": "#/sections/module_dag/edges",
        "path": list(path),
        "edgeRefs": edge_refs,
        "authority": "module_import_graph",
    }


def build_structural_join(
    finding_kind: str,
    *,
    canonical_sections: Mapping[str, Any],
    component_metrics: Sequence[str],
    component_refs: Sequence[Mapping[str, Any]],
    witness_refs: Sequence[Mapping[str, Any]],
    population: str,
    scope: str,
    authority: str,
    coverage_refs: Sequence[str],
) -> dict[str, Any] | None:
    """Build a join only when every required local pointer is inspectable."""

    plan = structural_join_plan(finding_kind)
    metrics = tuple(component_metrics)
    components = [dict(reference) for reference in component_refs]
    witnesses = [dict(reference) for reference in witness_refs]
    payload = {"sections": canonical_sections}
    if not _join_shape_valid(
        plan,
        metrics=metrics,
        components=components,
        witnesses=witnesses,
        population=population,
        scope=scope,
        authority=authority,
    ):
        return None
    if not _join_references_valid(components, witnesses, payload):
        return None
    return {
        "schema": JOIN_SCHEMA,
        "kind": plan.join_kind,
        "relationships": list(plan.relationships),
        "componentMetrics": list(metrics),
        "componentRefs": components,
        "witnessRefs": witnesses,
        "population": population,
        "scope": scope,
        "authority": authority,
        "coverage": {
            "coverageRefs": sorted(set(coverage_refs)),
            "claimKind": "positive_witness",
            "status": "subset",
            "exhaustive": False,
            "nonclaims": [
                "The promoted relationship is witnessed in canonical visible "
                "rows; omitted evidence may contain additional candidates."
            ],
        },
        "nonclaim": JOIN_NONCLAIM,
    }


def _join_shape_valid(
    plan: StructuralJoinPlan,
    *,
    metrics: tuple[str, ...],
    components: Sequence[Mapping[str, Any]],
    witnesses: Sequence[Mapping[str, Any]],
    population: str,
    scope: str,
    authority: str,
) -> bool:
    identity_valid = (
        metrics == plan.component_metrics
        and len(components) == len(plan.component_metrics)
    )
    labels_valid = bool(population and scope and authority)
    return identity_valid and bool(witnesses) and labels_valid


def _join_references_valid(
    components: Sequence[Mapping[str, Any]],
    witnesses: Sequence[Mapping[str, Any]],
    payload: Mapping[str, Any],
) -> bool:
    components_valid = all(
        _local_reference(reference, payload)
        for reference in components
    )
    witnesses_valid = all(
        _witness_reference(reference, payload)
        for reference in witnesses
    )
    return components_valid and witnesses_valid


def _restore_path(
    parents: Mapping[str, str | None],
    target: str,
) -> tuple[str, ...]:
    path: list[str] = []
    node: str | None = target
    while node is not None:
        path.append(node)
        node = parents[node]
    return tuple(reversed(path))


def _local_reference(
    reference: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    pointer = reference.get("pointer")
    if not (
        reference.get("type") in {"canonical-row", "aggregate"}
        and isinstance(pointer, str)
        and pointer.startswith("#/sections/")
    ):
        return False
    target = _resolved_target(payload, pointer)
    if target is _UNRESOLVED:
        return False
    identity = reference.get("identity")
    return (
        reference.get("type") != "canonical-row"
        or (
            isinstance(target, Mapping)
            and isinstance(identity, Mapping)
            and all(target.get(key) == value for key, value in identity.items())
        )
    )


def _witness_reference(
    reference: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    pointers = _nested_pointers(reference)
    return bool(pointers) and all(
        isinstance(pointer, str) and pointer.startswith("#/sections/")
        and _resolved_target(payload, pointer) is not _UNRESOLVED
        for pointer in pointers
    )


_UNRESOLVED = object()


def _resolved_target(payload: Mapping[str, Any], pointer: str) -> Any:
    try:
        return resolve_local_json_pointer(payload, pointer)
    except (IndexError, KeyError, TypeError, ValueError):
        return _UNRESOLVED


def _nested_pointers(value: Any) -> list[Any]:
    if isinstance(value, Mapping):
        return _mapping_pointers(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return _sequence_pointers(value)
    return []


def _mapping_pointers(value: Mapping[str, Any]) -> list[Any]:
    pointers: list[Any] = []
    for key, child in value.items():
        if key == "pointer" or key.endswith("Pointer"):
            pointers.append(child)
        else:
            pointers.extend(_nested_pointers(child))
    return pointers


def _sequence_pointers(value: Sequence[Any]) -> list[Any]:
    pointers: list[Any] = []
    for child in value:
        pointers.extend(_nested_pointers(child))
    return pointers


__all__ = [
    "JOIN_NONCLAIM",
    "JOIN_SCHEMA",
    "STRUCTURAL_JOIN_PLANS",
    "StructuralJoinPlan",
    "build_structural_join",
    "deterministic_graph_path",
    "graph_path_witness",
    "normalized_edges",
    "structural_join_plan",
]
