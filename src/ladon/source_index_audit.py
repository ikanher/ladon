"""Audit-command validity and coverage at the canonical source-index seam."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon.analysis.audit_surface import LEXICAL_AUTHORITY, AuditCommand
from ladon.coverage import CollectionCoverage, CoverageCause
from ladon.ir import LeanModule
from ladon.source_index_errors import SourceIndexError

SOURCE_INDEX_AUDITS_COVERAGE = "source_index.audits"
SOURCE_INDEX_COVERAGE_POINTER = "#/entries"


def audit_command_evidence_complete(module: LeanModule) -> bool:
    """Return whether one module carries usable current audit-command evidence."""

    return module.audit_commands_complete and all(
        valid_audit_command_row(command, module)
        for command in module.audit_commands
    )


def validate_audit_command_rows(module: LeanModule) -> None:
    """Reject malformed observed rows independently of collection completeness."""

    if all(
        valid_audit_command_row(command, module)
        for command in module.audit_commands
    ):
        return
    raise SourceIndexError(
        f"source-index audit commands are malformed for {module.name}"
    )


def valid_audit_command_row(
    command: AuditCommand,
    module: LeanModule,
) -> bool:
    """Validate one pre-enrichment source-index audit command fail closed."""

    return (
        _audit_identity_valid(command, module)
        and _audit_range_valid(command)
        and _audit_subject_valid(command)
        and _audit_state_valid(command)
    )


def _audit_identity_valid(command: AuditCommand, module: LeanModule) -> bool:
    return (
        command.module == module.name
        and command.path == module.path
        and command.identifier.startswith("ladon.audit.")
        and command.kind in {"check", "print_axioms"}
        and command.backend == "text"
        and command.authority == LEXICAL_AUTHORITY
    )


def _audit_range_valid(command: AuditCommand) -> bool:
    source_range = command.source_range
    return (
        source_range.start.line >= 1
        and source_range.start.column >= 1
        and source_range.start.offset >= 0
        and source_range.end.line >= source_range.start.line
        and source_range.end.column >= 1
        and source_range.end.offset >= source_range.start.offset
    )


def _audit_subject_valid(command: AuditCommand) -> bool:
    if command.subject_truncated:
        return command.subject_total_characters > len(command.subject)
    return command.subject_total_characters == len(command.subject)


def _audit_state_valid(command: AuditCommand) -> bool:
    diagnostic_state = (
        command.status == "lexical" and not command.diagnostics
    ) or (command.status == "unparsed" and bool(command.diagnostics))
    return (
        diagnostic_state
        and command.referenced_declaration is None
        and command.referenced_owner is None
        and command.result_status == "unavailable"
        and command.result_authority is None
        and bool(command.result_reason)
        and bool(command.nonclaim)
    )


def audit_commands_complete_field(row: Mapping[str, Any]) -> bool:
    """Decode additive audit availability without upgrading legacy absence."""

    explicit = row.get("auditCommandsComplete")
    present = "auditCommands" in row
    if explicit is None:
        return present
    if not isinstance(explicit, bool):
        raise SourceIndexError(
            "source-index audit-command completeness is malformed"
        )
    if explicit and not present:
        raise SourceIndexError("complete source-index audit commands are absent")
    return explicit


def audit_command_coverage(
    index: Any,
    *,
    causes: tuple[CoverageCause, ...],
) -> CollectionCoverage:
    """Report legacy audit absence as unknown rather than observed emptiness."""

    visible = sum(len(entry.module.audit_commands) for entry in index.entries)
    unavailable = tuple(
        entry.name
        for entry in index.entries
        if not audit_command_evidence_complete(entry.module)
    )
    if unavailable:
        return _unknown_audit_coverage(
            index,
            visible=visible,
            unavailable=unavailable,
            causes=causes,
        )
    if index.index_status == "complete":
        return CollectionCoverage.exact(
            identity=SOURCE_INDEX_AUDITS_COVERAGE,
            pointer=SOURCE_INDEX_COVERAGE_POINTER,
            visible=visible,
            total=visible,
            population="lexical_audit_commands",
            scope="source_index_inventory",
            authority="lexical_text",
            source_fingerprint=index.fingerprint,
        )
    return CollectionCoverage.unknown(
        identity=SOURCE_INDEX_AUDITS_COVERAGE,
        pointer=SOURCE_INDEX_COVERAGE_POINTER,
        visible=visible,
        observed_lower_bound=visible,
        completeness="partial",
        population="lexical_audit_commands",
        scope="source_index_inventory",
        authority="lexical_text",
        causes=causes,
        source_fingerprint=index.fingerprint,
    )


def _unknown_audit_coverage(
    index: Any,
    *,
    visible: int,
    unavailable: tuple[str, ...],
    causes: tuple[CoverageCause, ...],
) -> CollectionCoverage:
    unavailable_cause = CoverageCause(
        kind="compatibility",
        identifier="source_index.audit_commands_unavailable",
        detail=(
            "Audit-command availability is unknown for modules: "
            + ", ".join(unavailable)
            + "."
        ),
    )
    return CollectionCoverage.unknown(
        identity=SOURCE_INDEX_AUDITS_COVERAGE,
        pointer=SOURCE_INDEX_COVERAGE_POINTER,
        visible=visible,
        observed_lower_bound=visible,
        completeness="partial",
        population="lexical_audit_commands",
        scope="source_index_inventory",
        authority="lexical_text",
        causes=(*causes, unavailable_cause),
        source_fingerprint=index.fingerprint,
    )


__all__ = [
    "SOURCE_INDEX_AUDITS_COVERAGE",
    "audit_command_coverage",
    "audit_command_evidence_complete",
    "audit_commands_complete_field",
    "valid_audit_command_row",
    "validate_audit_command_rows",
]
