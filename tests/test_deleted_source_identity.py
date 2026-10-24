from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ladon.lean_toolchain import (
    LeanToolchainError,
    resolve_toolchain_context,
    verify_toolchain_identities,
)


def _tool(path: Path, version: str) -> Path:
    path.write_text(f"#!/bin/sh\nprintf '%s\\n' '{version}'\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def _repository(root: Path) -> tuple[Path, Path]:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    sources = root / "src" / "nested"
    sources.mkdir(parents=True)
    (sources / "A.lean").write_text("def a := true\n", encoding="utf-8")
    (sources / "B.lean").write_text("def b := true\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "lean-toolchain", "src"], check=True)
    return (
        _tool(root / "lake", "Lake version 4.20.0"),
        _tool(root / "lean", "Lean version 4.20.0"),
    )


def test_tracked_deleted_source_and_missing_parent_are_current_tree_material(
    tmp_path: Path,
) -> None:
    lake, lean = _repository(tmp_path)
    initial = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)

    (tmp_path / "src" / "nested" / "A.lean").unlink()
    (tmp_path / "src" / "nested" / "B.lean").unlink()
    (tmp_path / "src" / "nested").rmdir()
    (tmp_path / "src").rmdir()

    deleted = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)
    assert deleted.source_tree_identity != initial.source_tree_identity
    with pytest.raises(LeanToolchainError, match="source tree identity changed"):
        verify_toolchain_identities(initial)

    (tmp_path / "src" / "nested").mkdir(parents=True)
    (tmp_path / "src" / "nested" / "A.lean").write_text("def a := true\n", encoding="utf-8")
    (tmp_path / "src" / "nested" / "B.lean").write_text("def b := true\n", encoding="utf-8")
    with pytest.raises(LeanToolchainError, match="source tree identity changed"):
        verify_toolchain_identities(deleted)
    verify_toolchain_identities(initial)


def test_staged_and_unstaged_tracked_deletions_have_same_current_tree_identity(
    tmp_path: Path,
) -> None:
    lake, lean = _repository(tmp_path)
    (tmp_path / "src" / "nested" / "A.lean").unlink()
    unstaged = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)

    subprocess.run(["git", "-C", str(tmp_path), "add", "-u", "src"], check=True)
    staged = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)
    assert staged.source_tree_identity == unstaged.source_tree_identity
    assert staged.context_identity == unstaged.context_identity
