"""Stable dataclasses shared between Ladon extraction and analysis passes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LeanModule:
    """Stable module-level IR shared by pure Ladon analysis passes.

    `imports` stores module names as written in Lean import headers.
    `declarations` stores only names in the clean core; declaration-level proof
    facts are a future Lean-native extraction surface.
    """

    name: str
    path: str
    imports: tuple[str, ...] = ()
    declarations: tuple[str, ...] = ()


@dataclass(frozen=True)
class LeanDeclaration:
    """Stable declaration-level IR for exact-reference graph analysis.

    `references` stores raw candidate names supplied by extraction. Analysis
    only turns them into edges when a candidate exactly matches another known
    declaration name. Source evidence fields identify the file/range/hash used
    for attachment confidence; they are not Lean kernel dependency facts.
    """

    name: str
    module: str
    kind: str | None = None
    references: tuple[str, ...] = ()
    source_path: str | None = None
    source_range: dict[str, Any] | None = None
    selection_range: dict[str, Any] | None = None
    content_hash: str | None = None
    extraction_backend: str | None = None
    extractor_version: str | None = None
    name_resolution_method: str | None = None
    confidence: str | None = None


@dataclass(frozen=True)
class ExtractionBundle:
    """Backend-normalized extraction output for analysis phases."""

    modules: dict[str, LeanModule]
    declarations: dict[str, LeanDeclaration] | None = None
    counters: dict[str, int] = field(default_factory=dict)
