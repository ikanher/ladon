"""Stable dataclasses shared between Ladon extraction and analysis passes."""

from __future__ import annotations

from dataclasses import dataclass, field


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
    declaration name.
    """

    name: str
    module: str
    kind: str | None = None
    references: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExtractionBundle:
    """Backend-normalized extraction output for analysis phases."""

    modules: dict[str, LeanModule]
    declarations: dict[str, LeanDeclaration] | None = None
    counters: dict[str, int] = field(default_factory=dict)
