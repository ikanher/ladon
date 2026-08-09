from __future__ import annotations

from pathlib import Path

import pytest

from ladon.root_matrix import (
    default_root_matrix,
    matrix_command,
    select_matrix_entries,
)


def test_root_matrix_generates_ladon_commands() -> None:
    entry = select_matrix_entries(
        default_root_matrix({"matrix-factorization": "/repos/matrix-factorization"}),
        ["mf-gaussian-core"],
    )[0]
    command = matrix_command(entry, output_root=Path("out"), ladon_bin=Path("bin/ladon"))

    assert command[:2] == ["bin/ladon", "--repo-root"]
    assert "Mf/DP/GaussianCore.lean" in command
    assert "out/matrix-factorization/mf-gaussian-core.json" in command
    assert "--extraction-backend" in command
    assert "--skip-build" not in command


def test_root_matrix_has_no_implicit_sibling_roots() -> None:
    assert default_root_matrix(environment={}) == []


def test_root_matrix_uses_lean_backend_for_explicit_owner_roots() -> None:
    entries = default_root_matrix(
        {"matrix-factorization": "/repos/matrix-factorization"}
    )
    assert {
        entry["name"] for entry in entries if entry["backend"] == "lean"
    } == {
        "mf-gaussian-core",
        "mf-bsr-factor-core",
        "mf-optimization-ftrl",
        "mf-bifr-packed-profile",
    }


def test_root_matrix_keeps_project_root_text_backed() -> None:
    entry = select_matrix_entries(
        default_root_matrix({"matrix-factorization": "/repos/matrix-factorization"}),
        ["mf-project"],
    )[0]
    assert entry["backend"] == "text"


def test_root_matrix_rejects_separated_or_unknown_repository_roots() -> None:
    with pytest.raises(ValueError, match="unknown optional repository roots"):
        default_root_matrix({"quux": "/separated/quux"}, environment={})


def test_root_matrix_unknown_entry_is_explicit_error() -> None:
    entries = default_root_matrix(
        {"matrix-factorization": "/repos/matrix-factorization"}
    )
    with pytest.raises(ValueError, match="unknown root matrix entries"):
        select_matrix_entries(entries, ["missing-root"])
