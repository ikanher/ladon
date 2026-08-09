#!/usr/bin/env python3
"""Render or run the maintained local Ladon root matrix."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from ladon.root_matrix import default_root_matrix, matrix_command, select_matrix_entries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", action="append", help="Run only a named matrix entry.")
    parser.add_argument(
        "--repository-root",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help=(
            "Explicit optional repository root; NAME is matrix-factorization. "
            "The environment alternative is LADON_MATRIX_FACTORIZATION_ROOT."
        ),
    )
    parser.add_argument(
        "--output-root",
        default="temp/ladon-root-matrix",
        help="Directory for generated report files.",
    )
    parser.add_argument("--ladon-bin", default="bin/ladon", help="Path to the Ladon CLI.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--run", action="store_true", help="Execute selected commands.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    commands = selected_commands(args)
    if args.run:
        return run_commands(commands)
    print_commands(commands)
    return 0


def selected_commands(args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    entries = select_matrix_entries(
        default_root_matrix(parse_repository_roots(args.repository_root)),
        args.only,
    )
    output_root = Path(args.output_root)
    ladon_bin = Path(args.ladon_bin)
    return [
        (entry["name"], matrix_command(entry, output_root=output_root, ladon_bin=ladon_bin))
        for entry in entries
    ]


def parse_repository_roots(values: list[str]) -> dict[str, str]:
    """Parse repeatable explicit ``NAME=PATH`` repository roots."""

    roots: dict[str, str] = {}
    for value in values:
        name, separator, path = value.partition("=")
        if not separator or not name or not path:
            raise ValueError(
                f"invalid --repository-root {value!r}; expected NAME=PATH"
            )
        roots[name] = path
    return roots


def print_commands(commands: list[tuple[str, list[str]]]) -> None:
    for name, command in commands:
        print(f"# {name}")
        print(" ".join(command))


def run_commands(commands: list[tuple[str, list[str]]]) -> int:
    status = 0
    for name, command in commands:
        print(f"== {name} ==")
        status = subprocess.run(command, check=False).returncode or status
    return status


if __name__ == "__main__":
    raise SystemExit(main())
