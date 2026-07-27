"""Producer registration for structurally joined architecture findings."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ladon.analysis.structural_joins import (
    JOIN_SCHEMA,
    structural_join_plan,
)
from ladon.coverage import (
    CollectionCoverage,
    InspectionAction,
    ProducerRegistration,
    ProducerRegistry,
)
from ladon.finding_evidence import resolve_local_json_pointer
from ladon.pipeline_models import RunContext


ARCHITECTURE_JOINED_COVERAGE = "module_dag.architecture_joined_evidence"
_REGISTRY_POINTER = (
    "#/sections/module_dag/architectureProducerRegistrations/producers"
)
_JOINED_AUTHORITY = "ladon_derived_structural_join"
_ROOT_APPLICABILITY_WITNESSES = frozenset(
    {"root-applicability", "legacy-root-applicability"}
)
_REQUIRED_WITNESS_TYPES: Mapping[str, tuple[frozenset[str], ...]] = {
    "composite_import_pressure": (
        _ROOT_APPLICABILITY_WITNESSES,
        frozenset({"deterministic-graph-path"}),
    ),
    "facade_fanout_pressure": (
        frozenset({"population-membership"}),
    ),
    "root_scope_pressure": (
        _ROOT_APPLICABILITY_WITNESSES,
        frozenset({"population-subset"}),
    ),
    "proof_family_import_pressure": (
        _ROOT_APPLICABILITY_WITNESSES,
        frozenset({"declaration-containment"}),
        frozenset({"deterministic-graph-path"}),
    ),
}


def attach_architecture_producer_registrations(
    context: RunContext,
    dag: dict[str, Any],
    findings: Sequence[Mapping[str, Any]],
    declaration_graph: Mapping[str, Any] | None = None,
) -> None:
    """Expose valid joined findings to the report-owned region synthesizer."""

    canonical_report = {
        "sections": {
            "module_dag": dag,
            "declaration_graph": declaration_graph or {},
            "findings": list(findings),
        }
    }
    registry = ProducerRegistry()
    for index, finding in enumerate(findings):
        registration = _architecture_registration(
            finding,
            index=index,
            canonical_report=canonical_report,
        )
        if registration is not None:
            registry = registry.register_producer(registration)
    dag["architectureProducerRegistrations"] = registry.to_dict()
    count = len(registry.producers)
    dag["architecture_joined_coverage"] = CollectionCoverage.exact(
        identity=ARCHITECTURE_JOINED_COVERAGE,
        pointer=_REGISTRY_POINTER,
        visible=count,
        total=count,
        population="structurally_joined_architecture_findings",
        scope="selected_analysis_graphs",
        authority=_JOINED_AUTHORITY,
        source_fingerprint=(
            context.source_index.fingerprint
            if context.source_index is not None
            else None
        ),
        scope_fingerprint=(
            context.scope_plan.fingerprint
            if context.scope_plan is not None
            else None
        ),
    ).to_dict()


def _architecture_registration(
    finding: Mapping[str, Any],
    *,
    index: int,
    canonical_report: Mapping[str, Any],
) -> ProducerRegistration | None:
    """Adapt one finding only when its structural join is self-consistent."""

    fields = _registration_fields(finding)
    if fields is None:
        return None
    identity, kind, join, nonclaims, component_refs = fields
    if not _join_plan_matches(kind, join):
        return None
    if _canonical_pointers(join.get("componentRefs")) != component_refs:
        return None
    witness_pointers = _validated_witness_pointers(kind, join)
    if witness_pointers is None:
        return None
    finding_ref = f"#/sections/findings/{index}"
    join_ref = f"{finding_ref}/join"
    witness_refs = tuple(
        f"{join_ref}/witnessRefs/{witness_index}"
        for witness_index, _witness in enumerate(
            _mapping_sequence(join.get("witnessRefs"))
        )
    )
    evidence_refs = _ordered_unique(
        (
            finding_ref,
            join_ref,
            *component_refs,
            *witness_refs,
            *witness_pointers,
        )
    )
    if not _pointers_resolve(evidence_refs, canonical_report):
        return None
    return ProducerRegistration(
        identity=f"{identity}.review",
        kind=kind,
        evidence_refs=evidence_refs,
        coverage_ref=ARCHITECTURE_JOINED_COVERAGE,
        authority=_JOINED_AUTHORITY,
        nonclaims=nonclaims,
        action=InspectionAction(noun="modules"),
    )


def _registration_fields(
    finding: Mapping[str, Any],
) -> tuple[
    str,
    str,
    Mapping[str, Any],
    tuple[str, ...],
    tuple[str, ...],
] | None:
    """Return the typed producer inputs without accepting compatibility guesses."""

    if finding.get("authority") != _JOINED_AUTHORITY:
        return None
    identity = _nonempty_text(finding.get("stable_key"))
    kind = _nonempty_text(finding.get("kind"))
    join = finding.get("join")
    nonclaims = _nonempty_strings(finding.get("nonclaims"))
    component_refs = _canonical_pointers(finding.get("evidenceRefs"))
    if (
        identity is None
        or kind is None
        or not isinstance(join, Mapping)
        or nonclaims is None
        or not component_refs
    ):
        return None
    return identity, kind, join, nonclaims, component_refs


def _join_plan_matches(kind: str, join: Mapping[str, Any]) -> bool:
    """Require the registered finding to retain its exact structural plan."""

    try:
        plan = structural_join_plan(kind)
    except ValueError:
        return False
    return (
        join.get("schema") == JOIN_SCHEMA
        and join.get("kind") == plan.join_kind
        and _nonempty_strings(join.get("componentMetrics"))
        == plan.component_metrics
        and _nonempty_strings(join.get("relationships"))
        == plan.relationships
    )


def _validated_witness_pointers(
    kind: str,
    join: Mapping[str, Any],
) -> tuple[str, ...] | None:
    """Return all nested pointers only for the plan's required witness shapes."""

    witnesses = _mapping_sequence(join.get("witnessRefs"))
    requirements = _REQUIRED_WITNESS_TYPES.get(kind)
    if not witnesses or requirements is None:
        return None
    witness_types = _witness_types(witnesses)
    if witness_types is None:
        return None
    if not _witness_requirements_met(witness_types, requirements):
        return None
    return _witness_pointers(witnesses)


def _witness_types(
    witnesses: Sequence[Mapping[str, Any]],
) -> frozenset[str] | None:
    raw_types = tuple(witness.get("type") for witness in witnesses)
    if any(not isinstance(value, str) or not value for value in raw_types):
        return None
    return frozenset(value for value in raw_types if isinstance(value, str))


def _witness_requirements_met(
    witness_types: frozenset[str],
    requirements: tuple[frozenset[str], ...],
) -> bool:
    allowed = frozenset().union(*requirements)
    return witness_types.issubset(allowed) and all(
        witness_types & alternatives for alternatives in requirements
    )


def _witness_pointers(
    witnesses: Sequence[Mapping[str, Any]],
) -> tuple[str, ...] | None:
    pointers: list[str] = []
    for witness in witnesses:
        nested = _nested_pointers(witness)
        if nested is None or not nested:
            return None
        pointers.extend(nested)
    return _ordered_unique(pointers)


def _mapping_sequence(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    if any(not isinstance(row, Mapping) for row in value):
        return ()
    return tuple(row for row in value if isinstance(row, Mapping))


def _nested_pointers(value: Any) -> tuple[str, ...] | None:
    """Collect nested pointer fields and reject any malformed pointer value."""

    pointers: list[str] = []
    if not _collect_nested_pointers(value, pointers):
        return None
    return tuple(pointers)


def _collect_nested_pointers(value: Any, pointers: list[str]) -> bool:
    if isinstance(value, Mapping):
        return _collect_mapping_pointers(value, pointers)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return all(_collect_nested_pointers(child, pointers) for child in value)
    return True


def _collect_mapping_pointers(
    value: Mapping[str, Any],
    pointers: list[str],
) -> bool:
    for key, child in value.items():
        if key == "pointer" or key.endswith("Pointer"):
            if not _append_pointer(child, pointers):
                return False
        elif not _collect_nested_pointers(child, pointers):
            return False
    return True


def _append_pointer(value: Any, pointers: list[str]) -> bool:
    if not isinstance(value, str) or not value.startswith("#/sections/"):
        return False
    pointers.append(value)
    return True


def _pointers_resolve(
    pointers: Sequence[str],
    canonical_report: Mapping[str, Any],
) -> bool:
    try:
        for pointer in pointers:
            resolve_local_json_pointer(canonical_report, pointer)
    except (IndexError, KeyError, TypeError, ValueError):
        return False
    return True


def _ordered_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _canonical_pointers(value: Any) -> tuple[str, ...]:
    """Return canonical local pointers from structured evidence references."""

    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    pointers: list[str] = []
    for row in value:
        pointer = row.get("pointer") if isinstance(row, Mapping) else None
        if not isinstance(pointer, str) or not pointer.startswith("#/sections/"):
            return ()
        pointers.append(pointer)
    return tuple(pointers)


def _nonempty_strings(value: Any) -> tuple[str, ...] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    rows = tuple(str(row) for row in value if isinstance(row, str) and row)
    return rows if rows and len(rows) == len(value) else None


def _nonempty_text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


__all__ = [
    "ARCHITECTURE_JOINED_COVERAGE",
    "attach_architecture_producer_registrations",
]
