"""Offset-preserving Lean masks from one conservative lexical scan.

The ordinary mask blanks comments and literal payloads for regex-based source
navigation.  The command-shape mask additionally retains literal delimiters,
raw-string modifiers, and escaped identifier spelling without exposing string
or character contents.  Neither view is a Lean parser.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LeanSourceMasks:
    """Lexical and command-shape views with source offsets preserved."""

    lexical: str
    command_shape: str


@dataclass(frozen=True)
class _RawStringBounds:
    opening_end: int
    closing_start: int
    end: int


def mask_lean_source(text: str) -> LeanSourceMasks:
    """Build comment-safe lexical and literal-shape masks in one pass."""

    lexical: list[str] = []
    command_shape: list[str] = []
    index = 0
    block_depth = 0
    line_comment = False
    while index < len(text):
        char = text[index]
        pair = text[index : index + 2]
        if char == "\n":
            _append_both(lexical, command_shape, char)
            line_comment = False
            index += 1
            continue
        if line_comment:
            index = _mask_line_comment(
                text,
                index,
                lexical,
                command_shape,
            )
            continue
        if block_depth:
            block_depth, index = _mask_block_position(
                pair,
                block_depth,
                index,
                lexical,
                command_shape,
            )
            continue
        atom_end = _mask_code_atom(
            text,
            index,
            lexical,
            command_shape,
        )
        if atom_end is not None:
            index = atom_end
            continue
        if pair == "--":
            line_comment = True
            _extend_both(lexical, command_shape, "  ")
            index += 2
            continue
        if pair == "/-":
            block_depth = 1
            _extend_both(lexical, command_shape, "  ")
            index += 2
            continue
        _append_both(lexical, command_shape, char)
        index += 1
    return LeanSourceMasks(
        lexical="".join(lexical),
        command_shape="".join(command_shape),
    )


def _mask_line_comment(
    text: str,
    start: int,
    lexical: list[str],
    command_shape: list[str],
) -> int:
    """Mask one line-comment body in a single chunk, preserving its newline."""

    newline = text.find("\n", start)
    end = len(text) if newline < 0 else newline
    _append_both(lexical, command_shape, " " * (end - start))
    return end


def _mask_code_atom(
    text: str,
    start: int,
    lexical: list[str],
    command_shape: list[str],
) -> int | None:
    raw = _raw_string_bounds(text, start)
    if raw is not None:
        _append_raw_string(text, start, raw, lexical, command_shape)
        return raw.end
    char = text[start]
    if char == '"':
        end = _ordinary_string_end(text, start)
        _append_quoted_literal(
            text,
            start,
            end,
            '"',
            lexical,
            command_shape,
        )
        return end
    if char == "'" and _at_token_boundary(text, start):
        end = _char_literal_end(text, start)
        if end is not None:
            _append_quoted_literal(
                text,
                start,
                end,
                "'",
                lexical,
                command_shape,
            )
            return end
    if char == "«":
        end = _escaped_identifier_end(text, start)
        _append_escaped_identifier(
            text,
            start,
            end,
            lexical,
            command_shape,
        )
        return end
    return None


def _raw_string_bounds(
    text: str,
    start: int,
) -> _RawStringBounds | None:
    if text[start] != "r" or not _at_token_boundary(text, start):
        return None
    cursor = start + 1
    while cursor < len(text) and text[cursor] == "#":
        cursor += 1
    if cursor >= len(text) or text[cursor] != '"':
        return None
    opening_end = cursor + 1
    delimiter = '"' + "#" * (cursor - start - 1)
    closing_start = text.find(delimiter, opening_end)
    if closing_start < 0:
        return _RawStringBounds(opening_end, len(text), len(text))
    end = closing_start + len(delimiter)
    return _RawStringBounds(opening_end, closing_start, end)


def _ordinary_string_end(text: str, start: int) -> int:
    cursor = start + 1
    escaped = False
    while cursor < len(text):
        char = text[cursor]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            return cursor + 1
        cursor += 1
    return len(text)


def _char_literal_end(text: str, start: int) -> int | None:
    cursor = start + 1
    if cursor >= len(text) or text[cursor] in {"'", "\n"}:
        return None
    if text[cursor] == "\\":
        cursor = _quoted_char_escape_end(text, cursor + 1)
        if cursor is None:
            return None
    else:
        cursor += 1
    if cursor < len(text) and text[cursor] == "'":
        return cursor + 1
    return None


def _quoted_char_escape_end(text: str, cursor: int) -> int | None:
    if cursor >= len(text):
        return None
    escape = text[cursor]
    if escape in {"\\", '"', "'", "r", "n", "t"}:
        return cursor + 1
    if escape == "x" and _all_hex(text[cursor + 1 : cursor + 3], 2):
        return cursor + 3
    if escape == "u" and _all_hex(text[cursor + 1 : cursor + 5], 4):
        return cursor + 5
    return None


def _all_hex(value: str, expected: int) -> bool:
    return len(value) == expected and all(
        char in "0123456789abcdefABCDEF" for char in value
    )


def _escaped_identifier_end(text: str, start: int) -> int:
    closing = text.find("»", start + 1)
    return len(text) if closing < 0 else closing + 1


def _at_token_boundary(text: str, start: int) -> bool:
    return start == 0 or not _identifier_rest(text[start - 1])


def _identifier_rest(char: str) -> bool:
    return char.isalnum() or char in {"_", "'", "!", "?"}


def _append_raw_string(
    text: str,
    start: int,
    bounds: _RawStringBounds,
    lexical: list[str],
    command_shape: list[str],
) -> None:
    for offset in range(start, bounds.end):
        char = text[offset]
        lexical.append(char if char == "\n" else " ")
        visible = (
            offset < bounds.opening_end
            or offset >= bounds.closing_start
        )
        command_shape.append(
            char if char == "\n" or visible else " "
        )


def _append_quoted_literal(
    text: str,
    start: int,
    end: int,
    delimiter: str,
    lexical: list[str],
    command_shape: list[str],
) -> None:
    closed = end > start + 1 and text[end - 1] == delimiter
    for offset in range(start, end):
        char = text[offset]
        lexical.append(char if char == "\n" else " ")
        visible = offset == start or (closed and offset == end - 1)
        command_shape.append(
            char if char == "\n" or visible else " "
        )


def _append_escaped_identifier(
    text: str,
    start: int,
    end: int,
    lexical: list[str],
    command_shape: list[str],
) -> None:
    closed = end > start and text[end - 1] == "»"
    for offset in range(start, end):
        char = text[offset]
        visible = offset == start or (closed and offset == end - 1)
        lexical.append(
            char if char == "\n" or visible else " "
        )
        command_shape.append(char)


def _mask_block_position(
    pair: str,
    depth: int,
    index: int,
    lexical: list[str],
    command_shape: list[str],
) -> tuple[int, int]:
    if pair == "/-":
        _extend_both(lexical, command_shape, "  ")
        return depth + 1, index + 2
    if pair == "-/":
        _extend_both(lexical, command_shape, "  ")
        return depth - 1, index + 2
    _append_both(lexical, command_shape, " ")
    return depth, index + 1


def _append_both(
    lexical: list[str],
    command_shape: list[str],
    value: str,
) -> None:
    lexical.append(value)
    command_shape.append(value)


def _extend_both(
    lexical: list[str],
    command_shape: list[str],
    value: str,
) -> None:
    lexical.extend(value)
    command_shape.extend(value)


__all__ = ["LeanSourceMasks", "mask_lean_source"]
