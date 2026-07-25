#!/usr/bin/env python3
"""Verify OpenSpec canonicalization profiles used by archive-aware readiness."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ladon.analysis.openspec_canonical import CanonicalGateError, check_legacy_cli_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("legacy-cli",), required=True)
    parser.add_argument("--openspec-root", default="openspec")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--allow-active-delta", action="store_true")
    modes.add_argument("--require-canonical", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        state = check_legacy_cli_profile(
            Path(args.openspec_root),
            allow_active_delta=args.allow_active_delta,
            require_canonical=args.require_canonical,
        )
    except CanonicalGateError as exc:
        sys.stderr.write(f"openspec-canonical-gate: {exc}\n")
        return 1
    sys.stdout.write(f"openspec-canonical-gate: profile={args.profile} state={state} PASS\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
