from __future__ import annotations

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
        resolve_toolchain_context(
            tmp_path, selection_mode="explicit", environment={"PATH": str(shadow)}
        )


def test_pin_mismatch_fails_before_context_creation(tmp_path: Path) -> None:
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    lake = _tool(tmp_path / "lake", "Lake version 4.19.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.19.0")
    with pytest.raises(LeanToolchainError, match="pin mismatch"):
        resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)


def test_pin_comparison_is_exact_not_a_version_substring(tmp_path: Path) -> None:
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.2.0\n", encoding="utf-8")
    lake = _tool(tmp_path / "lake", "Lake version 5.0.0 (Lean version 4.20.0)")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")
    with pytest.raises(LeanToolchainError, match="pin mismatch"):
        resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)


def test_version_preflight_is_output_bounded(tmp_path: Path) -> None:
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    lake = tmp_path / "lake"
    lake.write_text("#!/bin/sh\nyes x | head -c 1000000\n", encoding="utf-8")
    lake.chmod(0o755)
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")
    with pytest.raises(LeanToolchainError, match="output bounds"):
        resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)


def test_selected_executable_identity_is_rechecked(tmp_path: Path) -> None:
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)

    lean.write_text("#!/bin/sh\nprintf 'Lean version 4.20.0 changed\\n'\n", encoding="utf-8")

    with pytest.raises(LeanToolchainError, match="identity changed: lean"):
        verify_toolchain_identities(context)


def test_nested_lean_source_is_part_of_source_tree_identity(tmp_path: Path) -> None:
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")
    nested = tmp_path / "Project" / "Hidden.lean"
    nested.parent.mkdir()
    nested.write_text("def hidden := true\n", encoding="utf-8")
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)

    nested.write_text("def hidden := false\n", encoding="utf-8")

    with pytest.raises(LeanToolchainError, match="source tree identity changed"):
        verify_toolchain_identities(context)
