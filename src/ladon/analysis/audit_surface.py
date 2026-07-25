"""Bounded lexical review surfaces for Lean audit commands.

This module records source intent only.  It does not invoke Lean, resolve a
name, calculate an axiom closure, or interpret a resource setting as observed
runtime.  Optional Lean enrichment belongs to the existing extraction runtime
and can join these rows by their stable identifiers.

Resource directives remain evidence rows unless a project explicitly promotes
their source text through the generic source-pattern policy.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable

from ladon.extraction import mask_lean_comments_and_strings


MAX_SUBJECT_CHARACTERS = 256
LEXICAL_AUTHORITY = "lexical_text"
CHECK_NONCLAIM = (
    "Lexical #check intent only; not name resolution, elaboration, proof "
    "completion, theorem endorsement, or theorem truth."
)
AXIOM_NONCLAIM = (
    "Lexical #print axioms intent only; no axiom set, transitive trust "
    "footprint, proof correctness, or theorem truth was established."
)
RESOURCE_NONCLAIM = (
    "Lexical resource-setting evidence only; not measured runtime, budget "
    "consumption, proof failure, proof authority, or theorem truth."
)
RESULT_UNAVAILABLE_NONCLAIM = (
    "No Lean query result is available; the lexical command remains source "
    "intent only."
)

_CHECK_RE = re.compile(
    r"(?m)^[ \t]*(?P<keyword>#check)(?=[ \t]|$)(?P<subject>[^\n]*)"
)
_PRINT_AXIOMS_RE = re.compile(
    r"(?m)^[ \t]*(?P<keyword>#print[ \t]+axioms)(?=[ \t]|$)"
    r"(?P<subject>[^\n]*)"
)
_RESOURCE_RE = re.compile(
    r"(?m)^[ \t]*(?P<keyword>set_option)[ \t]+"
    r"(?P<option>maxHeartbeats|maxRecDepth)(?=[ \t]|$)"
    r"(?P<body>[^\n]*)"
)
_IN_TOKEN_RE = re.compile(r"(?:^|\s)in(?:\s|$)")
_NUMERIC_RE = re.compile(r"[0-9]+")


@dataclass(frozen=True)
class SourcePosition:
    """One one-based source position."""

    line: int
    column: int
    offset: int

    def to_dict(self) -> dict[str, int]:
        """Return the canonical source-position shape."""

        return {
            "line": self.line,
            "column": self.column,
            "offset": self.offset,
        }


@dataclass(frozen=True)
class SourceRange:
    """One half-open source range."""

    start: SourcePosition
    end: SourcePosition

    def to_dict(self) -> dict[str, dict[str, int]]:
        """Return the canonical source-range shape."""

        return {"start": self.start.to_dict(), "end": self.end.to_dict()}


@dataclass(frozen=True)
class AuditDiagnostic:
    """One stable lexical extraction diagnostic."""

    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        """Return a report-ready diagnostic row."""

        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class AuditCommand:
    """A bounded lexical ``#check`` or ``#print axioms`` command."""

    identifier: str
    kind: str
    module: str
    path: str
    source_range: SourceRange
    subject: str
    subject_total_characters: int
    subject_truncated: bool
    status: str
    diagnostics: tuple[AuditDiagnostic, ...]
    backend: str
    authority: str
    referenced_declaration: str | None
    referenced_owner: str | None
    result_status: str
    result_authority: str | None
    result_reason: str
    nonclaim: str

    def to_dict(self) -> dict[str, Any]:
        """Return the deterministic lexical audit-command shape."""

        return {
            "id": self.identifier,
            "kind": self.kind,
            "module": self.module,
            "path": self.path,
            "sourceRange": self.source_range.to_dict(),
            "subject": self.subject,
            "subjectTotalCharacters": self.subject_total_characters,
            "subjectTruncated": self.subject_truncated,
            "status": self.status,
            "diagnostics": [row.to_dict() for row in self.diagnostics],
            "backend": self.backend,
            "authority": self.authority,
            "containingOwner": self.module,
            "containingPopulation": None,
            "referencedDeclaration": self.referenced_declaration,
            "referencedOwner": self.referenced_owner,
            "referencedPopulation": None,
            "referencedBackend": None,
            "resultStatus": self.result_status,
            "resultBackend": None,
            "resultAuthority": self.result_authority,
            "resultReason": self.result_reason,
            "resultNonclaim": RESULT_UNAVAILABLE_NONCLAIM,
            "queryResult": None,
            "nonclaim": self.nonclaim,
        }


@dataclass(frozen=True)
class ResourceDirective:
    """A bounded lexical Lean resource-option directive."""

    identifier: str
    option: str
    module: str
    path: str
    source_range: SourceRange
    raw_value: str
    numeric_value: int | None
    normalized_meaning: str | None
    lexical_scope: str
    status: str
    diagnostics: tuple[AuditDiagnostic, ...]
    backend: str = "text"
    authority: str = LEXICAL_AUTHORITY
    nonclaim: str = RESOURCE_NONCLAIM

    def to_dict(self) -> dict[str, Any]:
        """Return the deterministic resource-directive shape."""

        return {
            "id": self.identifier,
            "option": self.option,
            "module": self.module,
            "path": self.path,
            "sourceRange": self.source_range.to_dict(),
            "rawValue": self.raw_value,
            "numericValue": self.numeric_value,
            "normalizedMeaning": self.normalized_meaning,
            "lexicalScope": self.lexical_scope,
            "status": self.status,
            "diagnostics": [row.to_dict() for row in self.diagnostics],
            "backend": self.backend,
            "authority": self.authority,
            "nonclaim": self.nonclaim,
        }


@dataclass(frozen=True)
class AuditSurface:
    """All lexical audit facts for one selected source module."""

    module: str
    path: str
    declaration_count: int
    command_only: bool
    commands: tuple[AuditCommand, ...]
    resource_directives: tuple[ResourceDirective, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return one canonical, deterministically ordered surface."""

        commands = sorted(self.commands, key=_row_sort_key)
        directives = sorted(self.resource_directives, key=_row_sort_key)
        return {
            "module": self.module,
            "path": self.path,
            "declarationCount": self.declaration_count,
            "commandOnly": self.command_only,
            "summary": {
                "auditCommands": len(commands),
                "resourceDirectives": len(directives),
            },
            "auditCommands": [row.to_dict() for row in commands],
            "resourceDirectives": [row.to_dict() for row in directives],
        }


def extract_audit_surface(
    module: str,
    path: str,
    text: str,
    *,
    declaration_count: int,
    subject_limit: int = MAX_SUBJECT_CHARACTERS,
) -> AuditSurface:
    """Extract bounded audit facts without invoking Lean."""

    normalized_module = _normalized_module(module)
    normalized_path = _normalized_relative_path(path)
    if declaration_count < 0:
        raise ValueError("declaration_count must be non-negative")
    if subject_limit < 1:
        raise ValueError("subject_limit must be positive")
    if not audit_surface_candidate(text):
        return AuditSurface(
            module=normalized_module,
            path=normalized_path,
            declaration_count=declaration_count,
            command_only=False,
            commands=(),
            resource_directives=(),
        )
    masked = mask_lean_comments_and_strings(text)
    commands = tuple(
        sorted(
            _audit_commands(
                normalized_module,
                normalized_path,
                text,
                masked,
                subject_limit,
            ),
            key=_row_sort_key,
        )
    )
    directives = tuple(
        sorted(
            _resource_directives(
                normalized_module,
                normalized_path,
                text,
                masked,
            ),
            key=_row_sort_key,
        )
    )
    return AuditSurface(
        module=normalized_module,
        path=normalized_path,
        declaration_count=declaration_count,
        command_only=bool(commands) and declaration_count == 0,
        commands=commands,
        resource_directives=directives,
    )


def audit_surface_candidate(text: str) -> bool:
    """Cheaply exclude sources that cannot contain a supported audit surface."""

    return (
        "#check" in text
        or "#print" in text
        or "maxHeartbeats" in text
        or "maxRecDepth" in text
    )


def _audit_commands(
    module: str,
    path: str,
    text: str,
    masked: str,
    subject_limit: int,
) -> Iterable[AuditCommand]:
    """Yield supported commands in stable source order."""

    matches = [
        ("check", match, CHECK_NONCLAIM)
        for match in _CHECK_RE.finditer(masked)
    ]
    matches.extend(
        ("print_axioms", match, AXIOM_NONCLAIM)
        for match in _PRINT_AXIOMS_RE.finditer(masked)
    )
    for kind, match, nonclaim in sorted(matches, key=lambda row: row[1].start()):
        yield _audit_command(
            module,
            path,
            text,
            masked,
            kind,
            match,
            nonclaim,
            subject_limit,
        )


def _audit_command(
    module: str,
    path: str,
    text: str,
    masked: str,
    kind: str,
    match: re.Match[str],
    nonclaim: str,
    subject_limit: int,
) -> AuditCommand:
    """Build one typed command from an offset-preserving match."""

    full_subject = _visible_text(
        text,
        masked,
        match.start("subject"),
        match.end("subject"),
    )
    subject, truncated = _bounded_text(full_subject, subject_limit)
    diagnostic = _subject_diagnostic(full_subject)
    start = match.start("keyword")
    end = _visible_end(masked, start, match.end())
    source_range = _source_range(masked, start, end)
    identifier = _stable_id(
        "audit",
        {
            "module": module,
            "kind": kind,
            "line": source_range.start.line,
            "column": source_range.start.column,
            "subject": full_subject,
        },
    )
    return AuditCommand(
        identifier=identifier,
        kind=kind,
        module=module,
        path=path,
        source_range=source_range,
        subject=subject,
        subject_total_characters=len(full_subject),
        subject_truncated=truncated,
        status="unparsed" if diagnostic else "lexical",
        diagnostics=(diagnostic,) if diagnostic else (),
        backend="text",
        authority=LEXICAL_AUTHORITY,
        referenced_declaration=None,
        referenced_owner=None,
        result_status="unavailable",
        result_authority=None,
        result_reason="Lean enrichment was not requested by lexical extraction",
        nonclaim=nonclaim,
    )


def _resource_directives(
    module: str,
    path: str,
    text: str,
    masked: str,
) -> Iterable[ResourceDirective]:
    """Yield supported numeric or explicitly unparsed option directives."""

    for match in _RESOURCE_RE.finditer(masked):
        option = match.group("option")
        body = _visible_text(text, masked, match.start("body"), match.end("body"))
        raw_value, lexical_scope = _directive_value_and_scope(body)
        numeric_value = (
            int(raw_value) if _NUMERIC_RE.fullmatch(raw_value) else None
        )
        diagnostic = _resource_diagnostic(option, raw_value)
        start = match.start("keyword")
        end = _visible_end(masked, start, match.end())
        source_range = _source_range(masked, start, end)
        yield ResourceDirective(
            identifier=_stable_id(
                "resource",
                {
                    "module": module,
                    "option": option,
                    "line": source_range.start.line,
                    "column": source_range.start.column,
                    "rawValue": raw_value,
                },
            ),
            option=option,
            module=module,
            path=path,
            source_range=source_range,
            raw_value=raw_value,
            numeric_value=numeric_value,
            normalized_meaning=_resource_meaning(option, numeric_value),
            lexical_scope=lexical_scope,
            status="unparsed" if diagnostic else "complete",
            diagnostics=(diagnostic,) if diagnostic else (),
        )


def _directive_value_and_scope(body: str) -> tuple[str, str]:
    """Separate a bounded option value from an optional ``in`` scope."""

    scope_match = _IN_TOKEN_RE.search(body)
    if scope_match is None:
        return body.strip(), "module"
    return body[:scope_match.start()].strip(), "command_local"


def _resource_meaning(option: str, value: int | None) -> str | None:
    """Normalize only meanings established by the supported lexical contract."""

    if value is None:
        return None
    if option == "maxHeartbeats" and value == 0:
        return "unlimited"
    return "finite"


def _subject_diagnostic(subject: str) -> AuditDiagnostic | None:
    """Explain why a detected command has no safely extracted subject."""

    if subject:
        return None
    return AuditDiagnostic(
        code="audit.subject_unparsed",
        message=(
            "The bounded lexical scanner detected the command but could not "
            "extract a non-comment, non-string subject"
        ),
    )


def _resource_diagnostic(
    option: str,
    raw_value: str,
) -> AuditDiagnostic | None:
    """Return a fail-closed diagnostic for unsupported option expressions."""

    if _NUMERIC_RE.fullmatch(raw_value):
        return None
    return AuditDiagnostic(
        code="audit.resource_value_unparsed",
        message=(
            f"{option} requires one literal non-negative integer in the "
            "bounded lexical surface; the value was retained without "
            "normalization"
        ),
    )


def _visible_text(
    text: str,
    masked: str,
    start: int,
    end: int,
) -> str:
    """Return normalized source characters still visible after masking."""

    visible = "".join(
        original if mask_char != " " else " "
        for original, mask_char in zip(text[start:end], masked[start:end])
    )
    return " ".join(visible.split())


def _visible_end(masked: str, start: int, end: int) -> int:
    """Return an exclusive range end with masked trailing trivia removed."""

    while end > start and masked[end - 1].isspace():
        end -= 1
    return end


def _source_range(text: str, start: int, end: int) -> SourceRange:
    """Build one one-based half-open source range from offsets."""

    return SourceRange(_position(text, start), _position(text, end))


def _position(text: str, offset: int) -> SourcePosition:
    """Translate an offset without changing the indexed text."""

    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset) + 1
    return SourcePosition(line=line, column=offset - line_start + 1, offset=offset)


def _bounded_text(text: str, limit: int) -> tuple[str, bool]:
    """Return a deterministic character-bounded prefix."""

    return (text, False) if len(text) <= limit else (text[:limit], True)


def _stable_id(namespace: str, payload: dict[str, Any]) -> str:
    """Hash semantic identity fields independently of display wording."""

    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"ladon.{namespace}.{hashlib.sha256(encoded).hexdigest()[:20]}"


def _row_sort_key(row: AuditCommand | ResourceDirective) -> tuple[int, int, str]:
    """Order heterogeneous rows by source anchor then stable identity."""

    return (
        row.source_range.start.line,
        row.source_range.start.column,
        row.identifier,
    )


def _normalized_module(module: str) -> str:
    """Require a non-empty normalized Lean module identity."""

    normalized = module.strip()
    if not normalized:
        raise ValueError("module must be non-empty")
    return normalized


def _normalized_relative_path(path: str) -> str:
    """Require a portable repository-relative source path."""

    normalized = path.replace("\\", "/").strip()
    candidate = PurePosixPath(normalized)
    if (
        not normalized
        or candidate.is_absolute()
        or ".." in candidate.parts
    ):
        raise ValueError("path must be a non-empty repository-relative path")
    return candidate.as_posix()
