"""Join lexical Lean audit commands with existing elaborator evidence.

The join is deliberately exact: only a bare fully qualified subject (or its
``_root_.`` spelling) can match a declaration returned by the existing
elaborated helper.  No suffix matching, extra helper process, or theorem-truth
inference is performed here.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from ladon.analysis.audit_surface import AuditCommand, extract_audit_surface
from ladon.declaration_surface import (
    MAX_DEPENDENCIES,
    bounded_strings,
    declaration_name,
    mapping_rows,
    string_or_none,
)
from ladon.ir import BoundedStrings, LeanAuditQuery

CHECK_NONCLAIM = (
    "Lean environment identity and rendered-type evidence for one exact "
    "#check subject only; it is not an independent proof-correctness or "
    "theorem truth verdict."
)
AXIOM_QUERY_NONCLAIM = (
    "Lean-reported #print axioms dependency evidence for one exact "
    "declaration; bounded output does not independently establish proof "
    "correctness, theorem truth, or endorsement."
)
UNAVAILABLE_NONCLAIM = (
    "The lexical command remains review evidence, but no successful Lean "
    "query result is claimed."
)
_EXACT_NAME_RE = re.compile(
    r"^(?:_root_\.)?[^\s()[\]{}:,]+(?:\.[^\s()[\]{}:,]+)*$"
)


def audit_queries_from_elaborated_payload(
    module: str,
    source_path: str,
    source_text: str,
    payload: Mapping[str, Any],
) -> dict[str, LeanAuditQuery]:
    """Build exact command results from one completed helper environment."""

    declarations = {
        name: row
        for row in mapping_rows(payload.get("declarations"))
        for name in [declaration_name(row)]
        if name is not None
    }
    commands = extract_audit_surface(
        module,
        source_path,
        source_text,
        declaration_count=0,
    ).commands
    return {
        query.identifier: query
        for command in commands
        for query in [
            _query_from_command(
                command,
                declarations,
                payload,
            )
        ]
    }


def unavailable_audit_queries(
    module: str,
    source_path: str,
    source_text: str,
    reason: str,
) -> dict[str, LeanAuditQuery]:
    """Retain every lexical row with one explicit helper-failure state."""

    status = _failure_status(reason)
    commands = extract_audit_surface(
        module,
        source_path,
        source_text,
        declaration_count=0,
    ).commands
    return {
        command.identifier: LeanAuditQuery(
            identifier=command.identifier,
            kind=command.kind,
            containing_owner=module,
            source_path=source_path,
            subject=command.subject,
            status=status,
            reason=reason,
            backend="lean_elaborated_helper",
            authority="lean_runtime",
            nonclaim=UNAVAILABLE_NONCLAIM,
        )
        for command in commands
    }


def apply_audit_query(
    command: dict[str, Any],
    query: LeanAuditQuery | None,
) -> None:
    """Attach one query result without replacing its lexical source fields."""

    if query is None:
        return
    command["containingOwner"] = query.containing_owner
    command["referencedDeclaration"] = query.referenced_declaration
    command["referencedOwner"] = query.referenced_owner
    command["resultStatus"] = query.status
    command["resultBackend"] = query.backend
    command["resultAuthority"] = query.authority
    command["resultReason"] = query.reason
    command["resultNonclaim"] = query.nonclaim
    command["queryResult"] = query.to_dict()


def _query_from_command(
    command: AuditCommand,
    declarations: Mapping[str, Mapping[str, Any]],
    payload: Mapping[str, Any],
) -> LeanAuditQuery:
    """Resolve one supported lexical command against exact helper rows."""

    subject = _exact_subject(command)
    if subject is None:
        return _unavailable_command_query(
            command,
            "The lexical subject is not a complete bare declaration identity",
        )
    declaration = declarations.get(subject)
    if declaration is None:
        return _unresolved_command_query(command, subject, payload)
    if command.kind == "check":
        return _check_query(command, subject, declaration, payload)
    return _axiom_query(command, subject, declaration, payload)


def _check_query(
    command: AuditCommand,
    subject: str,
    declaration: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> LeanAuditQuery:
    """Return exact environment identity and bounded rendered-type evidence."""

    status, reason = _declaration_state(declaration)
    rendered_type = string_or_none(declaration.get("renderedType"))
    truncated = bool(declaration.get("renderedTypeTruncated"))
    if status == "complete" and rendered_type is None:
        status = "partial"
        reason = "Lean resolved the exact declaration but supplied no rendered type"
    elif status == "complete" and truncated:
        status = "partial"
        reason = "Lean resolved the exact declaration; rendered type was truncated"
    elif status == "complete":
        reason = "Lean resolved the exact declaration and supplied its rendered type"
    return _resolved_query(
        command,
        subject,
        declaration,
        payload,
        status=status,
        reason=reason,
        rendered_type=rendered_type,
        rendered_type_truncated=truncated,
        nonclaim=CHECK_NONCLAIM,
    )


def _axiom_query(
    command: AuditCommand,
    subject: str,
    declaration: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> LeanAuditQuery:
    """Return one bounded Lean ``#print axioms``-equivalent result."""

    declaration_status, declaration_reason = _declaration_state(declaration)
    axioms = bounded_strings(
        declaration.get("axioms"),
        cap=MAX_DEPENDENCIES,
        authority="lean_environment",
    )
    status, reason = _axiom_state(
        declaration_status,
        declaration_reason,
        axioms,
    )
    return _resolved_query(
        command,
        subject,
        declaration,
        payload,
        status=status,
        reason=reason,
        axioms=axioms,
        nonclaim=AXIOM_QUERY_NONCLAIM,
    )


def _resolved_query(
    command: AuditCommand,
    subject: str,
    declaration: Mapping[str, Any],
    payload: Mapping[str, Any],
    *,
    status: str,
    reason: str,
    rendered_type: str | None = None,
    rendered_type_truncated: bool = False,
    axioms: BoundedStrings | None = None,
    nonclaim: str,
) -> LeanAuditQuery:
    """Build one result after an exact environment declaration match."""

    return LeanAuditQuery(
        identifier=command.identifier,
        kind=command.kind,
        containing_owner=command.module,
        source_path=command.path,
        subject=command.subject,
        status=status,
        reason=reason,
        referenced_declaration=subject,
        referenced_owner=_declaration_owner(
            declaration,
            subject,
            command.module,
        ),
        rendered_type=rendered_type,
        rendered_type_truncated=rendered_type_truncated,
        axioms=axioms or _not_applicable_axioms(),
        helper_version=_helper_version(payload),
        lean_version=string_or_none(payload.get("leanVersion")),
        nonclaim=nonclaim,
    )


def _unresolved_command_query(
    command: AuditCommand,
    subject: str,
    payload: Mapping[str, Any],
) -> LeanAuditQuery:
    """Build an exact negative lookup from a completed helper environment."""

    return LeanAuditQuery(
        identifier=command.identifier,
        kind=command.kind,
        containing_owner=command.module,
        source_path=command.path,
        subject=command.subject,
        status="unresolved",
        reason=(
            f"Lean's completed environment contained no exact declaration "
            f"named {subject}"
        ),
        helper_version=_helper_version(payload),
        lean_version=string_or_none(payload.get("leanVersion")),
        nonclaim=UNAVAILABLE_NONCLAIM,
    )


def _unavailable_command_query(
    command: AuditCommand,
    reason: str,
) -> LeanAuditQuery:
    """Build an unavailable result while retaining lexical command identity."""

    return LeanAuditQuery(
        identifier=command.identifier,
        kind=command.kind,
        containing_owner=command.module,
        source_path=command.path,
        subject=command.subject,
        status="unavailable",
        reason=reason,
        nonclaim=UNAVAILABLE_NONCLAIM,
    )


def _exact_subject(command: AuditCommand) -> str | None:
    """Return a complete bare name without applying heuristic resolution."""

    subject = command.subject.strip()
    if (
        command.status != "lexical"
        or command.subject_truncated
        or not _EXACT_NAME_RE.fullmatch(subject)
    ):
        return None
    return subject.removeprefix("_root_.")


def _declaration_state(
    declaration: Mapping[str, Any],
) -> tuple[str, str]:
    """Normalize helper declaration state and its required reason."""

    status = str(declaration.get("status") or "unavailable")
    reason = string_or_none(declaration.get("reason"))
    if status == "complete":
        return status, ""
    if status == "partial":
        return status, reason or "Lean supplied a partial declaration surface"
    failure = reason or "Lean declaration evidence was unavailable"
    return _failure_status(failure), failure


def _axiom_state(
    declaration_status: str,
    declaration_reason: str,
    axioms: BoundedStrings,
) -> tuple[str, str]:
    """Combine declaration and bounded axiom-collection completeness."""

    if declaration_status != "complete":
        return declaration_status, declaration_reason
    if axioms.status == "unavailable":
        reason = axioms.reason or "Lean did not supply an axiom query result"
        return _failure_status(reason), reason
    if axioms.status == "partial" or axioms.truncated:
        return "partial", (
            axioms.reason
            or "Lean supplied a bounded partial axiom query result"
        )
    return "complete", "Lean supplied the exact declaration's axiom query result"


def _declaration_owner(
    declaration: Mapping[str, Any],
    subject: str,
    containing_owner: str,
) -> str | None:
    """Return helper-owned module identity with a local-only fallback."""

    owner = string_or_none(declaration.get("ownerModule"))
    if owner is not None:
        return owner
    if subject == containing_owner or subject.startswith(f"{containing_owner}."):
        return containing_owner
    return None


def _not_applicable_axioms() -> BoundedStrings:
    """Return an explicit non-applicable collection for ``#check``."""

    return BoundedStrings(
        status="unavailable",
        reason="axiom collection is not applicable to #check",
        authority="lean_environment",
    )


def _helper_version(payload: Mapping[str, Any]) -> str | None:
    """Return existing helper-version provenance without inventing it."""

    return string_or_none(
        payload.get("helperVersion")
        or payload.get("version")
    )


def _failure_status(reason: str) -> str:
    """Distinguish timeout evidence from other unavailable helper states."""

    normalized = reason.casefold()
    return (
        "timeout"
        if "timed out" in normalized or "timeout" in normalized
        else "unavailable"
    )


__all__ = [
    "apply_audit_query",
    "audit_queries_from_elaborated_payload",
    "unavailable_audit_queries",
]
