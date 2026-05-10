#!/usr/bin/env python3
"""Run Ladon's Python code-quality audits.

Default mode prints radon and vulture reports. Strict mode is the project gate:
it fails on C-or-worse active complexity, C-grade maintainability,
high-confidence dead code, compile failures, or tests.
"""

from __future__ import annotations

import argparse
import compileall
import subprocess
import sys
from pathlib import Path

from ladon.quality import format_issue, strict_quality_issues


DEFAULT_TARGETS = ("src", "tests", "scripts")


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def existing_targets(root: Path, targets: list[str]) -> list[str]:
    found = [target for target in targets if (root / target).exists()]
    if not found:
        raise SystemExit(f"no quality targets exist under {root}: {targets}")
    return found


def run_command(label: str, command: list[str], cwd: Path) -> int:
    print(f"\n== {label} ==", flush=True)
    print("+ " + " ".join(command), flush=True)
    return subprocess.run(command, cwd=cwd).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run radon and vulture over Ladon's Python sources."
    )
    parser.add_argument(
        "--target",
        action="append",
        dest="targets",
        help=(
            "Path to audit, relative to the project root. Can be passed more "
            "than once. Defaults to src, tests, and scripts."
        ),
    )
    parser.add_argument(
        "--skip-radon",
        action="store_true",
        help="Skip radon complexity and maintainability reports.",
    )
    parser.add_argument(
        "--skip-vulture",
        action="store_true",
        help="Skip vulture dead-code detection.",
    )
    parser.add_argument(
        "--include-raw",
        action="store_true",
        help="Also print radon raw metrics.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on radon C-or-worse blocks, C-grade MI, vulture findings, compile failures, or tests.",
    )
    parser.add_argument(
        "--vulture-min-confidence",
        type=int,
        default=80,
        help="Minimum vulture confidence to report. Defaults to 80.",
    )
    return parser


def run_strict(root: Path, targets: list[str]) -> int:
    """Run the full quality gate used before applying Ladon changes."""

    print("\n== strict radon/vulture checks ==", flush=True)
    target_paths = [root / target for target in targets]
    issues = strict_quality_issues(target_paths)
    if issues:
        print("\n== strict quality failures ==", flush=True)
        for issue in issues:
            print(format_issue(issue))
        return 1
    print("radon/vulture: clean", flush=True)
    print("\n== compileall ==", flush=True)
    if not compileall.compile_dir(root / "src", quiet=1):
        return 1
    if (root / "tests").exists() and not compileall.compile_dir(root / "tests", quiet=1):
        return 1
    if (root / "scripts").exists() and not compileall.compile_dir(root / "scripts", quiet=1):
        return 1
    return run_command("pytest", [sys.executable, "-m", "pytest", "-q"], root)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = project_root()
    targets = existing_targets(root, args.targets or list(DEFAULT_TARGETS))
    if args.strict:
        return run_strict(root, targets)

    commands: list[tuple[str, list[str]]] = []
    if not args.skip_radon:
        commands.append(
            (
                "radon cyclomatic complexity",
                [sys.executable, "-m", "radon", "cc", *targets, "-s", "-a"],
            )
        )
        commands.append(
            (
                "radon maintainability index",
                [sys.executable, "-m", "radon", "mi", *targets, "-s"],
            )
        )
        if args.include_raw:
            commands.append(
                (
                    "radon raw metrics",
                    [sys.executable, "-m", "radon", "raw", *targets],
                )
            )

    if not args.skip_vulture:
        commands.append(
            (
                "vulture dead-code scan",
                [
                    sys.executable,
                    "-m",
                    "vulture",
                    *targets,
                    "--min-confidence",
                    str(args.vulture_min_confidence),
                ],
            )
        )

    if not commands:
        print("No quality tools selected.")
        return 0

    status = 0
    for label, command in commands:
        status = run_command(label, command, root) or status
    return status


if __name__ == "__main__":
    raise SystemExit(main())
