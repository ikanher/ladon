"""Maintained local root matrix for manual Ladon calibration runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


MatrixEntry = dict[str, Any]


def default_root_matrix() -> list[MatrixEntry]:
    """Return explicit Quux and matrix-factorization calibration roots."""

    return [
        text_entry("quux-project", "quux", "/home/codex/projects/quux", "Quux"),
        text_entry(
            "quux-proof-ir",
            "quux",
            "/home/codex/projects/quux",
            "Quux/ProofIR.lean",
        ),
        text_entry(
            "quux-bridge-example-core",
            "quux",
            "/home/codex/projects/quux",
            "Quux/Bridge/Example/Core.lean",
        ),
        lean_entry(
            "quux-propagation",
            "quux",
            "/home/codex/projects/quux",
            "Quux/Semantics/Propagation.lean",
        ),
        lean_entry(
            "quux-bifr-rmse-problem",
            "quux",
            "/home/codex/projects/quux",
            "Quux/Problems/BIFRRMSESaturationMini.lean",
        ),
        text_entry("mf-project", "matrix-factorization", "/home/codex/projects/lean/matrix-factorization", "Mf"),
        lean_entry(
            "mf-gaussian-core",
            "matrix-factorization",
            "/home/codex/projects/lean/matrix-factorization",
            "Mf/DP/GaussianCore.lean",
        ),
        lean_entry(
            "mf-bsr-factor-core",
            "matrix-factorization",
            "/home/codex/projects/lean/matrix-factorization",
            "Mf/DP/BSRFactorCore.lean",
        ),
        lean_entry(
            "mf-optimization-ftrl",
            "matrix-factorization",
            "/home/codex/projects/lean/matrix-factorization",
            "Mf/Optimization/FTRLAnalysis.lean",
        ),
        lean_entry(
            "mf-bifr-packed-profile",
            "matrix-factorization",
            "/home/codex/projects/lean/matrix-factorization",
            "Mf/DP/BIFRPackedProfileFiniteSumBounds.lean",
        ),
    ]


def text_entry(name: str, repo_key: str, repo_root: str, root: str) -> MatrixEntry:
    """Build one text-backed matrix entry."""

    return {
        "name": name,
        "repo_key": repo_key,
        "repo_root": repo_root,
        "root": root,
        "backend": "text",
    }


def lean_entry(name: str, repo_key: str, repo_root: str, root: str) -> MatrixEntry:
    """Build one Lean-backed matrix entry."""

    return {
        **text_entry(name, repo_key, repo_root, root),
        "backend": "lean",
        "lean_extraction_scope": "root",
    }


def select_matrix_entries(entries: list[MatrixEntry], names: list[str] | None) -> list[MatrixEntry]:
    """Return selected entries or all entries when no names are given."""

    if not names:
        return entries
    by_name = {entry["name"]: entry for entry in entries}
    missing = [name for name in names if name not in by_name]
    if missing:
        raise ValueError(f"unknown root matrix entries: {', '.join(missing)}")
    return [by_name[name] for name in names]


def matrix_command(
    entry: MatrixEntry,
    *,
    output_root: Path,
    ladon_bin: Path,
) -> list[str]:
    """Return a Ladon command for one matrix entry."""

    output_base = output_root / entry["repo_key"] / entry["name"]
    command = [
        str(ladon_bin),
        "--repo-root",
        entry["repo_root"],
        "--root",
        entry["root"],
        "--output-json",
        str(output_base.with_suffix(".json")),
        "--output-text",
        str(output_base.with_suffix(".txt")),
    ]
    if entry["backend"] == "lean":
        command.extend(
            [
                "--extraction-backend",
                "lean",
                "--lean-extraction-scope",
                entry.get("lean_extraction_scope", "root"),
                "--lean-cache-dir",
                str(output_root / ".lean-cache" / entry["name"]),
            ]
        )
    else:
        command.append("--skip-build")
    return command
