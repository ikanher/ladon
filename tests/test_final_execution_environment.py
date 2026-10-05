from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from ladon import lean_toolchain
from ladon.lean_toolchain import (
    LeanToolchainError,
    resolve_toolchain_context,
    verify_toolchain_identities,
)
from ladon.process_supervisor import ProcessResult
from ladon.scratch_replay import replay_scratch
from ladon.semantic_candidate_batch_worker import check_semantic_candidates
from ladon.semantic_candidate_worker import SemanticCandidateRequest, check_semantic_candidate
from ladon.semantic_lean_execution import prepare_direct_lean_execution


def _repository(root: Path) -> tuple[Path, Path, Path]:
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n")
    for name in ("lake", "lean"):
        executable = root / name
        executable.write_text("#!/bin/sh\nprintf 'Lean version 4.20.0\\n'\n")
        executable.chmod(0o755)
    library = root / ".lake" / "build" / "lib" / "lean"
    library.mkdir(parents=True)
    (library / "Main.olean").write_bytes(b"compiled fixture")
    return root / "lake", root / "lean", library


def test_version_preflight_and_worker_receive_the_same_final_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    lake, lean, library = _repository(tmp_path)
    original_runner = lean_toolchain.run_bounded_target_process
    versions: list[dict[str, str]] = []
    launched: list[dict[str, str]] = []

    def capture_preflight(command, **kwargs):
        if tuple(command)[-1] == "--version":
            versions.append(dict(kwargs["env"]))
        return original_runner(command, **kwargs)

    def capture_worker(command, **kwargs):
        launched.append(dict(kwargs["env"]))
        return ProcessResult(tuple(command), 1, "", "fixture process failure", 0.1)

    monkeypatch.setattr(lean_toolchain, "run_bounded_target_process", capture_preflight)
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)
    result = check_semantic_candidate(
        SemanticCandidateRequest(tmp_path, "Main", "True", "Main.fact", toolchain=context),
        runner=capture_worker,
    )

    assert result.status == "failed-checker"
    assert len(versions) == 2
    assert len(launched) == 1
    assert versions == [dict(context.environment), dict(context.environment)]
    assert launched == [dict(context.environment)]
    assert context.environment["LEAN_PATH"] == str(library.resolve())


def test_direct_execution_cannot_mutate_the_final_environment(tmp_path: Path) -> None:
    lake, lean, _ = _repository(tmp_path)
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)
    execution = prepare_direct_lean_execution(tmp_path, "Main", context)

    assert dict(execution.environment) == dict(context.environment)
    with pytest.raises(TypeError):
        execution.environment["LEAN_PATH"] = "/unbound/library"  # type: ignore[index]


@pytest.mark.parametrize("mutation", ["addition", "deletion", "symlink-retarget"])
@pytest.mark.parametrize("boundary", ["verification", "preparation"])
def test_changed_compiled_library_roots_fail_closed(
    tmp_path: Path, mutation: str, boundary: str,
) -> None:
    lake, lean, _ = _repository(tmp_path)
    old_target, new_target = tmp_path / "compiled-old", tmp_path / "compiled-new"
    old_target.mkdir()
    new_target.mkdir()
    dependency = tmp_path / ".lake" / "packages" / "dep" / ".lake" / "build" / "lib" / "lean"
    dependency.parent.mkdir(parents=True)
    dependency.symlink_to(old_target, target_is_directory=True)
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)

    if mutation == "addition":
        extra = tmp_path / ".lake" / "packages" / "extra" / ".lake" / "build" / "lib" / "lean"
        extra.mkdir(parents=True)
    else:
        dependency.unlink()
        if mutation == "symlink-retarget":
            dependency.symlink_to(new_target, target_is_directory=True)

    with pytest.raises(LeanToolchainError, match="library|compiled|execution environment|search path"):
        if boundary == "verification":
            verify_toolchain_identities(context)
        else:
            prepare_direct_lean_execution(tmp_path, "Main", context)


def test_caller_library_path_cannot_replace_or_taint_derived_context(tmp_path: Path) -> None:
    lake, lean, library = _repository(tmp_path)
    marker = "synthetic-private-library-7251"
    baseline = {"PATH": os.defpath, "LANG": "C"}
    clean = resolve_toolchain_context(
        tmp_path, lake_path=lake, lean_path=lean, environment=baseline,
    )
    tainted = resolve_toolchain_context(
        tmp_path, lake_path=lake, lean_path=lean,
        environment={**baseline, "LEAN_PATH": marker, "SYNTHETIC_PRIVATE_NAME": marker},
    )
    execution = prepare_direct_lean_execution(tmp_path, "Main", tainted)

    assert tainted.context_identity == clean.context_identity
    assert tainted.to_dict() == clean.to_dict()
    assert execution.environment["LEAN_PATH"] == str(library.resolve())
    assert "SYNTHETIC_PRIVATE_NAME" not in execution.environment
    assert marker not in json.dumps(tainted.to_dict())
    assert marker not in repr(execution.environment)


def test_direct_context_rejects_forged_derived_library_path(tmp_path: Path) -> None:
    lake, lean, _ = _repository(tmp_path)
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)
    marker = "synthetic-private-library-7251"

    with pytest.raises(LeanToolchainError) as caught:
        replace(context, environment={**context.environment, "LEAN_PATH": marker})

    assert marker not in str(caught.value)


def test_worker_rejects_a_repository_different_from_its_bound_context(tmp_path: Path) -> None:
    selected = tmp_path / "selected-repository"
    selected.mkdir()
    lake, lean, _ = _repository(selected)
    context = resolve_toolchain_context(selected, lake_path=lake, lean_path=lean)
    other = tmp_path / "other-repository"
    other.mkdir()
    _repository(other)
    launched: list[tuple[str, ...]] = []

    def runner(command, **_kwargs):
        launched.append(tuple(command))
        return ProcessResult(tuple(command), 1, "", "fixture process failure", 0.1)

    result = check_semantic_candidate(
        SemanticCandidateRequest(other, "Main", "True", "Main.fact", toolchain=context),
        runner=runner,
    )

    assert launched == []
    assert result.status == "invalid-worker-output"
    assert result.diagnostic is not None
    assert result.diagnostic["code"] == "toolchain-identity-changed"


@pytest.mark.parametrize("operation", ["single", "batch", "scratch"])
def test_worker_cannot_publish_after_compiled_library_roots_change(
    tmp_path: Path, operation: str,
) -> None:
    lake, lean, _ = _repository(tmp_path)
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)
    launches: list[tuple[str, ...]] = []

    def mutating_runner(command, **_kwargs):
        launches.append(tuple(command))
        extra = tmp_path / ".lake" / "packages" / "extra" / ".lake" / "build" / "lib" / "lean"
        extra.mkdir(parents=True)
        return ProcessResult(tuple(command), 0, "", "", 0.1)

    request = SemanticCandidateRequest(tmp_path, "Main", "True", "Main.fact", toolchain=context)
    if operation == "scratch":
        with pytest.raises(LeanToolchainError, match="library|compiled|execution environment|search path"):
            replay_scratch(
                repo_root=tmp_path, module="Main", goal="True", candidate="Main.fact",
                toolchain=context, runner=mutating_runner,
            )
    else:
        result = (
            check_semantic_candidate(request, runner=mutating_runner)
            if operation == "single"
            else check_semantic_candidates(request, ["Main.fact"], runner=mutating_runner)
        )
        assert result.status == "invalid-worker-output"
        assert result.diagnostic is not None
        assert result.diagnostic["code"] == "toolchain-identity-changed"
    assert len(launches) == 1
