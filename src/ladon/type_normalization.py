"""Conservative lexical normalization shared by type-oriented surfaces."""

from __future__ import annotations


def peel_binder_signature(candidate: str) -> tuple[str, list[str], str | None]:
    """Peel leading binder groups, returning conclusion and residual binders."""
    text = candidate.strip()
    binders: list[str] = []
    while text.startswith("("):
        end = _balanced_group_end(text)
        if end is None:
            return text, binders, "unsupported-binder-syntax"
        binders.append(text[1:end])
        remainder = text[end + 1 :].lstrip()
        if remainder.startswith(":"):
            return remainder[1:].strip(), binders, None
        if not remainder.startswith("("):
            return text, binders, "unsupported-binder-syntax"
        text = remainder
    return text, binders, None


def _balanced_group_end(text: str) -> int | None:
    depth = 0
    for index, char in enumerate(text):
        depth += char == "("
        depth -= char == ")"
        if depth == 0:
            return index
    return None


__all__ = ["peel_binder_signature"]
