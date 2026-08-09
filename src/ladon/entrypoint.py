"""Lightweight installed entrypoint with lazy command-family imports."""

from __future__ import annotations

import sys
from typing import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch proof-search without importing the general analyzer first."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "proof-search":
        from ladon.proof_search_cli import proof_search_main

        return proof_search_main(arguments[1:])
    if arguments and arguments[0] == "proofir":
        from ladon.proofir_v3_cli import proofir_v3_main

        return proofir_v3_main(arguments[1:])
    from ladon.cli import main as analyzer_main

    return analyzer_main(arguments)


__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
