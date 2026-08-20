from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

import ladon.theorem_capsule_materialization as materialization
from ladon.theorem_capsule_materialization import materialize_theorem_capsule
from ladon.theorem_capsule_models import (
    CapsuleContentError,
    CapsuleInvocationError,
    TheoremPlan,
)
from ladon.theorem_capsule_planning import plan_theorem_capsule

FIXTURE = Path(__file__).parent / "fixtures" / "theorem_capsule"
MULTI_ROOT_FIXTURE = Path(__file__).parent / "fixtures" / "theorem_capsule_multi_root"


@pytest.fixture
def planned_repository(tmp_path: Path) -> tuple[Path, TheoremPlan]:
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    build = subprocess.run(
        ["lake", "build"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if build.returncode != 0:
        pytest.fail(build.stderr or build.stdout)
    return root, plan_theorem_capsule(root, "CapsuleFixture.chosen")


def test_materialization_preserves_prefix_and_imports(
    planned_repository: tuple[Path, TheoremPlan],
    tmp_path: Path,
) -> None:
    root, plan = planned_repository
    output = tmp_path / "capsule"
    before = tree_state(root)

    manifest = materialize_theorem_capsule(plan, output)

    target = (output / "CapsuleFixture.lean").read_text(encoding="utf-8")
    assert "local notation" in target
    assert "theorem chosen" in target
    assert "theorem later" not in target
    assert_materialized_inputs(root, output, plan)
    assert manifest.payload["status"] == "materialized_unverified"
    assert manifest.payload["nonclaims"]
    assert tree_state(root) == before


def assert_materialized_inputs(
    root: Path,
    output: Path,
    plan: TheoremPlan,
) -> None:
    assert (output / "CapsuleFixture" / "Base.lean").read_bytes() == (
        root / "CapsuleFixture" / "Base.lean"
    ).read_bytes()
    assert (output / "CapsuleFixture" / "Large.lean").is_file()
    assert (output / "lean-toolchain").is_file()
    assert (output / "lakefile.toml").is_file()
    assert (
        json.loads((output / "plan.json").read_text())["planIdentity"] == plan.identity
    )


def test_materialization_is_deterministic(
    planned_repository: tuple[Path, TheoremPlan],
    tmp_path: Path,
) -> None:
    _, plan = planned_repository
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_manifest = materialize_theorem_capsule(plan, first)
    second_manifest = materialize_theorem_capsule(plan, second)

    assert first_manifest.to_bytes() == second_manifest.to_bytes()
    assert tree_state(first) == tree_state(second)


def test_reproducible_tar_output(
    planned_repository: tuple[Path, TheoremPlan],
    tmp_path: Path,
) -> None:
    _, plan = planned_repository
    first = tmp_path / "first.tar"
    second = tmp_path / "second.tar"

    materialize_theorem_capsule(plan, first)
    materialize_theorem_capsule(plan, second)

    assert first.read_bytes() == second.read_bytes()


def test_reproducible_zip_output(
    planned_repository: tuple[Path, TheoremPlan],
    tmp_path: Path,
) -> None:
    _, plan = planned_repository
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    first_manifest = materialize_theorem_capsule(plan, first)
    second_manifest = materialize_theorem_capsule(plan, second)

    assert first.read_bytes() == second.read_bytes()
    assert first_manifest.to_bytes() == second_manifest.to_bytes()
    assert first_manifest.payload["outputKind"] == "archive"
    with zipfile.ZipFile(first) as archive:
        assert archive.namelist() == sorted(archive.namelist())
        assert "capsule.json" in archive.namelist()


def test_materialization_preserves_multiple_declared_source_roots(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    shutil.copytree(MULTI_ROOT_FIXTURE, root)
    subprocess.run(["lake", "build"], cwd=root, check=True, capture_output=True)
    plan = plan_theorem_capsule(root, "Main.selected")
    output = tmp_path / "capsule"

    materialize_theorem_capsule(plan, output)

    roots = {row["path"] for row in plan.repository["sourceRoots"]}
    assert roots == {"src", "support"}
    assert (output / "src" / "Main.lean").is_file()
    assert (output / "support" / "Support.lean").is_file()
    assert "Main.later" not in (output / "src" / "Main.lean").read_text()


def test_materialization_rejects_stale_plan(
    planned_repository: tuple[Path, TheoremPlan],
    tmp_path: Path,
) -> None:
    root, plan = planned_repository
    source = root / "CapsuleFixture" / "Base.lean"
    source.write_text(source.read_text() + "\n-- drift\n", encoding="utf-8")

    with pytest.raises(CapsuleContentError, match="changed"):
        materialize_theorem_capsule(plan, tmp_path / "capsule")


def test_materialization_rejects_output_inside_repository(
    planned_repository: tuple[Path, TheoremPlan],
) -> None:
    root, plan = planned_repository
    with pytest.raises(CapsuleInvocationError, match="outside"):
        materialize_theorem_capsule(plan, root / "generated-capsule")


def test_materialization_rejects_unsafe_plan_path(
    planned_repository: tuple[Path, TheoremPlan],
    tmp_path: Path,
) -> None:
    _, plan = planned_repository
    payload = plan.to_payload()
    payload.pop("planIdentity")
    files = [dict(row) for row in payload["files"]]
    files[0]["path"] = "../escape.lean"
    payload["files"] = files
    unsafe = TheoremPlan.create(payload)

    with pytest.raises(CapsuleContentError, match="escapes"):
        materialize_theorem_capsule(unsafe, tmp_path / "capsule")


def test_materialization_rejects_symlinked_planned_input(
    planned_repository: tuple[Path, TheoremPlan],
    tmp_path: Path,
) -> None:
    root, plan = planned_repository
    source = root / "CapsuleFixture" / "Base.lean"
    replacement = root / "Base-copy.lean"
    replacement.write_bytes(source.read_bytes())
    source.unlink()
    source.symlink_to(replacement)

    with pytest.raises(CapsuleContentError, match="symbolic link"):
        materialize_theorem_capsule(plan, tmp_path / "capsule")


def test_materialization_rejects_casefold_path_collision(
    planned_repository: tuple[Path, TheoremPlan],
    tmp_path: Path,
) -> None:
    _, plan = planned_repository
    payload = plan.to_payload()
    payload.pop("planIdentity")
    files = [dict(row) for row in payload["files"]]
    files[1]["path"] = files[0]["path"].swapcase()
    payload["files"] = files
    colliding = TheoremPlan.create(payload)

    with pytest.raises(CapsuleContentError, match="collide"):
        materialize_theorem_capsule(colliding, tmp_path / "capsule")


def test_materialization_refuses_existing_destination(
    planned_repository: tuple[Path, TheoremPlan],
    tmp_path: Path,
) -> None:
    _, plan = planned_repository
    output = tmp_path / "capsule"
    output.mkdir()

    with pytest.raises(CapsuleInvocationError, match="already exists"):
        materialize_theorem_capsule(plan, output)


def test_materialization_cleans_interrupted_staging(
    planned_repository: tuple[Path, TheoremPlan],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, plan = planned_repository
    output = tmp_path / "capsule"
    before = tree_state(root)
    original = materialization._write_stage_file
    calls = 0

    def interrupted(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated interrupted copy")
        return original(*args, **kwargs)

    monkeypatch.setattr(materialization, "_write_stage_file", interrupted)

    with pytest.raises(OSError, match="interrupted"):
        materialize_theorem_capsule(plan, output)

    assert output.exists() is False
    assert list(tmp_path.glob(".capsule.staging-*")) == []
    assert tree_state(root) == before


def tree_state(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".lake" not in path.parts
    }
