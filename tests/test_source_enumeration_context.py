from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from ladon import source_enumeration
from ladon.process_supervisor import ProcessResult
from ladon.source_enumeration import SourceEnumerationError, resolve_source_enumeration


def _git(root: Path) -> Path:
    path = root / "git"
    path.write_text("#!/bin/sh\nexit 0\n")
    path.chmod(0o755)
    return path


def test_git_selection_and_final_environment_do_not_follow_host_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git = _git(tmp_path)
    final = {"PATH": "/selected/lean", "HOME": "/selected/home", "LEAN_PATH": "/compiled"}
    context = resolve_source_enumeration({"PATH": str(tmp_path)}, final)
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def runner(command: tuple[str, ...], **kwargs: object) -> ProcessResult:
        calls.append((command, kwargs))
        return ProcessResult(command, 0, "Project.lean\0lean-toolchain\0", "", 0.1)

    monkeypatch.setattr(source_enumeration, "run_bounded_target_process", runner)
    expected = dict(final)
    final["HOME"] = "/changed/caller"
    monkeypatch.setenv("PATH", "/changed/host")
    monkeypatch.setenv("HOME", "/changed/host-home")
    monkeypatch.setenv("API_TOKEN", "synthetic-secret")
    assert context.paths(tmp_path) == ("Project.lean", "lean-toolchain")
    assert context.paths(tmp_path) == ("Project.lean", "lean-toolchain")
    assert all(command[0] == str(git) and kwargs["env"] == expected
               for command, kwargs in calls)
    assert all(kwargs["cwd"] == tmp_path for _, kwargs in calls)
    assert calls[0][1]["max_rss_bytes"] == 256 * 1024 * 1024
    with pytest.raises(TypeError):
        context.environment["HOME"] = "changed"  # type: ignore[index]


@pytest.mark.parametrize("search", [{}, {"PATH": ""}, {"PATH": "/missing-git-directory"}])
def test_absent_selected_git_uses_recorded_fallback_without_host_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, search: dict[str, str]
) -> None:
    _git(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    context = resolve_source_enumeration(search, {"PATH": "/selected/lean"})
    assert context.git_path is None
    assert context.paths(tmp_path) is None
    assert context.to_dict()["mode"] == "filesystem"


def test_environment_values_affect_identity_without_being_published(tmp_path: Path) -> None:
    _git(tmp_path)
    context = resolve_source_enumeration({"PATH": str(tmp_path)}, {"HOME": "synthetic-home"})
    changed = replace(context, environment={"HOME": "changed-synthetic-home"})
    assert changed.context_identity != context.context_identity
    assert "synthetic-home" not in json.dumps(context.to_dict())
    assert "changed-synthetic-home" not in json.dumps(changed.to_dict())
    assert context.to_dict()["environmentKeys"] == ["HOME"]


@pytest.mark.parametrize("during_run", [False, True])
def test_changed_git_executable_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, during_run: bool
) -> None:
    git = _git(tmp_path)
    context = resolve_source_enumeration({"PATH": str(tmp_path)}, {})
    calls = 0

    def runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        nonlocal calls
        calls += 1
        git.write_text("changed executable")
        return ProcessResult(command, 0, "", "", 0.1)

    monkeypatch.setattr(source_enumeration, "run_bounded_target_process", runner)
    if not during_run:
        git.write_text("changed executable")
    with pytest.raises(SourceEnumerationError, match="identity changed"):
        context.paths(tmp_path)
    assert calls == int(during_run)


@pytest.mark.parametrize(
    "failure", ["ordinary", "timeout", "output", "memory", "localized", "misleading-path"]
)
def test_process_failures_do_not_fallback_or_echo_child_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    _git(tmp_path)
    context = resolve_source_enumeration({"PATH": str(tmp_path)}, {})
    marker = "synthetic-private-output"

    def runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        diagnostic = "kein Git-Repository" if failure == "localized" else "not a git repository"
        if failure == "misleading-path":
            diagnostic = "fatal: detected dubious ownership in repository '/not a git repository'"
        return ProcessResult(
            command, 1 if failure == "ordinary" else 128, marker, diagnostic + marker, 0.1,
            timed_out=failure == "timeout", output_limited=failure == "output",
            memory_limited=failure == "memory",
        )

    monkeypatch.setattr(source_enumeration, "run_bounded_target_process", runner)
    with pytest.raises(SourceEnumerationError) as caught:
        context.paths(tmp_path)
    assert marker not in str(caught.value)


def test_nonrepository_fallback_is_explicit_and_remains_bound_to_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git = _git(tmp_path)
    context = resolve_source_enumeration({"PATH": str(tmp_path)}, {})

    def runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        return ProcessResult(command, 128, "", "fatal: not a git repository", 0.1)

    monkeypatch.setattr(source_enumeration, "run_bounded_target_process", runner)
    assert context.paths(tmp_path) is None
    assert context.to_dict()["mode"] == "git-with-nonrepository-fallback"
    git.unlink()
    with pytest.raises(SourceEnumerationError, match="unavailable"):
        context.paths(tmp_path)


@pytest.mark.parametrize("failure", ["launch", "malformed-list"])
def test_launch_errors_and_unframed_paths_are_finite_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    _git(tmp_path)
    context = resolve_source_enumeration({"PATH": str(tmp_path)}, {})
    marker = "synthetic-private-output"

    def runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        if failure == "launch":
            raise OSError(marker)
        return ProcessResult(command, 0, marker, "", 0.1)

    monkeypatch.setattr(source_enumeration, "run_bounded_target_process", runner)
    with pytest.raises(SourceEnumerationError) as caught:
        context.paths(tmp_path)
    assert marker not in str(caught.value)


def _lean_repository(root: Path) -> tuple[Path, Path]:
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n")
    for name in ("lake", "lean"):
        path = root / name
        path.write_text("#!/bin/sh\nprintf 'Lean version 4.20.0\\n'\n")
        path.chmod(0o755)
    return root / "lake", root / "lean"


def test_toolchain_enumeration_runs_exact_final_environment_with_library_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ladon.lean_toolchain import resolve_toolchain_context, verify_toolchain_identities

    lake, lean = _lean_repository(tmp_path)
    roots = tmp_path / ".lake" / "build" / "lib" / "lean"
    roots.mkdir(parents=True)
    utilities = tmp_path / "utilities"
    utilities.mkdir()
    _git(utilities)
    observed: list[object] = []

    def runner(command: tuple[str, ...], **kwargs: object) -> ProcessResult:
        observed.append(kwargs["env"])
        return ProcessResult(command, 0, "lean-toolchain\0", "", 0.1)

    monkeypatch.setattr(source_enumeration, "run_bounded_target_process", runner)
    context = resolve_toolchain_context(
        tmp_path, lake_path=lake, lean_path=lean,
        environment={"PATH": str(utilities), "HOME": "/selected/home", "API_TOKEN": "discarded"},
    )
    verify_toolchain_identities(context)
    assert context.source_enumeration is not None
    assert context.source_enumeration.environment == context.environment
    assert context.environment["LEAN_PATH"] == str(roots)
    assert observed and all(environment == context.environment for environment in observed)
    assert "API_TOKEN" not in context.source_enumeration.environment


def test_toolchain_git_exclusions_survive_changed_host_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ladon.lean_toolchain import resolve_toolchain_context, verify_toolchain_identities

    git = shutil.which("git")
    assert git is not None
    subprocess.run([git, "init", "-q", str(tmp_path)], check=True)
    lake, lean = _lean_repository(tmp_path)
    (tmp_path / ".gitignore").write_text("Ignored.lean\n")
    ignored = tmp_path / "Ignored.lean"
    ignored.write_text("def ignored := true\n")
    context = resolve_toolchain_context(
        tmp_path, lake_path=lake, lean_path=lean,
        environment={"PATH": str(Path(git).parent), "HOME": str(tmp_path / "selected-home")},
    )
    before = context.context_identity
    shadow = tmp_path / "shadow"
    shadow.mkdir()
    _git(shadow)
    monkeypatch.setenv("PATH", str(shadow))
    monkeypatch.setenv("HOME", str(tmp_path / "changed-home"))
    ignored.write_text("def ignored := false\n")
    verify_toolchain_identities(context)
    assert context.context_identity == before
    assert context.source_enumeration is not None
    assert context.source_enumeration.git_path == Path(git).resolve()


def test_toolchain_verification_rejects_changed_selected_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ladon.lean_toolchain import (
        LeanToolchainError,
        resolve_toolchain_context,
        verify_toolchain_identities,
    )

    lake, lean = _lean_repository(tmp_path)
    git = _git(tmp_path)

    def runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        return ProcessResult(command, 0, "lean-toolchain\0", "", 0.1)

    monkeypatch.setattr(source_enumeration, "run_bounded_target_process", runner)
    context = resolve_toolchain_context(
        tmp_path, lake_path=lake, lean_path=lean, environment={"PATH": str(tmp_path)},
    )
    git.write_text("changed selected Git")
    with pytest.raises(LeanToolchainError, match="enumeration executable identity changed"):
        verify_toolchain_identities(context)


def test_empty_toolchain_environment_records_filesystem_fallback_inside_git_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ladon.lean_toolchain import (
        LeanToolchainError,
        resolve_toolchain_context,
        verify_toolchain_identities,
    )

    git = shutil.which("git")
    assert git is not None
    subprocess.run([git, "init", "-q", str(tmp_path)], check=True)
    lake, lean = _lean_repository(tmp_path)
    monkeypatch.setenv("PATH", str(Path(git).parent))
    (tmp_path / ".gitignore").write_text("Ignored.lean\n")
    ignored = tmp_path / "Ignored.lean"
    ignored.write_text("def ignored := true\n")
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean, environment={})
    assert context.source_enumeration is not None
    assert context.source_enumeration.git_path is None
    assert context.source_enumeration.to_dict()["mode"] == "filesystem"
    ignored.write_text("def ignored := false\n")
    with pytest.raises(LeanToolchainError, match="source tree identity changed"):
        verify_toolchain_identities(context)
