"""Build-mode policy and conservative module cache identities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class SemanticBuildRequest:
    mode: str = "lexical"
    lean_timeout: float = 120.0
    completeness: str = "allow-partial"

    def __post_init__(self) -> None:
        if self.mode not in {"lexical", "semantic", "hybrid"}:
            raise ValueError("mode must be lexical, semantic, or hybrid")
        if self.completeness not in {"allow-partial", "require-complete"}:
            raise ValueError("completeness must be allow-partial or require-complete")
        if self.lean_timeout <= 0:
            raise ValueError("lean_timeout must be positive")


def module_cache_key(identity: Mapping[str, object]) -> str:
    """Hash every supplied source/build/helper identity conservatively."""

    return "sha256:" + hashlib.sha256(json.dumps(dict(identity), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def cache_reusable(record: Mapping[str, object], identity: Mapping[str, object]) -> bool:
    return str(record.get("cacheKey", "")) == module_cache_key(identity) and str(record.get("status", "")) in {"complete", "partial"}


__all__ = ["SemanticBuildRequest", "module_cache_key", "cache_reusable"]
