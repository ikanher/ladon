from __future__ import annotations

from pathlib import Path

from ladon.root_matrix import (
    default_root_matrix,
    matrix_command,
    select_matrix_entries,
)


def test_root_matrix_generates_ladon_commands() -> None:
    entry = select_matrix_entries(default_root_matrix(), ["quux-propagation"])[0]
    command = matrix_command(entry, output_root=Path("out"), ladon_bin=Path("bin/ladon"))

    assert command[:2] == ["bin/ladon", "--repo-root"]
    assert "--root" in command
    assert "Quux/Semantics/Propagation.lean" in command
    assert "--output-json" in command
    assert "out/quux/quux-propagation.json" in command
    assert "--extraction-backend" in command


def test_root_matrix_selects_named_entries() -> None:
    entries = select_matrix_entries(
        default_root_matrix(),
        ["quux-project", "mf-bifr-packed-profile"],
    )

    assert [entry["name"] for entry in entries] == [
        "quux-project",
        "mf-bifr-packed-profile",
    ]


def test_root_matrix_unknown_entry_is_explicit_error() -> None:
    try:
        select_matrix_entries(default_root_matrix(), ["missing-root"])
    except ValueError as exc:
        assert "unknown root matrix entries" in str(exc)
    else:
        raise AssertionError("missing root matrix entry should fail")
