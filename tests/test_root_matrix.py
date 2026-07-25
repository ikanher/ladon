from __future__ import annotations

from pathlib import Path

from ladon.root_matrix import (
    default_root_matrix,
    matrix_command,
    select_matrix_entries,
)


def test_root_matrix_generates_ladon_commands() -> None:
    entry = select_matrix_entries(
        default_root_matrix({"quux": "/repos/quux"}),
        ["quux-propagation"],
    )[0]
    command = matrix_command(entry, output_root=Path("out"), ladon_bin=Path("bin/ladon"))

    assert command[:2] == ["bin/ladon", "--repo-root"]
    assert "--root" in command
    assert "Quux/Semantics/Propagation.lean" in command
    assert "--format" in command
    assert "json" in command
    assert "--output" in command
    assert "out/quux/quux-propagation.json" in command
    assert "--extraction-backend" in command
    assert "--skip-build" not in command


def test_root_matrix_has_no_implicit_sibling_roots() -> None:
    entries = default_root_matrix(environment={})

    assert entries == []


def test_root_matrix_uses_lean_backend_for_explicit_owner_roots() -> None:
    entries = select_matrix_entries(
        default_root_matrix(
            {
                "quux": "/repos/quux",
                "matrix-factorization": "/repos/matrix-factorization",
            }
        ),
        [
            "quux-bifr-rmse-problem",
            "mf-gaussian-core",
            "mf-bsr-factor-core",
            "mf-optimization-ftrl",
        ],
    )

    assert {entry["name"] for entry in entries if entry["backend"] == "lean"} == {
        "quux-bifr-rmse-problem",
        "mf-gaussian-core",
        "mf-bsr-factor-core",
        "mf-optimization-ftrl",
    }


def test_root_matrix_keeps_project_roots_text_backed() -> None:
    entries = select_matrix_entries(
        default_root_matrix(
            {
                "quux": "/repos/quux",
                "matrix-factorization": "/repos/matrix-factorization",
            }
        ),
        ["quux-project", "mf-project"],
    )

    assert [entry["backend"] for entry in entries] == ["text", "text"]


def test_root_matrix_accepts_explicit_optional_repository_roots() -> None:
    entries = select_matrix_entries(
        default_root_matrix(
            {
                "quux": "/portable/quux",
                "matrix-factorization": "/portable/matrix-factorization",
            }
        ),
        ["quux-project", "mf-project"],
    )

    assert [entry["repo_root"] for entry in entries] == [
        "/portable/quux",
        "/portable/matrix-factorization",
    ]


def test_root_matrix_selects_named_entries() -> None:
    entries = select_matrix_entries(
        default_root_matrix(
            {
                "quux": "/repos/quux",
                "matrix-factorization": "/repos/matrix-factorization",
            }
        ),
        ["quux-project", "mf-bifr-packed-profile"],
    )

    assert [entry["name"] for entry in entries] == [
        "quux-project",
        "mf-bifr-packed-profile",
    ]


def test_root_matrix_unknown_entry_is_explicit_error() -> None:
    try:
        select_matrix_entries(
            default_root_matrix({"quux": "/repos/quux"}),
            ["missing-root"],
        )
    except ValueError as exc:
        assert "unknown root matrix entries" in str(exc)
    else:
        raise AssertionError("missing root matrix entry should fail")
