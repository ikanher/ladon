"""Shared v2 declaration-name normalization for indexing and querying."""

from __future__ import annotations

import re
from typing import Any


_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_TOKEN = re.compile(r"[A-Za-z0-9]+")


def name_casefold(name: str) -> str:
    """Return the exact folded lookup key."""

    return name.casefold()


def semantic_name_segments_v1(name: str) -> str:
    """Split namespaces, snake case, and camel case into FTS segments."""

    expanded = _CAMEL_BOUNDARY.sub(" ", name.replace("_", " ").replace(".", " "))
    return " ".join(token.casefold() for token in _TOKEN.findall(expanded))


def is_exact_name_query(text: str) -> bool:
    """Return whether text is suitable for monotone exact-name refinement."""

    return bool(text.strip()) and not any(char.isspace() for char in text)


def query_name_database(connection: Any, **kwargs: Any) -> Any:
    """Stable name-query entry point; legacy SQL planning remains behind it."""

    from ladon.proof_search_query import query_database

    return query_database(connection, **kwargs)


__all__ = ["is_exact_name_query", "name_casefold", "semantic_name_segments_v1"]
