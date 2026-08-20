"""Versioned ProofIR fingerprint schemes admitted to semantic search."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

SCHEMES = MappingProxyType(
    {
        ("lean-expr", "1"): MappingProxyType(
            {"owner": "lean", "semantics": "expression-structural", "exact": True}
        ),
        ("lean-expr-structural", "2"): MappingProxyType(
            {"owner": "ladon-lean-worker", "semantics": "expression-structural", "exact": True}
        ),
    }
)


def scheme_key(scheme: dict[str, Any]) -> tuple[str, str] | None:
    if not isinstance(scheme, dict):
        return None
    name, version = scheme.get("name"), scheme.get("version")
    if not isinstance(name, str) or not isinstance(version, str):
        return None
    return name, version


def is_exact_scheme(name: str, version: str) -> bool:
    profile = SCHEMES.get((name, version))
    return bool(profile and profile["exact"])


__all__ = ["SCHEMES", "is_exact_scheme", "scheme_key"]
