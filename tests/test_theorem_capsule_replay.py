from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ladon.theorem_capsule_materialization import materialize_theorem_capsule
from ladon.theorem_capsule_models import CapsuleManifest, sha256_bytes
from ladon.theorem_capsule_planning import plan_theorem_capsule
from ladon.theorem_capsule_replay import replay_theorem_capsule
from ladon.theorem_capsule_replay import _sanitize_output
from ladon.theorem_cli import theorem_main


FIXTURE = Path(__file__).parent / "fixtures" / "theorem_capsule"
MULTI_ROOT_FIXTURE = (
    Path(__file__).parent / "fixtures" / "theorem_capsule_multi_root"
)


@pytest.fixture
def capsule_fixture(tmp_path: Path) -> tuple[Path, Path]:
    repository = tmp_path / "repository"
    shutil.copytree(FIXTURE, repository)
    build = subprocess.run(
        ["lake", "build"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if build.returncode != 0:
        pytest.fail(build.stderr or build.stdout)
    plan = plan_theorem_capsule(repository, "CapsuleFixture.chosen")
    capsule = tmp_path / "capsule"
    materialize_theorem_capsule(plan, capsule)
    return repository, capsule


def test_replay_verifies_after_original_checkout_is_renamed(
    capsule_fixture: tuple[Path, Path],
) -> None:
    repository, capsule = capsule_fixture
    renamed = repository.with_name("repository-unavailable")
    repository.rename(renamed)

    receipt = replay_theorem_capsule(capsule)
    repeated = replay_theorem_capsule(capsule)

    assert receipt["status"] == "verified"
    assert repeated["receiptIdentity"] == receipt["receiptIdentity"]
    assert receipt["isolation"]["passed"] is True
    assert all(receipt["comparisons"]["checks"].values())
    assert receipt["nonclaims"]
    assert ".lake" not in {path.name for path in capsule.iterdir()}


def test_replay_rejects_mutated_content_before_lean(
    capsule_fixture: tuple[Path, Path],
) -> None:
    _, capsule = capsule_fixture
    target = capsule / "CapsuleFixture.lean"
    target.write_text(target.read_text() + "\n-- mutation\n", encoding="utf-8")

    receipt = replay_theorem_capsule(capsule)

    assert receipt["status"] == "content-invalid"
    assert receipt["stages"][0]["stage"] == "content_validation"


def test_replay_rejects_undeclared_file(
    capsule_fixture: tuple[Path, Path],
) -> None:
    _, capsule = capsule_fixture
    (capsule / "Ghost.lean").write_text("theorem ghost : True := by trivial\n")

    receipt = replay_theorem_capsule(capsule)

    assert receipt["status"] == "content-invalid"
    assert "extra" in receipt["stages"][0]["diagnostic"]


def test_replay_rejects_undeclared_symlink_before_lean(
    capsule_fixture: tuple[Path, Path],
) -> None:
    _, capsule = capsule_fixture
    (capsule / "linked-input").symlink_to(capsule / "lean-toolchain")

    receipt = replay_theorem_capsule(capsule)

    assert receipt["status"] == "content-invalid"
    assert "unsupported filesystem entry" in receipt["stages"][0]["diagnostic"]


def test_replay_rejects_resigned_toolchain_drift_against_plan(
    capsule_fixture: tuple[Path, Path],
) -> None:
    _, capsule = capsule_fixture
    toolchain = capsule / "lean-toolchain"
    manifest_path = capsule / "capsule.json"
    toolchain.write_text("leanprover/lean4:v0.0.0\n", encoding="utf-8")
    manifest_payload = json.loads(manifest_path.read_text())
    manifest_payload.pop("capsuleIdentity")
    files = [dict(row) for row in manifest_payload["files"]]
    row = next(item for item in files if item["path"] == "lean-toolchain")
    row["sha256"] = sha256_bytes(toolchain.read_bytes())
    row["bytes"] = len(toolchain.read_bytes())
    manifest_payload["files"] = files
    manifest_path.write_bytes(CapsuleManifest.create(manifest_payload).to_bytes())

    receipt = replay_theorem_capsule(capsule)

    assert receipt["status"] == "content-invalid"
    assert "source plan" in receipt["stages"][0]["diagnostic"]


def test_replay_detects_structural_identity_change(
    capsule_fixture: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, capsule = capsule_fixture

    def changed_helper(plan, *_args, **_kwargs):
        nodes = [
            dict(row)
            for row in plan.payload["semanticGraph"]["nodes"]
        ]
        target = next(row for row in nodes if row["name"] == plan.target["name"])
        target["typeFingerprint"] = "changed-structural-fingerprint"
        return {
            "status": None,
            "row": {"stage": "theorem_query", "returncode": 0},
            "payload": {
                "target": plan.target["name"],
                "leanVersion": plan.payload["toolchain"]["leanVersion"],
                "nodes": nodes,
            },
        }

    monkeypatch.setattr(
        "ladon.theorem_capsule_replay._run_replay_helper",
        changed_helper,
    )

    receipt = replay_theorem_capsule(capsule)

    assert receipt["status"] == "identity-mismatch"
    assert receipt["comparisons"]["checks"]["typeFingerprint"] is False


def test_replay_classifies_process_timeout_as_resource_limit(
    capsule_fixture: tuple[Path, Path],
) -> None:
    _, capsule = capsule_fixture

    receipt = replay_theorem_capsule(capsule, timeout_seconds=0.0001)

    assert receipt["status"] == "resource-limit"
    assert receipt["stages"][0]["timedOut"] is True


def test_replay_output_redacts_secret_forms(tmp_path: Path) -> None:
    sanitized = _sanitize_output(
        "TOKEN=abc Authorization: Bearer xyz "
        "https://person:password@example.invalid/repository",
        tmp_path,
    )

    assert "abc" not in sanitized
    assert "xyz" not in sanitized
    assert "person" not in sanitized
    assert "password" not in sanitized
    assert sanitized.count("<redacted>") == 3


def test_replay_supported_tar_archive(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    shutil.copytree(FIXTURE, repository)
    subprocess.run(["lake", "build"], cwd=repository, check=True, capture_output=True)
    plan = plan_theorem_capsule(repository, "CapsuleFixture.chosen")
    archive = tmp_path / "capsule.tar"
    materialize_theorem_capsule(plan, archive)
    repository.rename(tmp_path / "repository-unavailable")

    receipt = replay_theorem_capsule(archive)

    assert receipt["status"] == "verified"


def test_replay_verifies_multiple_source_roots_without_checkout(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    shutil.copytree(MULTI_ROOT_FIXTURE, repository)
    subprocess.run(["lake", "build"], cwd=repository, check=True, capture_output=True)
    plan = plan_theorem_capsule(repository, "Main.selected")
    capsule = tmp_path / "capsule"
    materialize_theorem_capsule(plan, capsule)
    repository.rename(tmp_path / "repository-unavailable")

    receipt = replay_theorem_capsule(capsule)

    assert receipt["status"] == "verified"


def test_extract_cli_composes_the_same_services(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = tmp_path / "repository"
    shutil.copytree(FIXTURE, repository)
    subprocess.run(["lake", "build"], cwd=repository, check=True, capture_output=True)
    capsule = tmp_path / "capsule"

    status = theorem_main(
        [
            "extract",
            "CapsuleFixture.chosen",
            "--repo-root",
            str(repository),
            "--output",
            str(capsule),
            "--verify",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert status == 0
    assert captured.err == ""
    assert payload["status"] == "verified"
    assert payload["receiptIdentity"].startswith("sha256:")
