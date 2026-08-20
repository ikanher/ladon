"""Conservative lexical declaration candidates for Lean source text.

The scanner consumes an offset-preserving comment/string mask supplied by the
text extractor.  It tracks only a documented namespace/section subset and
fails closed whenever that state is ambiguous.  Nothing here implements Lean
parsing, name resolution, or elaboration.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from ladon.ir import LeanTextDeclaration

DECLARATION_KINDS = (
    "theorem",
    "lemma",
    "def",
    "abbrev",
    "instance",
    "structure",
    "class",
    "inductive",
    "opaque",
    "axiom",
    "constant",
)
DECLARATION_MODIFIERS = (
    "local",
    "private",
    "protected",
    "noncomputable",
    "unsafe",
    "partial",
)
DECLARATION_BLOCK_NORMALIZATION_VERSION = "ladon-lexical-declaration-block-v2"
DECLARATION_SOURCE_SHAPE_NORMALIZATION_VERSION = (
    "ladon-lexical-declaration-source-shape-v2"
)
DECLARATION_ID_VERSION = "ladon-lexical-declaration-row-v1"
_LEAN_NAME = r"(?:[^\W\d]|_)[\w']*[!?]?"
_LEAN_ESCAPED_NAME = r"«[^»\n]*»"
_LEAN_NAME_COMPONENT = rf"(?:{_LEAN_NAME}|{_LEAN_ESCAPED_NAME})"
_LEAN_QUALIFIED_NAME = rf"{_LEAN_NAME_COMPONENT}(?:\.{_LEAN_NAME_COMPONENT})*"
_EXAMPLE_COMMAND_HEAD = (
    rf"(?:(?:{'|'.join(DECLARATION_MODIFIERS)})[ \t]+)*"
    r"example"
)
DECL_RE = re.compile(
    r"^[ \t]*(?:@\[[^\]\n]*\][ \t]*(?:\n[ \t]*)?)*"
    rf"(?P<modifiers>(?:(?:{'|'.join(DECLARATION_MODIFIERS)})[ \t]+)*)"
    rf"(?P<kind>{'|'.join(DECLARATION_KINDS)})\s+"
    rf"(?P<name>(?:_root_\.)?{_LEAN_QUALIFIED_NAME})",
    re.MULTILINE,
)
_SCOPE_COMMAND_RE = re.compile(
    r"(?m)^[ \t]*(?P<kind>namespace|section|end|mutual)\b"
    r"(?P<body>[^\n]*)"
)
_SCOPE_NAME_RE = re.compile(_LEAN_QUALIFIED_NAME)
_NON_DECLARATION_COMMAND_HEAD_RE = re.compile(
    r"(?P<command>"
    r"#[^\s]+"
    r"|(?:public[ \t]+)?(?:meta[ \t]+)?import"
    r"|open(?:[ \t]+scoped)?"
    r"|export"
    r"|include"
    r"|omit"
    r"|variables?"
    r"|universes?"
    r"|set_option"
    r"|attribute"
    r"|@\[[^\]\n]*\]"
    rf"|{_EXAMPLE_COMMAND_HEAD}"
    r"|(?:local[ \t]+|scoped[ \t]+)?notation"
    r"|(?:local[ \t]+|scoped[ \t]+)?(?:infixl|infixr|infix|prefix|postfix)"
    r"|(?:local[ \t]+)?syntax"
    r"|(?:local[ \t]+)?macro"
    r"|elab"
    r"|command_elab"
    r"|initialize"
    r"|builtin_initialize"
    r"|register_option"
    r"|declare_syntax_cat"
    r")(?=[ \t]|$)"
)
_SOURCE_SHAPE_TOKEN_RE = re.compile(
    rf"{_LEAN_ESCAPED_NAME}"
    r'|"(?:\\.|[^"\\])*"'
    r"|(?:0[xX][0-9A-Fa-f]+|0[bB][01]+|[0-9]+(?:\.[0-9]+)?)"
    rf"|{_LEAN_NAME}"
)
_PLAIN_WHITESPACE_RE = re.compile(r"\s+")
_SOURCE_SHAPE_KEYWORDS = frozenset(
    {
        *DECLARATION_KINDS,
        *DECLARATION_MODIFIERS,
        "as",
        "by",
        "decreasing_by",
        "deriving",
        "do",
        "else",
        "extends",
        "for",
        "from",
        "fun",
        "have",
        "if",
        "in",
        "let",
        "match",
        "return",
        "show",
        "termination_by",
        "then",
        "where",
        "with",
    }
)


@dataclass(frozen=True)
class _LexicalScopeFrame:
    """One bounded lexical frame relevant to declaration naming."""

    kind: str
    name: str | None
    namespace_segments: tuple[str, ...]
    start_offset: int
    safe: bool = True


@dataclass
class _LexicalScopeState:
    """Mutable state used only while scanning one immutable source string."""

    frames: list[_LexicalScopeFrame]
    permanently_unresolved: bool = False

    @property
    def candidate_available(self) -> bool:
        """Return whether every currently open frame is understood."""

        return not self.permanently_unresolved and all(
            frame.safe for frame in self.frames
        )

    @property
    def namespace_stack(self) -> tuple[str, ...]:
        """Flatten only namespace frames into candidate-name segments."""

        return tuple(
            segment for frame in self.frames for segment in frame.namespace_segments
        )

    @property
    def section_stack(self) -> tuple[str, ...]:
        """Retain section context without changing candidate names."""

        return tuple(
            frame.name or "<anonymous>"
            for frame in self.frames
            if frame.kind == "section"
        )


@dataclass(frozen=True)
class _IndentedBoundary:
    """One supported non-declaration command and its source indentation."""

    offset: int
    indentation: int


@dataclass
class _BlockNormalizer:
    """State machine for comment/whitespace-trivia normalization."""

    output: list[str]
    index: int = 0
    block_depth: int = 0
    line_comment: bool = False
    in_string: bool = False
    escaped: bool = False
    pending_space: bool = False

    def step(self, text: str) -> None:
        """Consume one lexical unit while preserving string literal bytes."""

        pair = text[self.index : self.index + 2]
        char = text[self.index]
        if self.line_comment:
            self._consume_line_comment(text)
        elif self.block_depth:
            self._consume_block_comment(pair)
        elif self.in_string:
            self._consume_string(char)
        elif char == "«":
            self._append_escaped_identifier(text)
        elif pair in {"--", "/-"}:
            self._open_comment(pair)
        elif char.isspace():
            self.pending_space = True
            self.index += 1
        else:
            self._append_visible(char)

    def _consume_line_comment(self, text: str) -> None:
        """Skip one comment body in C-backed search instead of per character."""

        newline = text.find("\n", self.index)
        self.index = len(text) if newline < 0 else newline + 1
        self.line_comment = False
        self.pending_space = True

    def _consume_block_comment(self, pair: str) -> None:
        if pair == "/-":
            self.block_depth += 1
            self.index += 2
        elif pair == "-/":
            self.block_depth -= 1
            self.index += 2
        else:
            self.index += 1
        self.pending_space = True

    def _consume_string(self, char: str) -> None:
        self.output.append(char)
        if self.escaped:
            self.escaped = False
        elif char == "\\":
            self.escaped = True
        elif char == '"':
            self.in_string = False
        self.index += 1

    def _open_comment(self, pair: str) -> None:
        self.line_comment = pair == "--"
        self.block_depth = int(pair == "/-")
        self.pending_space = True
        self.index += 2

    def _append_visible(self, char: str) -> None:
        if (
            self.pending_space
            and self.output
            and _normalization_separator_required(self.output[-1], char)
        ):
            self.output.append(" ")
        self.pending_space = False
        self.output.append(char)
        if char == '"':
            self.in_string = True
            self.escaped = False
        self.index += 1

    def _append_escaped_identifier(self, text: str) -> None:
        """Preserve escaped spelling as one atom, including comment markers."""

        closing = text.find("»", self.index + 1)
        end = len(text) if closing < 0 else closing + 1
        atom = text[self.index : end]
        if (
            self.pending_space
            and self.output
            and _normalization_separator_required(self.output[-1], atom[0])
        ):
            self.output.append(" ")
        self.pending_space = False
        self.output.extend(atom)
        self.index = end


def scan_text_declarations(
    text: str,
    masked: str,
    *,
    module: str | None,
    source_path: str | None,
) -> tuple[LeanTextDeclaration, ...]:
    """Return bounded scope-aware candidates over an existing source mask."""

    declarations = tuple(DECL_RE.finditer(masked))
    scopes = tuple(_SCOPE_COMMAND_RE.finditer(masked))
    boundaries = sorted(
        {match.start() for match in declarations} | {match.start() for match in scopes}
    )
    command_boundaries = _non_declaration_command_boundaries(masked)
    state = _LexicalScopeState(frames=[])
    rows = _scan_events(
        declarations,
        scopes,
        text,
        masked,
        state,
        boundaries,
        command_boundaries,
        module,
        source_path,
    )
    return _invalidate_unbalanced_scope_rows(rows, state)


def _non_declaration_command_boundaries(
    masked: str,
) -> tuple[_IndentedBoundary, ...]:
    """Scan only nonblank line heads for supported command boundaries."""

    rows: list[_IndentedBoundary] = []
    offset = 0
    for line in masked.splitlines(keepends=True):
        body = line.lstrip(" \t")
        indentation = len(line) - len(body)
        if body and _NON_DECLARATION_COMMAND_HEAD_RE.match(
            body.rstrip("\r\n")
        ):
            rows.append(_IndentedBoundary(offset, indentation))
        offset += len(line)
    return tuple(rows)


def _scan_events(
    declarations: Sequence[re.Match[str]],
    scopes: Sequence[re.Match[str]],
    text: str,
    masked: str,
    state: _LexicalScopeState,
    boundaries: Sequence[int],
    command_boundaries: Sequence[_IndentedBoundary],
    module: str | None,
    source_path: str | None,
) -> list[LeanTextDeclaration]:
    """Merge declaration and scope events in source order."""

    rows: list[LeanTextDeclaration] = []
    declaration_index = 0
    scope_index = 0
    while declaration_index < len(declarations):
        declaration = declarations[declaration_index]
        while (
            scope_index < len(scopes)
            and scopes[scope_index].start() < declaration.start()
        ):
            _apply_scope_command(state, scopes[scope_index], text)
            scope_index += 1
        rows.append(
            _text_declaration(
                declaration,
                text,
                masked,
                state,
                boundaries,
                command_boundaries,
                module=module,
                source_path=source_path,
            )
        )
        declaration_index += 1
    while scope_index < len(scopes):
        _apply_scope_command(state, scopes[scope_index], text)
        scope_index += 1
    return rows


def _text_declaration(
    match: re.Match[str],
    text: str,
    masked: str,
    scope: _LexicalScopeState,
    boundaries: Sequence[int],
    command_boundaries: Sequence[_IndentedBoundary],
    *,
    module: str | None,
    source_path: str | None,
) -> LeanTextDeclaration:
    """Build one source-located lexical declaration candidate."""

    start = match.start("name")
    end = match.end("name")
    line = masked.count("\n", 0, start) + 1
    line_start = masked.rfind("\n", 0, start) + 1
    block_start = match.start()
    block_end = _next_boundary(
        boundaries,
        command_boundaries,
        block_start,
        len(text),
        declaration_indentation=_leading_indentation(masked, block_start),
    )
    modifiers = tuple(match.group("modifiers").split())
    written_name = text[start:end]
    candidate_name = _available_candidate_name(scope, written_name)
    block_text = text[block_start:block_end]
    normalized_block = normalize_declaration_block(block_text)
    block_hash = _normalized_text_hash(normalized_block)
    source_shape_hash = _normalized_text_hash(
        _source_shape_from_normalized(normalized_block)
    )
    return LeanTextDeclaration(
        name=written_name,
        kind=match.group("kind"),
        line=line,
        column=start - line_start + 1,
        start_offset=start,
        end_offset=end,
        identifier=_stable_lexical_declaration_id(
            module,
            source_path,
            match.group("kind"),
            written_name,
            start,
        ),
        namespace_stack=scope.namespace_stack,
        section_stack=scope.section_stack,
        modifiers=modifiers,
        privacy="private" if "private" in modifiers else "public",
        locality="local" if "local" in modifiers else "global",
        candidate_name=candidate_name,
        candidate_status=("lexical_candidate" if candidate_name else "unresolved"),
        block_start_offset=block_start,
        block_end_offset=block_end,
        normalized_block_sha256=block_hash,
        block_normalization_version=DECLARATION_BLOCK_NORMALIZATION_VERSION,
        normalized_source_shape_sha256=source_shape_hash,
        source_shape_normalization_version=(
            DECLARATION_SOURCE_SHAPE_NORMALIZATION_VERSION
        ),
    )


def _apply_scope_command(
    state: _LexicalScopeState,
    match: re.Match[str],
    text: str,
) -> None:
    """Apply one supported scope transition or fail closed."""

    kind = match.group("kind")
    body = _visible_source_group(text, match, "body")
    if kind == "end":
        _close_scope_frame(state, body)
    elif kind == "mutual":
        _open_mutual_frame(state, body, match.start())
    elif kind == "section":
        _open_section_frame(state, body, match.start())
    else:
        _open_namespace_frame(state, body, match.start())


def _open_namespace_frame(
    state: _LexicalScopeState,
    body: str,
    start_offset: int,
) -> None:
    """Open one safely recognized namespace command."""

    if not _SCOPE_NAME_RE.fullmatch(body):
        state.permanently_unresolved = True
        return
    state.frames.append(
        _LexicalScopeFrame(
            kind="namespace",
            name=body,
            namespace_segments=tuple(body.split(".")),
            start_offset=start_offset,
        )
    )


def _open_section_frame(
    state: _LexicalScopeState,
    body: str,
    start_offset: int,
) -> None:
    """Open one named or anonymous section command."""

    if body and not _SCOPE_NAME_RE.fullmatch(body):
        state.permanently_unresolved = True
        return
    state.frames.append(
        _LexicalScopeFrame(
            kind="section",
            name=body or None,
            namespace_segments=(),
            start_offset=start_offset,
        )
    )


def _open_mutual_frame(
    state: _LexicalScopeState,
    body: str,
    start_offset: int,
) -> None:
    """Retain an unsupported mutual block until its unambiguous ``end``."""

    if body:
        state.permanently_unresolved = True
        return
    state.frames.append(
        _LexicalScopeFrame(
            kind="mutual",
            name=None,
            namespace_segments=(),
            start_offset=start_offset,
            safe=False,
        )
    )


def _close_scope_frame(
    state: _LexicalScopeState,
    body: str,
) -> None:
    """Close only an unambiguous top lexical frame."""

    if not state.frames:
        state.permanently_unresolved = True
        return
    frame = state.frames[-1]
    if body and body != frame.name:
        state.permanently_unresolved = True
        return
    state.frames.pop()


def _invalidate_unbalanced_scope_rows(
    rows: list[LeanTextDeclaration],
    state: _LexicalScopeState,
) -> tuple[LeanTextDeclaration, ...]:
    """Fail closed for declarations inside frames left open at EOF."""

    if not state.frames:
        return tuple(rows)
    first = min(frame.start_offset for frame in state.frames)
    return tuple(
        replace(row, candidate_name=None, candidate_status="unresolved")
        if row.start_offset >= first
        else row
        for row in rows
    )


def _available_candidate_name(
    scope: _LexicalScopeState,
    written_name: str,
) -> str | None:
    """Return a lexical FQN only while scope state is unambiguous."""

    if not scope.candidate_available:
        return None
    if written_name.startswith("_root_."):
        return written_name.removeprefix("_root_.")
    return ".".join((*scope.namespace_stack, written_name))


def _next_boundary(
    boundaries: Sequence[int],
    command_boundaries: Sequence[_IndentedBoundary],
    start: int,
    fallback: int,
    *,
    declaration_indentation: int,
) -> int:
    """Return the next supported command start after one declaration."""

    structural = next((offset for offset in boundaries if offset > start), fallback)
    command = next(
        (
            boundary.offset
            for boundary in command_boundaries
            if boundary.offset > start
            and boundary.indentation <= declaration_indentation
        ),
        fallback,
    )
    return min(structural, command)


def _leading_indentation(text: str, line_start: int) -> int:
    """Count source whitespace before the first command token on one line."""

    cursor = line_start
    while cursor < len(text) and text[cursor] in {" ", "\t"}:
        cursor += 1
    return cursor - line_start


def _visible_source_group(
    text: str,
    match: re.Match[str],
    group: str,
) -> str:
    """Recover visible source spelling while excluding masked trailing trivia."""

    masked_value = match.group(group)
    leading = len(masked_value) - len(masked_value.lstrip())
    trailing = len(masked_value.rstrip())
    start = match.start(group) + leading
    end = match.start(group) + trailing
    return text[start:end]


def _stable_lexical_declaration_id(
    module: str | None,
    source_path: str | None,
    kind: str,
    name: str,
    start: int,
) -> str:
    """Return a deterministic identity for one source-anchored lexical row."""

    payload: dict[str, Any] = {
        "version": DECLARATION_ID_VERSION,
        "module": module,
        "path": source_path,
        "kind": kind,
        "name": name,
        "startOffset": start,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:20]
    return f"ladon.lexical_declaration.{digest}"


def _normalized_text_hash(normalized: str) -> str:
    """Hash one already-normalized lexical value."""

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize_declaration_block(text: str) -> str:
    """Remove comment/whitespace trivia while preserving literal contents."""

    if all(marker not in text for marker in ("--", "/-", '"', "«")):
        return _PLAIN_WHITESPACE_RE.sub(
            _plain_whitespace_replacement,
            text,
        )
    normalizer = _BlockNormalizer(output=[])
    while normalizer.index < len(text):
        normalizer.step(text)
    return "".join(normalizer.output).strip()


def _plain_whitespace_replacement(match: re.Match[str]) -> str:
    """Normalize trivia for a block with no comments or quoted atoms."""

    text = match.string
    start = match.start()
    end = match.end()
    return (
        " "
        if start > 0
        and end < len(text)
        and _normalization_separator_required(text[start - 1], text[end])
        else ""
    )


def normalize_declaration_source_shape(text: str) -> str:
    """Return a bounded lexical token-category shape for one source block.

    The transformation first removes only comment and whitespace trivia using
    the exact-block normalizer. It then preserves structural Lean keywords and
    delimiters while replacing other identifiers, numeric literals, and string
    literals with category markers. This is deliberately not a Lean parse or
    an elaborated proof-shape representation.
    """

    return _source_shape_from_normalized(normalize_declaration_block(text))


def _source_shape_from_normalized(normalized: str) -> str:
    """Categorize one exact-block normalization without rescanning trivia."""

    return _SOURCE_SHAPE_TOKEN_RE.sub(_source_shape_token, normalized)


def _source_shape_token(match: re.Match[str]) -> str:
    """Map one lexical token to a stable structural category."""

    token = match.group(0)
    if token.startswith("«"):
        return "<identifier>"
    if token.startswith('"'):
        return "<string>"
    if token[0].isdigit():
        return "<number>"
    if token in _SOURCE_SHAPE_KEYWORDS:
        return token
    return "<identifier>"


def _normalization_separator_required(previous: str, current: str) -> bool:
    """Keep only whitespace needed to avoid merging lexical word tokens."""

    return _word_token_character(previous) and _word_token_character(current)


def _word_token_character(character: str) -> bool:
    return character.isalnum() or character in {"_", "'", '"'}


__all__ = [
    "DECLARATION_BLOCK_NORMALIZATION_VERSION",
    "DECLARATION_KINDS",
    "DECLARATION_MODIFIERS",
    "DECLARATION_SOURCE_SHAPE_NORMALIZATION_VERSION",
    "DECL_RE",
    "normalize_declaration_block",
    "normalize_declaration_source_shape",
    "scan_text_declarations",
]
