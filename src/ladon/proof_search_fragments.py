"""Small case-sensitive tokenizer for normalized Lean type fragments."""

from __future__ import annotations

import unicodedata

_SYMBOL_BOUNDARIES = "‖()[]{}⟨⟩⦃⦄,;«»\"'_∀∃→←↔¬"


def tokenize_lean_text(text: str) -> tuple[str, ...]:
    """Tokenize identifiers, quoted strings, and operators.

    Whitespace is insignificant between tokens. Identifier spelling and quoted
    contents remain exact. Common binder and arrow symbols delimit operator
    runs, and other adjacent operator characters can form a compound token.
    """
    tokens: list[str] = []
    i = 0
    while i < len(text):
        char = text[i]
        if char.isspace():
            i += 1
            continue
        token, i = _token_at(text, i)
        tokens.append(token)
    return tuple(tokens)


def _token_at(text: str, i: int) -> tuple[str, int]:
    char = text[i]
    if char == '"':
        return _quoted_token(text, i)
    if char == "«":
        end = text.find("»", i + 1)
        return (text[i:end + 1], end + 1) if end >= 0 else (char, i + 1)
    if char == "'":
        end = _character_literal_end(text, i)
        if end is not None:
            return text[i:end], end
    word = _word_token(text, i)
    if word is not None:
        return word
    return _symbol_token(text, i)


def _word_token(text: str, i: int) -> tuple[str, int] | None:
    char = text[i]
    if _identifier_start(char):
        end = i + 1
        while end < len(text) and _identifier_continue(text[end]):
            end += 1
        return text[i:end], end
    if char.isdigit():
        end = i + 1
        while end < len(text) and (text[end].isdigit() or text[end] == "_"):
            end += 1
        return text[i:end], end
    return None


def _symbol_token(text: str, i: int) -> tuple[str, int]:
    char = text[i]
    if text.startswith("∃!", i):
        return "∃!", i + 2
    if char in _SYMBOL_BOUNDARIES:
        return char, i + 1
    if _operator(char):
        end = i + 1
        while end < len(text) and text[end] not in _SYMBOL_BOUNDARIES and _operator(text[end]):
            end += 1
        return text[i:end], end
    return char, i + 1


def _character_literal_end(text: str, start: int) -> int | None:
    i = start + 1
    if i >= len(text):
        return None
    if text[i] == "\\":
        i += 2
    else:
        i += 1
    return i + 1 if i < len(text) and text[i] == "'" else None


def _quoted_token(text: str, start: int) -> tuple[str, int]:
    i = start + 1
    escaped = False
    while i < len(text):
        current = text[i]
        i += 1
        if current == '"' and not escaped:
            break
        escaped = current == "\\" and not escaped
    return text[start:i], i


def _identifier_start(char: str) -> bool:
    return char == "_" or char.isalpha() or unicodedata.category(char).startswith("L")


def _identifier_continue(char: str) -> bool:
    category = unicodedata.category(char)
    return _identifier_start(char) or char.isdigit() or category.startswith("M") or char in "'!?"


def _operator(char: str) -> bool:
    category = unicodedata.category(char)
    return category.startswith(("S", "P"))


def contains_fragment(text: str, fragment: str) -> bool:
    """Return whether fragment tokens occur contiguously in text tokens."""
    haystack = tokenize_lean_text(text)
    needle = tokenize_lean_text(fragment)
    return contains_tokens(haystack, needle)


def contains_tokens(haystack: tuple[str, ...], needle: tuple[str, ...]) -> bool:
    width = len(needle)
    return bool(width) and any(haystack[i:i + width] == needle for i in range(len(haystack) - width + 1))


def normalized_fragments(fragments: tuple[str, ...]) -> tuple[str, ...]:
    """Reject whitespace-only requests and collapse token-equivalent duplicates."""
    result: list[str] = []
    seen: set[tuple[str, ...]] = set()
    for fragment in fragments:
        tokens = tokenize_lean_text(fragment)
        if not tokens:
            raise ValueError("type-text fragments must contain non-whitespace text")
        if tokens not in seen:
            result.append(fragment)
            seen.add(tokens)
    return tuple(result)


__all__ = ["contains_fragment", "normalized_fragments", "tokenize_lean_text"]
