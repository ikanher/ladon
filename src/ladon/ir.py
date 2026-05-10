from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LeanModule:
    """Stable module-level IR shared by Ladon analysis passes."""

    name: str
    path: str
    imports: tuple[str, ...] = ()
    declarations: tuple[str, ...] = ()
