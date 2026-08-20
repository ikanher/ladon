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
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from ladon.ir import LeanResourceSetting
from ladon.lexical_mask import mask_lean_source

MAX_SUBJECT_CHARACTERS = 256
MAX_SUBJECT_CONTINUATION_LINES = 4
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
    r"(?m)^[ \t]*(?P<keyword>#check)(?=[ \t]|$)(?P<tail>[^\n]*)"
)
_PRINT_AXIOMS_RE = re.compile(
    r"(?m)^[ \t]*(?P<keyword>#print[ \t]+axioms)(?=[ \t]|$)"
    r"(?P<tail>[^\n]*)"
)
_BARE_SUBJECT_RE = re.compile(
    r"(?:_root_\.)?[^\W\d][\w']*(?:\.[^\W\d][\w']*)*",
    re.UNICODE,
)
_CONTINUATION_BOUNDARY_RE = re.compile(
    r"(?:#check|#print|set_option|import|namespace|section|end|mutual|"
    r"theorem|lemma|def|abbrev|instance|structure|class|inductive|"
    r"opaque|axiom|constant)\b"
)


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
class _AuditSubject:
    """One bounded subject parse and its command-range endpoint."""

    text: str
    end_offset: int
    diagnostic: AuditDiagnostic | None


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
            "candidateStatus": "unavailable",
            "candidateMatchCount": 0,
            "candidateMatches": [],
            "candidateDeclarationId": None,
            "candidateReferencedDeclaration": None,
            "candidateReferencedOwner": None,
            "candidateAuthority": None,
            "candidateSourceIndexFingerprint": None,
            "candidateCoverage": None,
            "candidateNonclaim": (
                "No lexical source-index candidate join has been attached."
            ),
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
    resource_settings: Sequence[LeanResourceSetting] = (),
) -> AuditSurface:
    """Extract audit commands and adapt canonical indexed resource settings."""

    normalized_module = _normalized_module(module)
    normalized_path = _normalized_relative_path(path)
    commands = scan_audit_commands(
        normalized_module,
        normalized_path,
        text,
        mask_lean_source(text).lexical,
        subject_limit=subject_limit,
    )
    return audit_surface_from_index(
        normalized_module,
        normalized_path,
        declaration_count=declaration_count,
        audit_commands=commands,
        resource_settings=resource_settings,
    )


def audit_surface_from_index(
    module: str,
    path: str,
    *,
    declaration_count: int,
    audit_commands: Sequence[AuditCommand] = (),
    resource_settings: Sequence[LeanResourceSetting] = (),
) -> AuditSurface:
    """Adapt canonical source-index rows without reopening or rescanning source."""

    normalized_module = _normalized_module(module)
    normalized_path = _normalized_relative_path(path)
    if declaration_count < 0:
        raise ValueError("declaration_count must be non-negative")
    commands = tuple(
        sorted(
            (
                _validated_audit_command(
                    command,
                    module=normalized_module,
                    path=normalized_path,
                )
                for command in audit_commands
            ),
            key=_row_sort_key,
        )
    )
    directives = tuple(
        sorted(
            (
                _resource_directive(
                    setting,
                    module=normalized_module,
                    path=normalized_path,
                )
                for setting in resource_settings
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

    return "#check" in text or "#print" in text


def scan_audit_commands(
    module: str,
    path: str,
    text: str,
    masked: str,
    *,
    subject_limit: int = MAX_SUBJECT_CHARACTERS,
) -> tuple[AuditCommand, ...]:
    """Scan one already-masked source into canonical audit-command rows."""

    normalized_module = _normalized_module(module)
    normalized_path = _normalized_relative_path(path)
    if len(masked) != len(text):
        raise ValueError("audit-command source mask must preserve byte offsets")
    if subject_limit < 1:
        raise ValueError("subject_limit must be positive")
    matches = [
        ("check", match, CHECK_NONCLAIM)
        for match in _CHECK_RE.finditer(masked)
    ]
    matches.extend(
        ("print_axioms", match, AXIOM_NONCLAIM)
        for match in _PRINT_AXIOMS_RE.finditer(masked)
    )
    return tuple(
        _audit_command(
            normalized_module,
            normalized_path,
            text,
            masked,
            kind,
            match,
            nonclaim,
            subject_limit,
        )
        for kind, match, nonclaim in sorted(
            matches,
            key=lambda row: row[1].start(),
        )
    )


def _validated_audit_command(
    command: AuditCommand,
    *,
    module: str,
    path: str,
) -> AuditCommand:
    """Reject canonical rows attached to a different module or source path."""

    if command.module != module or command.path != path:
        raise ValueError("canonical audit command does not belong to the audit surface")
    return command


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

    parsed = _command_subject(text, masked, match)
    full_subject = parsed.text
    subject, truncated = _bounded_text(full_subject, subject_limit)
    diagnostic = parsed.diagnostic
    start = match.start("keyword")
    end = parsed.end_offset
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


def _command_subject(
    text: str,
    masked: str,
    match: re.Match[str],
) -> _AuditSubject:
    """Parse a same-line or one-line bare declaration subject."""

    tail_start = match.start("tail")
    tail_end = match.end("tail")
    same_line = _visible_text(text, masked, tail_start, tail_end)
    if same_line:
        return _classified_subject(
            same_line,
            _visible_end(masked, match.start("keyword"), tail_end),
            multiline=False,
        )
    continuation = _continuation_range(text, masked, tail_end)
    if continuation is None:
        return _AuditSubject(
            text="",
            end_offset=_original_visible_end(
                text,
                match.start("keyword"),
                tail_end,
            ),
            diagnostic=_missing_subject_diagnostic(),
        )
    continuation_start, continuation_end = continuation
    subject = _visible_text(
        text,
        masked,
        continuation_start,
        continuation_end,
    )
    if _BARE_SUBJECT_RE.fullmatch(subject):
        return _AuditSubject(
            text=subject,
            end_offset=_visible_end(
                masked,
                continuation_start,
                continuation_end,
            ),
            diagnostic=None,
        )
    return _AuditSubject(
        text=subject,
        end_offset=_original_visible_end(
            text,
            match.start("keyword"),
            continuation_end,
        ),
        diagnostic=_unsupported_subject_diagnostic(multiline=True),
    )


def _classified_subject(
    subject: str,
    end_offset: int,
    *,
    multiline: bool,
) -> _AuditSubject:
    """Classify one non-empty normalized subject conservatively."""

    diagnostic = (
        None
        if _BARE_SUBJECT_RE.fullmatch(subject)
        else _unsupported_subject_diagnostic(multiline=multiline)
    )
    return _AuditSubject(subject, end_offset, diagnostic)


def _continuation_range(
    text: str,
    masked: str,
    line_end: int,
) -> tuple[int, int] | None:
    """Return one bounded continuation envelope without crossing a command."""

    if line_end >= len(masked) or masked[line_end] != "\n":
        return None
    start = line_end + 1
    first_end = _line_end(masked, start)
    first_visible = masked[start:first_end].strip()
    if _CONTINUATION_BOUNDARY_RE.match(first_visible):
        return None
    if not first_visible:
        return (
            (start, first_end)
            if text[start:first_end].strip()
            else None
        )
    if _BARE_SUBJECT_RE.fullmatch(first_visible):
        return start, first_end
    return start, _unsupported_continuation_end(masked, start)


def _unsupported_continuation_end(masked: str, start: int) -> int:
    """Bound an unsupported multiline expression for source navigation."""

    end = _line_end(masked, start)
    cursor = end + int(end < len(masked) and masked[end] == "\n")
    lines = 1
    while cursor < len(masked) and lines < MAX_SUBJECT_CONTINUATION_LINES:
        candidate_end = _line_end(masked, cursor)
        line = masked[cursor:candidate_end]
        visible = line.strip()
        if visible and (
            not line[:1].isspace()
            or _CONTINUATION_BOUNDARY_RE.match(visible)
        ):
            break
        end = candidate_end
        cursor = candidate_end + int(
            candidate_end < len(masked)
            and masked[candidate_end] == "\n"
        )
        lines += 1
    return end


def _line_end(text: str, start: int) -> int:
    """Return the exclusive end of the physical line at ``start``."""

    end = text.find("\n", start)
    return len(text) if end < 0 else end


def _resource_directive(
    setting: LeanResourceSetting,
    *,
    module: str,
    path: str,
) -> ResourceDirective:
    """Adapt one canonical source-index row without reparsing its source."""

    if setting.module != module or setting.path != path:
        raise ValueError(
            "canonical resource setting does not belong to the audit surface"
        )
    source_range = SourceRange(
        start=SourcePosition(
            line=setting.line,
            column=setting.column,
            offset=setting.start_offset,
        ),
        end=SourcePosition(
            line=setting.line,
            column=setting.column + setting.end_offset - setting.start_offset,
            offset=setting.end_offset,
        ),
    )
    diagnostic = _resource_diagnostic(setting)
    return ResourceDirective(
        identifier=setting.identifier,
        option=setting.option,
        module=setting.module,
        path=setting.path,
        source_range=source_range,
        raw_value=setting.raw_value,
        numeric_value=setting.numeric_value,
        normalized_meaning=setting.normalized_meaning,
        lexical_scope=setting.lexical_scope,
        status=setting.status,
        diagnostics=(diagnostic,) if diagnostic else (),
        authority=setting.authority,
        nonclaim=setting.nonclaim,
    )


def _missing_subject_diagnostic() -> AuditDiagnostic:
    """Explain why a detected command has no safely extracted subject."""

    return AuditDiagnostic(
        code="audit.subject_unparsed",
        message=(
            "The bounded lexical scanner detected the command but could not "
            "extract a non-comment, non-string subject"
        ),
    )


def _unsupported_subject_diagnostic(
    *,
    multiline: bool,
) -> AuditDiagnostic:
    """Return a structured reason for a non-bare subject expression."""

    placement = "multiline " if multiline else ""
    return AuditDiagnostic(
        code="audit.subject_syntax_unsupported",
        message=(
            f"The bounded lexical scanner retained the {placement}command "
            "range but supports only one bare declaration subject"
        ),
    )


def _resource_diagnostic(
    setting: LeanResourceSetting,
) -> AuditDiagnostic | None:
    """Adapt the canonical fail-closed normalization reason."""

    if setting.status == "parsed":
        return None
    return AuditDiagnostic(
        code="audit.resource_value_unparsed",
        message=(
            setting.reason
            or f"{setting.option} resource normalization is unavailable"
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


def _original_visible_end(text: str, start: int, end: int) -> int:
    """Trim source whitespace while retaining unsupported literal syntax."""

    while end > start and text[end - 1].isspace():
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
