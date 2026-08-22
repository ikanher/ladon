from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

from ladon.process_supervisor import ProcessResult
from ladon.scratch_replay import build_scratch_source, replay_scratch


def test_scratch_source_is_independent_and_digestible() -> None:
    source = build_scratch_source("Main", "Nat", "Main.zero")
    assert "example : Nat" in source
    assert "exact Main.zero" in source


def test_scratch_source_preserves_ordered_local_context() -> None:
    source = build_scratch_source(
        "Main",
        "value = value",
        "Main.identity",
        ({"name": "value", "type": "Nat"}, {"name": "h", "type": "value = value"}),
    )
    assert "example (value : Nat) (h : value = value) : value = value" in source


def test_scratch_replay_preserves_compiled_or_rejected_outcome(tmp_path: Path) -> None:
    class Toolchain:
        lake_path = tmp_path / "lake"
        lean_path = tmp_path / "lean"
        environment = MappingProxyType({})

    def runner(*_args: object, **_kwargs: object) -> ProcessResult:
        return ProcessResult(("lake", "env", "lean"), 0, "ok", "", 0.1)

    result = replay_scratch(
        repo_root=tmp_path,
        module="Main",
        goal="Nat",
        candidate="Main.zero",
        toolchain=Toolchain(),  # type: ignore[arg-type]
        runner=runner,
    )
    assert result.status == "compiled"
    assert result.source_digest.startswith("sha256:")


def test_nonzero_scratch_exit_is_process_failure_without_framed_rejection(
    tmp_path: Path,
) -> None:
    class Toolchain:
        lake_path = tmp_path / "lake"
        lean_path = tmp_path / "lean"
        environment = MappingProxyType({})

    def runner(*_args: object, **_kwargs: object) -> ProcessResult:
        return ProcessResult(("lake", "env", "lean"), 1, "", "syntax error", 0.1)

    result = replay_scratch(
        repo_root=tmp_path,
        module="Main",
        goal="True",
        candidate="True.intro",
        toolchain=Toolchain(),  # type: ignore[arg-type]
        runner=runner,
    )

    assert result.status == "process-failed"
