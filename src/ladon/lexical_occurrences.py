"""Typed lexical option, resource, tactic-token, and attribute occurrences.

The helpers operate only on an immutable source string, its already-computed
comment/string mask, and canonical declaration block ranges.  They do not read
files, remask source, invoke Lean, or interpret token occurrences as elaborated
proof behavior.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from ladon.ir import (
    LeanOptionOccurrence,
    LeanProofMechanismOccurrence,
    LeanResourceSetting,
    LeanTextDeclaration,
)

LEXICAL_NAVIGATION_VERSION = "ladon-lexical-navigation-v1"
MAX_LEXICAL_VALUE_CHARACTERS = 256
RESOURCE_OPTIONS = frozenset({"maxHeartbeats", "maxRecDepth"})
TACTIC_TOKENS = (
    "aesop",
    "apply",
    "assumption",
    "by_contra",
    "by_cases",
    "cases",
    "change",
    "constructor",
    "contradiction",
    "decide",
    "exact",
    "ext",
    "fun_prop",
    "induction",
    "intro",
    "intros",
    "linarith",
    "native_decide",
    "nlinarith",
    "norm_num",
    "omega",
    "positivity",
    "rcases",
    "refine",
    "rfl",
    "ring",
    "ring_nf",
    "rw",
    "simp",
    "simpa",
    "subst",
    "tauto",
    "trivial",
    "unfold",
)
ATTRIBUTE_TOKENS = frozenset(
    {
        "aesop",
        "deprecated",
        "elab_as_elim",
        "extern",
        "ext",
        "implemented_by",
        "inherit_doc",
        "inline",
        "instance",
        "irreducible",
        "macro_inline",
        "match_pattern",
        "nolint",
        "norm_num",
        "pp_dot",
        "reducible",
        "scoped",
        "simp",
        "simps",
        "to_additive",
    }
)

_LEAN_NAME = r"[A-Za-z_][A-Za-z0-9_']*"
_LEAN_QUALIFIED_NAME = rf"{_LEAN_NAME}(?:\.{_LEAN_NAME})*"
_OPTION_RE = re.compile(
    rf"(?m)^[ \t]*(?P<keyword>set_option)[ \t]+"
    rf"(?P<option>{_LEAN_QUALIFIED_NAME})(?=[ \t]|$)"
    r"(?P<body>[^\n]*)"
)
_IN_TOKEN_RE = re.compile(r"(?:^|\s)in(?:\s|$)")
_TACTIC_RE = re.compile(
    rf"(?<![A-Za-z0-9_'.])(?P<token>{'|'.join(TACTIC_TOKENS)})"
    r"(?![A-Za-z0-9_'])"
)
_ATTRIBUTE_BLOCK_RE = re.compile(r"@\[(?P<body>[^\]\n]+)\]")
_ATTRIBUTE_NAME_RE = re.compile(_LEAN_QUALIFIED_NAME)
_NUMERIC_RE = re.compile(r"[0-9]+")


def option_matches(masked: str) -> tuple[re.Match[str], ...]:
    """Return safely recognized generic ``set_option`` command starts."""

    return tuple(_OPTION_RE.finditer(masked))


def option_occurrence(
    text: str,
    masked: str,
    match: re.Match[str],
    declarations: Sequence[LeanTextDeclaration],
    *,
    module: str,
    path: str,
    scope_context_id: str,
) -> LeanOptionOccurrence:
    """Build one generic lexical option row with bounded raw evidence."""

    option = match.group("option")
    raw_value, command_local = _option_value(text, masked, match)
    start = match.start("keyword")
    end = _visible_end(masked, start, match.end())
    line, column = _position(masked, start)
    containing = _option_declaration(
        masked,
        start,
        end,
        column,
        command_local,
        declarations,
    )
    bounded, total, truncated = bounded_lexical_text(raw_value)
    status = "parsed" if raw_value else "unresolved"
    return LeanOptionOccurrence(
        identifier=_stable_id(
            "option",
            {
                "version": LEXICAL_NAVIGATION_VERSION,
                "module": module,
                "path": path,
                "option": option,
                "startOffset": start,
                "rawValue": raw_value,
            },
        ),
        module=module,
        path=path,
        option=option,
        option_class=_option_class(option),
        raw_value=bounded,
        raw_value_total_characters=total,
        raw_value_truncated=truncated,
        lexical_scope=_option_scope(command_local, containing, column),
        line=line,
        column=column,
        start_offset=start,
        end_offset=end,
        status=status,
        reason=(
            None if status == "parsed" else "set_option has no bounded lexical value"
        ),
        declaration_id=containing.identifier if containing else None,
        declaration_candidate=_declaration_candidate(containing),
        scope_context_id=scope_context_id,
    )


def _declaration_candidate(
    declaration: LeanTextDeclaration | None,
) -> str | None:
    if declaration is None:
        return None
    return declaration.candidate_name or declaration.name


def _option_value(
    text: str,
    masked: str,
    match: re.Match[str],
) -> tuple[str, bool]:
    body_start = match.start("body")
    body_end = match.end("body")
    scope = _IN_TOKEN_RE.search(masked[body_start:body_end])
    value_end = body_end if scope is None else body_start + scope.start()
    visible_end = _visible_end(masked, body_start, value_end)
    return text[body_start:visible_end].strip(), scope is not None


def _option_declaration(
    masked: str,
    start: int,
    end: int,
    column: int,
    command_local: bool,
    declarations: Sequence[LeanTextDeclaration],
) -> LeanTextDeclaration | None:
    containing = _indented_containing_declaration(
        start,
        column,
        declarations,
    )
    if containing is not None or not command_local:
        return containing
    return _following_command_local_declaration(masked, end, declarations)


def _indented_containing_declaration(
    start: int,
    column: int,
    declarations: Sequence[LeanTextDeclaration],
) -> LeanTextDeclaration | None:
    if column <= 1:
        return None
    return next(
        (
            declaration
            for declaration in declarations
            if _declaration_block_contains(declaration, start)
        ),
        None,
    )


def _declaration_block_contains(
    declaration: LeanTextDeclaration,
    offset: int,
) -> bool:
    start = declaration.block_start_offset
    end = declaration.block_end_offset
    return start is not None and end is not None and start <= offset < end


def _following_command_local_declaration(
    masked: str,
    end: int,
    declarations: Sequence[LeanTextDeclaration],
) -> LeanTextDeclaration | None:
    following = next(
        (
            declaration
            for declaration in declarations
            if _declaration_start(declaration) > end
        ),
        None,
    )
    if following is None:
        return None
    return (
        following
        if not masked[end:_declaration_start(following)].strip()
        else None
    )


def _declaration_start(declaration: LeanTextDeclaration) -> int:
    start = declaration.block_start_offset
    return start if start is not None else declaration.start_offset


def _option_scope(
    command_local: bool,
    declaration: LeanTextDeclaration | None,
    column: int,
) -> str:
    if command_local:
        return "command_local"
    if declaration is not None and column > 1:
        return "declaration_block"
    return "module"


def _option_class(option: str) -> str:
    if option in RESOURCE_OPTIONS:
        return "resource"
    if option.startswith("linter."):
        return "linter"
    if option.startswith("pp."):
        return "pretty_printer"
    if option in {"autoImplicit", "relaxedAutoImplicit"}:
        return "elaboration"
    return "generic"


def resource_setting(
    option: LeanOptionOccurrence,
) -> LeanResourceSetting | None:
    """Normalize only supported literal resource-option meanings."""

    if option.option not in RESOURCE_OPTIONS:
        return None
    numeric = _resource_numeric_value(option)
    meaning = _resource_meaning(option.option, numeric)
    status = "parsed" if numeric is not None else "unresolved"
    return LeanResourceSetting(
        identifier=_stable_id(
            "resource",
            {
                "version": LEXICAL_NAVIGATION_VERSION,
                "optionRowId": option.identifier,
                "normalization": meaning,
            },
        ),
        option_row_id=option.identifier,
        module=option.module,
        path=option.path,
        option=option.option,
        raw_value=option.raw_value,
        numeric_value=numeric,
        normalized_meaning=meaning,
        lexical_scope=option.lexical_scope,
        line=option.line,
        column=option.column,
        start_offset=option.start_offset,
        end_offset=option.end_offset,
        status=status,
        reason=(
            None
            if status == "parsed"
            else "resource value is not one literal non-negative integer"
        ),
        declaration_id=option.declaration_id,
        declaration_candidate=option.declaration_candidate,
        scope_context_id=option.scope_context_id,
    )


def _resource_numeric_value(option: LeanOptionOccurrence) -> int | None:
    if option.raw_value_truncated or not _NUMERIC_RE.fullmatch(option.raw_value):
        return None
    return int(option.raw_value)


def _resource_meaning(option: str, value: int | None) -> str | None:
    if value is None:
        return None
    if option == "maxHeartbeats" and value == 0:
        return "unlimited"
    return "finite"


def proof_mechanisms(
    masked: str,
    declarations: Sequence[LeanTextDeclaration],
    *,
    module: str,
    path: str,
) -> tuple[LeanProofMechanismOccurrence, ...]:
    """Return supported tokens inside canonical declaration block ranges."""

    if "@[" not in masked and _TACTIC_RE.search(masked) is None:
        return ()
    rows: list[LeanProofMechanismOccurrence] = []
    for declaration in declarations:
        start = declaration.block_start_offset
        end = declaration.block_end_offset
        if start is None or end is None or end <= start:
            continue
        rows.extend(
            _declaration_tactic_rows(
                masked,
                declaration,
                module=module,
                path=path,
                end=end,
            )
        )
        rows.extend(
            _declaration_attribute_rows(
                masked,
                declaration,
                module=module,
                path=path,
                start=start,
                end=end,
            )
        )
    return tuple(rows)


def _declaration_tactic_rows(
    masked: str,
    declaration: LeanTextDeclaration,
    *,
    module: str,
    path: str,
    end: int,
) -> Iterable[LeanProofMechanismOccurrence]:
    proof_start = _proof_body_start(masked, declaration, end)
    if proof_start is None:
        return
    for match in _TACTIC_RE.finditer(masked[proof_start:end]):
        yield _mechanism_row(
            masked,
            declaration,
            module=module,
            path=path,
            mechanism=match.group("token"),
            kind="tactic-token",
            start=proof_start + match.start("token"),
            end=proof_start + match.end("token"),
        )


def _declaration_attribute_rows(
    masked: str,
    declaration: LeanTextDeclaration,
    *,
    module: str,
    path: str,
    start: int,
    end: int,
) -> Iterable[LeanProofMechanismOccurrence]:
    header_end = min(declaration.start_offset, end)
    for block in _ATTRIBUTE_BLOCK_RE.finditer(masked[start:header_end]):
        yield from _supported_attribute_rows(
            masked,
            declaration,
            module=module,
            path=path,
            body=block.group("body"),
            body_start=start + block.start("body"),
        )


def _supported_attribute_rows(
    masked: str,
    declaration: LeanTextDeclaration,
    *,
    module: str,
    path: str,
    body: str,
    body_start: int,
) -> Iterable[LeanProofMechanismOccurrence]:
    for match in _ATTRIBUTE_NAME_RE.finditer(body):
        attribute = match.group(0)
        if attribute.split(".")[-1] not in ATTRIBUTE_TOKENS:
            continue
        yield _mechanism_row(
            masked,
            declaration,
            module=module,
            path=path,
            mechanism=attribute,
            kind="attribute",
            start=body_start + match.start(),
            end=body_start + match.end(),
            attribute=attribute,
        )


def _proof_body_start(
    masked: str,
    declaration: LeanTextDeclaration,
    end: int,
) -> int | None:
    delimiter = masked.find(":=", declaration.end_offset, end)
    return delimiter + 2 if delimiter >= 0 else None


def _mechanism_row(
    masked: str,
    declaration: LeanTextDeclaration,
    *,
    module: str,
    path: str,
    mechanism: str,
    kind: str,
    start: int,
    end: int,
    attribute: str | None = None,
) -> LeanProofMechanismOccurrence:
    line, column = _position(masked, start)
    return LeanProofMechanismOccurrence(
        identifier=_stable_id(
            "proof-mechanism",
            {
                "version": LEXICAL_NAVIGATION_VERSION,
                "declarationId": declaration.identifier,
                "kind": kind,
                "mechanism": mechanism,
                "startOffset": start,
            },
        ),
        module=module,
        path=path,
        mechanism=mechanism,
        kind=kind,
        line=line,
        column=column,
        start_offset=start,
        end_offset=end,
        declaration_id=declaration.identifier,
        declaration_candidate=declaration.candidate_name or declaration.name,
        attribute=attribute,
        scope_context_id=declaration.scope_context_id,
    )


def bounded_lexical_text(value: str) -> tuple[str, int, bool]:
    """Return one value with explicit total and truncation state."""

    total = len(value)
    return (
        value[:MAX_LEXICAL_VALUE_CHARACTERS],
        total,
        total > MAX_LEXICAL_VALUE_CHARACTERS,
    )


def _visible_end(masked: str, start: int, end: int) -> int:
    cursor = end
    while cursor > start and masked[cursor - 1].isspace():
        cursor -= 1
    return cursor


def _position(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset) + 1
    return line, offset - line_start + 1


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:20]
    return f"ladon.lexical_{prefix.replace('-', '_')}.{digest}"


def option_order(row: LeanOptionOccurrence) -> tuple[int, int, str]:
    """Return deterministic source ordering for generic option rows."""

    return row.start_offset, row.end_offset, row.identifier


def resource_order(row: LeanResourceSetting) -> tuple[int, int, str]:
    """Return deterministic source ordering for resource rows."""

    return row.start_offset, row.end_offset, row.identifier


def mechanism_order(
    row: LeanProofMechanismOccurrence,
) -> tuple[int, int, str]:
    """Return deterministic source ordering for mechanism rows."""

    return row.start_offset, row.end_offset, row.identifier


__all__ = [
    "ATTRIBUTE_TOKENS",
    "LEXICAL_NAVIGATION_VERSION",
    "MAX_LEXICAL_VALUE_CHARACTERS",
    "RESOURCE_OPTIONS",
    "TACTIC_TOKENS",
    "bounded_lexical_text",
    "mechanism_order",
    "option_matches",
    "option_occurrence",
    "option_order",
    "proof_mechanisms",
    "resource_order",
    "resource_setting",
]
