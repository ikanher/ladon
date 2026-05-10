"""Strict Python quality checks used by Ladon's clean-core gate.

The gate treats radon C-or-worse active blocks and high-confidence vulture
findings as implementation failures. This keeps the standalone project from
accumulating another analyzer monolith.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from radon.complexity import cc_rank, cc_visit
from radon.metrics import mi_rank, mi_visit


RANK_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5}


@dataclass(frozen=True)
class QualityIssue:
    """One actionable Python quality finding."""

    tool: str
    path: str
    line: int
    name: str
    rank: str
    value: str
    message: str


def python_files(targets: Sequence[Path]) -> list[Path]:
    """Expand files/directories into active Python files for quality checks."""

    files: list[Path] = []
    for target in targets:
        files.extend(files_for_target(target))
    return sorted(set(files))


def files_for_target(target: Path) -> list[Path]:
    """Return active Python files under one checked target."""

    if target.is_file() and target.suffix == ".py":
        return [target]
    if target.is_dir():
        return [
            path
            for path in target.rglob("*.py")
            if "__pycache__" not in path.parts and ".venv" not in path.parts
        ]
    return []


def rank_exceeds(rank: str, maximum: str) -> bool:
    """Return whether a radon rank is worse than the allowed maximum."""

    return RANK_ORDER[rank] > RANK_ORDER[maximum]


def collect_radon_complexity_issues(
    targets: Sequence[Path],
    *,
    max_rank: str = "B",
) -> list[QualityIssue]:
    """Collect C-or-worse cyclomatic-complexity issues by default."""

    issues: list[QualityIssue] = []
    for path in python_files(targets):
        source = path.read_text(encoding="utf-8")
        issues.extend(complexity_issues_for_file(path, source, max_rank=max_rank))
    return issues


def complexity_issues_for_file(path: Path, source: str, *, max_rank: str) -> list[QualityIssue]:
    """Convert radon complexity blocks worse than `max_rank` into issues."""

    issues: list[QualityIssue] = []
    for block in cc_visit(source):
        rank = cc_rank(block.complexity)
        if rank_exceeds(rank, max_rank):
            issues.append(
                QualityIssue(
                    tool="radon-cc",
                    path=str(path),
                    line=block.lineno,
                    name=block.name,
                    rank=rank,
                    value=str(block.complexity),
                    message=f"{block.name} has radon rank {rank} ({block.complexity})",
                )
            )
    return issues


def collect_radon_mi_issues(
    targets: Sequence[Path],
    *,
    max_rank: str = "B",
) -> list[QualityIssue]:
    """Collect maintainability-index issues by file."""

    return [
        issue
        for path in python_files(targets)
        for issue in maintainability_issues_for_file(path, max_rank=max_rank)
    ]


def maintainability_issues_for_file(path: Path, *, max_rank: str) -> list[QualityIssue]:
    """Return one maintainability issue when a file exceeds the MI policy."""

    source = path.read_text(encoding="utf-8")
    score = mi_visit(source, multi=True)
    rank = mi_rank(score)
    if not rank_exceeds(rank, max_rank):
        return []
    return [
        QualityIssue(
            tool="radon-mi",
            path=str(path),
            line=1,
            name=path.name,
            rank=rank,
            value=f"{score:.2f}",
            message=f"{path} has maintainability rank {rank} ({score:.2f})",
        )
    ]


def collect_vulture_issues(
    targets: Sequence[Path],
    *,
    min_confidence: int = 80,
) -> list[QualityIssue]:
    """Run vulture and convert high-confidence output into gate issues."""

    command = [
        sys.executable,
        "-m",
        "vulture",
        *[str(target) for target in targets],
        "--min-confidence",
        str(min_confidence),
    ]
    proc = subprocess.run(command, text=True, capture_output=True, check=False)
    return vulture_issues_from_output(proc.stdout + proc.stderr)


def vulture_issues_from_output(output: str) -> list[QualityIssue]:
    """Parse vulture's line-oriented output into strict-gate issues."""

    return [
        QualityIssue(
            tool="vulture",
            path=line.split(":", 1)[0],
            line=vulture_line_number(line),
            name="dead-code",
            rank="C",
            value="",
            message=line,
        )
        for line in output.splitlines()
        if line.strip()
    ]


def vulture_line_number(line: str) -> int:
    """Extract a vulture line number, falling back to line 1."""

    parts = line.split(":", 2)
    if len(parts) < 2:
        return 1
    return int(parts[1]) if parts[1].isdigit() else 1


def strict_quality_issues(targets: Sequence[Path]) -> list[QualityIssue]:
    """Collect all issues that fail Ladon's strict quality gate."""

    return [
        *collect_radon_complexity_issues(targets),
        *collect_radon_mi_issues(targets),
        *collect_vulture_issues(targets),
    ]


def format_issue(issue: QualityIssue) -> str:
    """Render one quality issue for human CLI output."""

    location = f"{issue.path}:{issue.line}"
    return f"{issue.tool}: {location}: {issue.message}"
