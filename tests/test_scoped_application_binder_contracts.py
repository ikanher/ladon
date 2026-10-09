"""Regression reproduction for the retained Adam-energy field failure.

Run with: pytest -q temp/field-reliability-red/test_le_trans_duplicate_binders.py

The Nat instance keeps this probe within Lean's core library when Mathlib is
not available.  It preserves the field goal's ordered context and application
shape: le_trans has an unresolved middle term and therefore must yield
applicable-with-residuals.  The mixed call also checks that a separate
applicable candidate survives a row-local substitution failure.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "lean_integration"
GOAL = (
    "∀ (β : Nat), 0 ≤ β → β ≤ 1 → ∀ (s t : Nat), "
    "s ≤ t → β ^ t ≤ β ^ s"
)


def _fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "fixture"
    shutil.copytree(FIXTURE, repo)
    module = repo / "LadonFixture.lean"
    with module.open("a", encoding="utf-8") as source:
        source.write(
            "\n-- Core-only stand-ins for the Mathlib relations used by the field report.\n"
            "theorem le_trans {a b c : Nat} (h : a ≤ b) (h : b ≤ c) : a ≤ c :=\n"
            "  Nat.le_trans ‹a ≤ b› h\n"
            "theorem le_of_lt {a b : Nat} (hab : a < b) : a ≤ b :=\n"
            "  Nat.le_of_lt hab\n"
        )
    built = subprocess.run(
        ["lake", "build", "LadonFixture"], cwd=repo,
        text=True, capture_output=True, check=False, timeout=90,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    return repo


def _discover(repo: Path, *candidates: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable, "-m", "ladon.entrypoint", "proof-search", "discover",
            "--repo-root", str(repo), "--module", "LadonFixture",
            "--goal", GOAL,
            *[arg for candidate in candidates for arg in ("--candidate", candidate)],
            "--timeout-seconds", "30", "--max-rss-mib", "4096",
            "--projection", "audit", "--format", "json",
        ],
        cwd=ROOT, text=True, capture_output=True, check=False, timeout=90,
    )


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_le_trans_keeps_duplicate_binder_occurrences_and_residuals(tmp_path: Path) -> None:
    repo = _fixture(tmp_path)
    _assert_single_application(repo)
    _assert_mixed_applications(repo)


def _assert_single_application(repo: Path) -> None:
    single = _discover(repo, "le_trans")
    assert single.returncode == 0, single.stderr
    result = json.loads(single.stdout)
    assert result["status"] == "available"
    assert result["candidates"][0]["check"]["status"] == "applicable-with-residuals"
    residuals = result["candidates"][0]["check"]["residualPremises"]
    assert len(residuals) == 2


def _assert_mixed_applications(repo: Path) -> None:
    mixed = _discover(repo, "le_trans", "le_of_lt")
    assert mixed.returncode == 0, mixed.stderr
    batch = json.loads(mixed.stdout)
    assert batch["status"] == "available"
    rows = {row["name"].rsplit(".", 1)[-1]: row["check"] for row in batch["candidates"]}
    assert rows["le_trans"]["status"] == "applicable-with-residuals"
    assert rows["le_of_lt"]["status"] == "applicable-with-residuals"
    assert rows["le_of_lt"]["residualPremises"]

