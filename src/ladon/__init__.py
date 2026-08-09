"""Public package entrypoint for Ladon's clean-core CLI."""

from __future__ import annotations

from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Load the CLI lazily so ``python -m ladon.entrypoint`` stays warning-free."""

    from .entrypoint import main as run

    return run(argv)


__all__ = ["main"]
