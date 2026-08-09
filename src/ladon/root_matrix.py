"""Maintained local root matrix for manual Ladon calibration runs."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

MatrixEntry = dict[str, Any]
ROOT_ENVIRONMENT = {
    "matrix-factorization": "LADON_MATRIX_FACTORIZATION_ROOT",
}


def default_root_matrix(
    repo_roots: Mapping[str, str] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
) -> list[MatrixEntry]:
    """Return only explicitly configured optional live-repository roots."""

    roots = configured_repo_roots(repo_roots, environment=environment)
    entries: list[MatrixEntry] = []
    if "matrix-factorization" in roots:
        entries.extend(matrix_factorization_entries(roots["matrix-factorization"]))
    return entries


def configured_repo_roots(
    repo_roots: Mapping[str, str] | None,
    *,
    environment: Mapping[str, str] | None,
) -> dict[str, str]:
    """Resolve explicit arguments over opt-in environment variables."""

    source_environment = environment if environment is not None else os.environ
    configured = {
        name: value
        for name, variable in ROOT_ENVIRONMENT.items()
        if (value := source_environment.get(variable))
    }
    configured.update(repo_roots or {})
    unknown = sorted(set(configured) - set(ROOT_ENVIRONMENT))
    if unknown:
        raise ValueError(f"unknown optional repository roots: {', '.join(unknown)}")
    return configured


def matrix_factorization_entries(repo_root: str) -> list[MatrixEntry]:
    """Return explicitly rooted observational matrix-factorization entries."""

    return [
        text_entry(
            "mf-project",
            "matrix-factorization",
            repo_root,
            "Mf",
        ),
        lean_entry(
            "mf-gaussian-core",
            "matrix-factorization",
            repo_root,
            "Mf/DP/GaussianCore.lean",
        ),
        lean_entry(
            "mf-bsr-factor-core",
            "matrix-factorization",
            repo_root,
            "Mf/DP/BSRFactorCore.lean",
        ),
        lean_entry(
            "mf-optimization-ftrl",
            "matrix-factorization",
            repo_root,
            "Mf/Optimization/FTRLAnalysis.lean",
        ),
        lean_entry(
            "mf-bifr-packed-profile",
            "matrix-factorization",
            repo_root,
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
        "blocking": False,
        "evidence_kind": "optional_live_drift",
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
        "--format",
        "json",
        "--output",
        str(output_base.with_suffix(".json")),
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
    return command
