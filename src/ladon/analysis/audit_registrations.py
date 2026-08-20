"""Producer registrations for lexical audits and actionable resource settings."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon.analysis.resource_registrations import (
    RESOURCE_REVIEW_COVERAGE,
    attach_resource_policy_evidence,
    bind_resource_policy,
    register_resource_settings,
    resource_registration_authority,
)
from ladon.coverage import (
    CollectionCoverage,
    CoverageCause,
    InspectionAction,
    ProducerRegistration,
    ProducerRegistry,
)
from ladon.finding_evidence import json_pointer_token
from ladon.source_index_models import (
    SOURCE_INDEX_AUDITS_COVERAGE,
    SOURCE_INDEX_RESOURCES_COVERAGE,
    SourceIndex,
)

AUDIT_COMMAND_COVERAGE = "module_dag.audit_commands"
RESOURCE_DIRECTIVE_COVERAGE = "module_dag.resource_directives"
_AUDIT_COMMAND_POINTER = "#/sections/module_dag/audit_surfaces"
_RESOURCE_REGISTRY_POINTER = (
    "#/sections/module_dag/resourceProducerRegistrations/producers"
)


def attach_audit_producer_registrations(
    dag: dict[str, Any],
    source_index: SourceIndex | None,
    declaration_graph: Mapping[str, Any] | None = None,
    source_pattern_policy: Mapping[str, Any] | None = None,
    source_pattern_policy_identity: Mapping[str, Any] | None = None,
) -> None:
    """Register report inputs without promoting lexical rows to findings."""

    surfaces = dag.get("audit_surfaces")
    has_audit_commands = _has_audit_commands(surfaces)
    module_refs = _canonical_module_refs(dag) if has_audit_commands else {}
    lexical_rows = (
        _canonical_lexical_declarations(source_index) if has_audit_commands else {}
    )
    lean_refs = (
        _canonical_lean_declarations(declaration_graph) if has_audit_commands else {}
    )
    audit_registry = ProducerRegistry()
    resource_registry = ProducerRegistry()
    audit_observed = 0
    resource_count = 0
    resource_observed = 0
    resource_policy = bind_resource_policy(
        source_pattern_policy,
        source_pattern_policy_identity,
    )
    attach_resource_policy_evidence(dag, resource_policy)
    if isinstance(surfaces, list):
        for surface_index, surface in enumerate(surfaces):
            if not isinstance(surface, Mapping):
                continue
            (
                audit_registry,
                audit_added,
                audit_rejected,
            ) = _register_audit_commands(
                audit_registry,
                surface,
                surface_index,
                module_refs=module_refs,
                lexical_rows=lexical_rows,
                lean_refs=lean_refs,
            )
            resource_registry, resource_added = register_resource_settings(
                resource_registry,
                surface,
                surface_index,
                policy=resource_policy,
            )
            audit_observed += audit_added + audit_rejected
            resource_count += resource_added
            resource_observed += _resource_directive_count(surface)
    dag["auditProducerRegistrations"] = audit_registry.to_dict()
    dag["resourceProducerRegistrations"] = resource_registry.to_dict()
    source_fingerprint = source_index.fingerprint if source_index is not None else None
    scope_fingerprint = _scope_fingerprint(dag)
    audit_upstream = _source_coverage(
        source_index,
        SOURCE_INDEX_AUDITS_COVERAGE,
    )
    resource_upstream = _source_coverage(
        source_index,
        SOURCE_INDEX_RESOURCES_COVERAGE,
    )
    dag["audit_command_coverage"] = _producer_coverage(
        AUDIT_COMMAND_COVERAGE,
        audit_observed,
        "lexical_audit_commands",
        "lexical_text",
        source_fingerprint,
        scope_fingerprint,
        _AUDIT_COMMAND_POINTER,
        audit_upstream,
        observed=audit_observed,
    ).to_dict()
    dag["resource_review_coverage"] = _producer_coverage(
        RESOURCE_REVIEW_COVERAGE,
        resource_count,
        "normalized_unlimited_or_policy_backed_resource_settings",
        resource_registration_authority(resource_registry),
        source_fingerprint,
        scope_fingerprint,
        _RESOURCE_REGISTRY_POINTER,
        resource_upstream,
    ).to_dict()
    dag["resource_directive_coverage"] = _producer_coverage(
        RESOURCE_DIRECTIVE_COVERAGE,
        resource_observed,
        "lexical_resource_settings",
        "lexical_text",
        source_fingerprint,
        scope_fingerprint,
        _AUDIT_COMMAND_POINTER,
        resource_upstream,
        observed=resource_observed,
    ).to_dict()


def _resource_directive_count(surface: Mapping[str, Any]) -> int:
    """Count canonical resource rows, not their review registrations."""

    rows = surface.get("resourceDirectives")
    return len(rows) if isinstance(rows, list) else 0


def _has_audit_commands(surfaces: Any) -> bool:
    """Return whether audit registration needs declaration lookup tables."""

    if not isinstance(surfaces, list):
        return False
    return any(
        isinstance(surface, Mapping)
        and isinstance(surface.get("auditCommands"), list)
        and bool(surface["auditCommands"])
        for surface in surfaces
    )


def _register_audit_commands(
    registry: ProducerRegistry,
    surface: Mapping[str, Any],
    surface_index: int,
    *,
    module_refs: Mapping[str, str],
    lexical_rows: Mapping[str, tuple[str, str | None]],
    lean_refs: Mapping[tuple[str, str], str],
) -> tuple[ProducerRegistry, int, int]:
    commands = surface.get("auditCommands")
    if not isinstance(commands, list):
        return registry, 0, 0
    added = 0
    rejected = 0
    for command_index, command in enumerate(commands):
        if not isinstance(command, Mapping) or not command.get("id"):
            rejected += 1
            continue
        pointer = (
            "#/sections/module_dag/audit_surfaces/"
            f"{surface_index}/auditCommands/{command_index}"
        )
        evidence_refs = _audit_evidence_refs(
            surface,
            command,
            pointer=pointer,
            module_refs=module_refs,
            lexical_rows=lexical_rows,
            lean_refs=lean_refs,
        )
        if evidence_refs is None:
            rejected += 1
            continue
        registration = ProducerRegistration(
            identity=f"{command['id']}.review",
            kind="audit_command_navigation",
            evidence_refs=evidence_refs,
            coverage_ref=AUDIT_COMMAND_COVERAGE,
            authority=_audit_registration_authority(command),
            nonclaims=_row_nonclaims(command),
            action=InspectionAction(
                noun="audits",
                stable_id=str(command["id"]),
            ),
        )
        registry = registry.register_producer(registration)
        added += 1
    return registry, added, rejected


def _audit_evidence_refs(
    surface: Mapping[str, Any],
    command: Mapping[str, Any],
    *,
    pointer: str,
    module_refs: Mapping[str, str],
    lexical_rows: Mapping[str, tuple[str, str | None]],
    lean_refs: Mapping[tuple[str, str], str],
) -> tuple[str, ...] | None:
    """Resolve every canonical row claimed by one audit registration."""

    containing_owner = _nonempty_text(
        command.get("containingOwner") or command.get("module") or surface.get("module")
    )
    surface_module = _nonempty_text(surface.get("module"))
    if (
        containing_owner is None
        or surface_module != containing_owner
        or containing_owner not in module_refs
    ):
        return None
    lexical_refs = _audit_lexical_refs(command, lexical_rows)
    lean_ref = _audit_lean_ref(command, lean_refs)
    if lexical_refs is None or lean_ref is False:
        return None
    rows = [
        pointer,
        module_refs[containing_owner],
        *lexical_refs,
    ]
    if isinstance(lean_ref, str):
        rows.append(lean_ref)
    return tuple(dict.fromkeys(rows))


def _audit_lexical_refs(
    command: Mapping[str, Any],
    lexical_rows: Mapping[str, tuple[str, str | None]],
) -> tuple[str, ...] | None:
    """Validate every bounded source-index candidate cited by a command."""

    raw_matches = command.get("candidateMatches")
    if not isinstance(raw_matches, list):
        return None
    candidate_id = _nonempty_text(command.get("candidateDeclarationId"))
    matches = tuple(row for row in raw_matches if isinstance(row, Mapping))
    if len(matches) != len(raw_matches):
        return None
    if candidate_id is not None and not matches:
        return None
    refs: list[str] = []
    observed_ids: list[str] = []
    for match in matches:
        validated = _validated_lexical_match(match, lexical_rows)
        if validated is None:
            return None
        identifier, reference = validated
        observed_ids.append(identifier)
        refs.append(reference)
    if not _lexical_candidate_fields_match(
        command,
        observed_ids,
        lexical_rows,
    ):
        return None
    return tuple(dict.fromkeys(refs))


def _validated_lexical_match(
    match: Mapping[str, Any],
    lexical_rows: Mapping[str, tuple[str, str | None]],
) -> tuple[str, str] | None:
    """Return one canonical lexical ref only when owner and name also match."""

    identifier = _nonempty_text(match.get("id"))
    owner = _nonempty_text(match.get("candidateReferencedOwner"))
    name = _nonempty_text(match.get("candidateDeclaration"))
    if (
        identifier is None
        or owner is None
        or lexical_rows.get(identifier) != (owner, name)
    ):
        return None
    return identifier, f"source-index:declaration:{identifier}"


def _lexical_candidate_fields_match(
    command: Mapping[str, Any],
    observed_ids: list[str],
    lexical_rows: Mapping[str, tuple[str, str | None]],
) -> bool:
    """Require unique-candidate summary fields to match their canonical row."""

    candidate_id = _nonempty_text(command.get("candidateDeclarationId"))
    if command.get("candidateStatus") != "lexical_candidate":
        return candidate_id is None
    if len(observed_ids) != 1 or candidate_id != observed_ids[0]:
        return False
    owner, declaration = lexical_rows[observed_ids[0]]
    return (
        command.get("candidateReferencedOwner") == owner
        and command.get("candidateReferencedDeclaration") == declaration
    )


def _audit_lean_ref(
    command: Mapping[str, Any],
    lean_refs: Mapping[tuple[str, str], str],
) -> str | bool | None:
    """Return one exact Lean declaration pointer or fail a claimed join."""

    declaration = _nonempty_text(command.get("referencedDeclaration"))
    owner = _nonempty_text(command.get("referencedOwner"))
    claims_lean = command.get("resultAuthority") == "lean_environment"
    if not claims_lean:
        return None
    if declaration is None and owner is None:
        return None
    if declaration is None or owner is None:
        return False
    return lean_refs.get((declaration, owner), False)


def _audit_registration_authority(command: Mapping[str, Any]) -> str:
    """Keep optional Lean evidence visible without upgrading lexical commands."""

    if command.get("resultAuthority") == "lean_environment":
        return "lexical_text_and_lean_environment"
    return str(command.get("authority") or "lexical_text")


def _canonical_module_refs(dag: Mapping[str, Any]) -> dict[str, str]:
    """Index only report-resident canonical containing-module rows."""

    metadata = dag.get("module_metadata")
    if not isinstance(metadata, Mapping):
        return {}
    return {
        str(module): (
            "#/sections/module_dag/module_metadata/" + json_pointer_token(str(module))
        )
        for module, row in sorted(metadata.items(), key=lambda item: str(item[0]))
        if isinstance(row, Mapping) and str(module)
    }


def _canonical_lexical_declarations(
    source_index: SourceIndex | None,
) -> dict[str, tuple[str, str | None]]:
    """Index canonical source rows by stable lexical declaration identity."""

    if source_index is None:
        return {}
    return {
        declaration.identifier: (entry.name, declaration.candidate_name)
        for entry in source_index.entries
        for declaration in entry.module.declaration_evidence
        if declaration.identifier
    }


def _canonical_lean_declarations(
    declaration_graph: Mapping[str, Any] | None,
) -> dict[tuple[str, str], str]:
    """Index unique canonical declaration-graph rows by identity and owner."""

    if declaration_graph is None:
        return {}
    raw_rows = declaration_graph.get("declarations")
    if not isinstance(raw_rows, list):
        return {}
    grouped: dict[tuple[str, str], list[str]] = {}
    for index, row in enumerate(raw_rows):
        if not isinstance(row, Mapping):
            continue
        declaration = _nonempty_text(row.get("declaration"))
        owner = _nonempty_text(row.get("module"))
        if declaration is None or owner is None:
            continue
        grouped.setdefault((declaration, owner), []).append(
            f"#/sections/declaration_graph/declarations/{index}"
        )
    return {key: pointers[0] for key, pointers in grouped.items() if len(pointers) == 1}


def _nonempty_text(value: Any) -> str | None:
    """Return one nonempty string without coercing malformed fields."""

    return value if isinstance(value, str) and value else None


def _row_nonclaims(row: Mapping[str, Any]) -> tuple[str, ...]:
    values = (
        row.get("nonclaim"),
        row.get("resultNonclaim"),
    )
    selected = tuple(str(value) for value in values if isinstance(value, str) and value)
    return selected or ("Lexical navigation evidence only.",)


def _producer_coverage(
    identity: str,
    total: int,
    population: str,
    authority: str,
    source_fingerprint: str | None,
    scope_fingerprint: str | None,
    pointer: str,
    upstream: CollectionCoverage | None,
    *,
    observed: int | None = None,
    suppressed: int = 0,
) -> CollectionCoverage:
    """Describe visible producers without overstating incomplete inputs."""

    observed_count = total if observed is None else observed
    suppression_causes = (
        (
            CoverageCause(
                kind="analysis",
                identifier="audit_registration.dangling_evidence_suppressed",
                detail=(
                    f"{suppressed} observed audit command registration(s) "
                    "were suppressed because required canonical evidence "
                    "references did not resolve."
                ),
            ),
        )
        if suppressed
        else ()
    )
    common = {
        "identity": identity,
        "pointer": pointer,
        "visible": total,
        "population": population,
        "scope": "selected_module_graph",
        "authority": authority,
        "source_fingerprint": (
            upstream.source_fingerprint if upstream is not None else source_fingerprint
        ),
        "scope_fingerprint": scope_fingerprint,
    }
    if upstream is not None and upstream.completeness == "complete":
        return CollectionCoverage.exact(
            total=observed_count,
            observed_lower_bound=observed_count,
            causes=suppression_causes,
            **common,
        )
    return CollectionCoverage.unknown(
        observed_lower_bound=observed_count,
        completeness=(upstream.completeness if upstream is not None else "unavailable"),
        causes=(
            (*upstream.causes, *suppression_causes)
            if upstream is not None
            else (
                CoverageCause(
                    kind="analysis",
                    identifier="audit_registration.source_index_unavailable",
                    detail=("Audit producer coverage has no source-index population."),
                ),
                *suppression_causes,
            )
        ),
        **common,
    )


def _source_coverage(
    source_index: SourceIndex | None,
    identity: str,
) -> CollectionCoverage | None:
    """Return the canonical upstream collection for one producer family."""

    if source_index is None:
        return None
    return source_index.coverage_registry().require(identity)


def _scope_fingerprint(dag: Mapping[str, Any]) -> str | None:
    scope = dag.get("analysis_scope")
    value = scope.get("fingerprint") if isinstance(scope, Mapping) else None
    return str(value) if isinstance(value, str) and value else None


__all__ = [
    "AUDIT_COMMAND_COVERAGE",
    "RESOURCE_DIRECTIVE_COVERAGE",
    "RESOURCE_REVIEW_COVERAGE",
    "attach_audit_producer_registrations",
]
