from __future__ import annotations

from pathlib import Path

import pytest

from ladon.lean_toolchain import LeanToolchainError, resolve_toolchain_context


def _tool(path: Path, version: str) -> Path:
    path.write_text(f"#!/bin/sh\nprintf '%s\\n' '{version}'\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_explicit_toolchain_context_is_pinned_and_sanitized(tmp_path: Path) -> None:
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")

    context = resolve_toolchain_context(
        tmp_path,
        lake_path=lake,
        lean_path=lean,
        selection_mode="explicit",
        environment={"PATH": "/shadow", "SECRET": "hidden", "HOME": "/tmp"},
    )

    assert context.selection_mode == "explicit"
    assert context.lake_path == lake.resolve()
    assert context.lean_path == lean.resolve()
    assert "SECRET" not in context.environment_keys
    assert context.environment["PATH"].startswith(str(tmp_path))


def test_explicit_selection_does_not_fall_back_to_ambient_path(tmp_path: Path) -> None:
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    shadow = tmp_path / "shadow"
    shadow.mkdir()
    _tool(shadow / "lake", "Lake version 4.20.0")
    _tool(shadow / "lean", "Lean version 4.20.0")
    with pytest.raises(LeanToolchainError, match="requires lake and lean paths"):
        resolve_toolchain_context(tmp_path, selection_mode="explicit", environment={"PATH": str(shadow)})


def test_pin_mismatch_fails_before_context_creation(tmp_path: Path) -> None:
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    lake = _tool(tmp_path / "lake", "Lake version 4.19.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.19.0")
    with pytest.raises(LeanToolchainError, match="pin mismatch"):
        resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)
