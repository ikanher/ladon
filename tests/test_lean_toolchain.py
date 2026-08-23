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


def test_git_ignored_tree_is_outside_source_identity(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("temp/\n", encoding="utf-8")
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    source = tmp_path / "Project.lean"
    source.write_text("def visible := true\n", encoding="utf-8")
    ignored = tmp_path / "temp" / "logs" / "logs" / "Ignored.lean"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("def ignored := true\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", ".gitignore", "lean-toolchain", "Project.lean"],
        check=True,
    )
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)

    ignored.write_text("def ignored := false\n", encoding="utf-8")

    verify_toolchain_identities(context)


def test_tracked_contained_source_symlink_is_bound_to_target_bytes(
    tmp_path: Path,
) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    scripts = tmp_path / "scripts" / "bench"
    scripts.mkdir(parents=True)
    target = scripts / "runner"
    target.write_text("first\n", encoding="utf-8")
    link = scripts / "runner.py"
    link.symlink_to("runner")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "lean-toolchain", "scripts"],
        check=True,
    )
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)

    verify_toolchain_identities(context)
    target.write_text("second\n", encoding="utf-8")

    with pytest.raises(LeanToolchainError, match="source tree identity changed"):
        verify_toolchain_identities(context)


def test_source_symlink_retarget_to_equal_bytes_changes_identity(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "first").write_text("same\n", encoding="utf-8")
    (scripts / "second").write_text("same\n", encoding="utf-8")
    link = scripts / "runner.py"
    link.symlink_to("first")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "lean-toolchain", "scripts"],
        check=True,
    )
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)

    link.unlink()
    link.symlink_to("second")

    with pytest.raises(LeanToolchainError, match="source tree identity changed"):
        verify_toolchain_identities(context)


def test_source_symlink_replaced_by_equal_regular_file_changes_identity(
    tmp_path: Path,
) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "runner").write_text("same\n", encoding="utf-8")
    link = scripts / "runner.py"
    link.symlink_to("runner")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "lean-toolchain", "scripts"],
        check=True,
    )
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)

    link.unlink()
    link.write_text("same\n", encoding="utf-8")

    with pytest.raises(LeanToolchainError, match="source tree identity changed"):
        verify_toolchain_identities(context)


def test_source_path_rejects_symlinked_parent_directory(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    project = tmp_path / "Project"
    project.mkdir()
    source = project / "Run.lean"
    source.write_text("def same := true\n", encoding="utf-8")
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / "Run.lean").write_text("def same := true\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "lean-toolchain", "Project/Run.lean"],
        check=True,
    )
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)

    source.unlink()
    project.rmdir()
    project.symlink_to(".hidden", target_is_directory=True)

    with pytest.raises(LeanToolchainError, match="symlink ancestor"):
        verify_toolchain_identities(context)


def test_source_symlink_target_respects_path_depth_limit(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".hidden/\n", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    target = tmp_path / ".hidden" / Path(*(["deep"] * 64)) / "runner"
    target.parent.mkdir(parents=True)
    target.write_text("safe\n", encoding="utf-8")
    (scripts / "runner.py").symlink_to(Path("..") / target.relative_to(tmp_path))
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "add",
            ".gitignore",
            "lean-toolchain",
            "scripts/runner.py",
        ],
        check=True,
    )
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")

    with pytest.raises(LeanToolchainError, match="symlink target exceeds safety bounds"):
        resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)


@pytest.mark.parametrize(
    "link_kind",
    ["absolute-escape", "relative-escape", "chain", "dangling", "cycle", "directory"],
)
def test_unsafe_source_symlink_fails_closed(tmp_path: Path, link_kind: str) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    target = scripts / "runner"
    target.write_text("safe\n", encoding="utf-8")
    link = scripts / "runner.py"
    if link_kind in {"absolute-escape", "relative-escape"}:
        outside = tmp_path.parent / f"{tmp_path.name}-outside"
        outside.write_text("outside\n", encoding="utf-8")
        link.symlink_to(outside if link_kind == "absolute-escape" else f"../../{outside.name}")
    elif link_kind == "chain":
        alias = scripts / "alias"
        alias.symlink_to("runner")
        link.symlink_to("alias")
    elif link_kind == "dangling":
        link.symlink_to("missing")
    elif link_kind == "directory":
        directory = scripts / "directory"
        directory.mkdir()
        link.symlink_to("directory")
    else:
        link.symlink_to("runner.py")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "lean-toolchain", "scripts"],
        check=True,
    )
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")

    with pytest.raises(LeanToolchainError, match="source identity"):
        resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)


def test_untracked_nested_repository_directory_is_not_treated_as_source_file(
    tmp_path: Path,
) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    nested = tmp_path / "src" / "external-project"
    nested.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(nested)], check=True)
    nested.joinpath("Foreign.lean").write_text("def foreign := true\n", encoding="utf-8")
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")

    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)

    nested.joinpath("Foreign.lean").write_text("def foreign := false\n", encoding="utf-8")
    verify_toolchain_identities(context)


def test_non_git_fallback_prunes_review_and_build_trees(tmp_path: Path) -> None:
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    source = tmp_path / "Project.lean"
    source.write_text("def visible := true\n", encoding="utf-8")
    ignored = tmp_path / "temp" / "packet" / "Ignored.lean"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("def ignored := true\n", encoding="utf-8")
    lake = _tool(tmp_path / "lake", "Lake version 4.20.0")
    lean = _tool(tmp_path / "lean", "Lean version 4.20.0")
    context = resolve_toolchain_context(
        tmp_path,
        lake_path=lake,
        lean_path=lean,
        environment={"PATH": str(tmp_path)},
    )

    ignored.write_text("def ignored := false\n", encoding="utf-8")

    verify_toolchain_identities(context)
