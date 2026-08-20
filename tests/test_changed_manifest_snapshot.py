from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from ladon import pipeline_extraction
from ladon.pipeline import run_pipeline
from ladon.pipeline_models import RunContext


def write_project(root: Path) -> None:
    """Create one deterministic project with two selectable modules."""

    (root / "Pkg").mkdir()
    (root / "Pkg.lean").write_text(
        "import Pkg.Core\n",
        encoding="utf-8",
    )
    (root / "Pkg" / "Core.lean").write_text(
        "def core : Nat := 1\n",
        encoding="utf-8",
    )


def write_changed_manifest(path: Path, changed_path: str) -> bytes:
    """Write one deliberately non-canonical changed-set document."""

    content = (
        "{\n"
        '  "schema": "ladon-changed-set-v1",\n'
        f'  "paths": [{{"path": "{changed_path}"}}]\n'
        "}\n"
    ).encode()
    path.write_bytes(content)
    return content


def changed_run(
    repo: Path,
    manifest_path: Path,
    *,
    verification_hook=None,
):
    """Run one changed-set analysis with deterministic local settings."""

    return run_pipeline(
        RunContext(
            repo_root=repo,
            analysis_scope="changed-set",
            changed_manifest=manifest_path,
            source_cache_enabled=False,
            snapshot_verification_hook=verification_hook,
        )
    )


def mismatch_for(result, path: str) -> dict[str, Any]:
    """Return one expected final snapshot mismatch by registry path."""

    decision = result.context.snapshot_decision
    assert decision is not None
    return next(row for row in decision.mismatches if row["path"] == path)


def test_changed_manifest_bytes_are_registered_before_scope_consumption(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    manifest_path = repo / "changed.json"
    manifest_bytes = write_changed_manifest(manifest_path, "Pkg/Core.lean")

    result = changed_run(repo, manifest_path)

    snapshot = result.context.analysis_snapshot
    plan = result.context.scope_plan
    decision = result.context.snapshot_decision
    assert snapshot is not None
    assert plan is not None
    assert decision is not None
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    entry = snapshot.entries["changed.json"]
    assert (entry.kind, entry.sha256, entry.byte_count) == (
        "configuration",
        f"sha256:{digest}",
        len(manifest_bytes),
    )
    assert snapshot.configuration["changedManifest"] == {
        "status": "present",
        "path": "changed.json",
        "bytes": len(manifest_bytes),
        "sha256": f"sha256:{digest}",
    }
    assert (
        plan.primary_modules,
        plan.changed_authority["manifestSha256"],
        decision.status,
    ) == (("Pkg.Core",), digest, "stable")


def test_changed_manifest_phase_uses_capture_and_reports_preplan_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    manifest_path = repo / "changed.json"
    original = write_changed_manifest(manifest_path, "Pkg/Core.lean")
    changed = b'{"schema":"ladon-changed-set-v1","paths":["Pkg.lean"]}\n'
    resolve = pipeline_extraction.resolve_analysis_scope

    def mutate_before_scope_consumption(*args, **kwargs):
        manifest_path.write_bytes(changed)
        return resolve(*args, **kwargs)

    monkeypatch.setattr(
        pipeline_extraction,
        "resolve_analysis_scope",
        mutate_before_scope_consumption,
    )
    result = changed_run(repo, manifest_path)

    assert result.context.scope_plan is not None
    assert result.context.scope_plan.primary_modules == ("Pkg.Core",)
    mismatch = mismatch_for(result, "changed.json")
    assert (
        mismatch["expected"]["sha256"],
        mismatch["actual"]["sha256"],
    ) == (
        "sha256:" + hashlib.sha256(original).hexdigest(),
        "sha256:" + hashlib.sha256(changed).hexdigest(),
    )


def test_changed_manifest_verification_hook_detects_final_drift(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    manifest_path = repo / "changed.json"
    write_changed_manifest(manifest_path, "Pkg/Core.lean")
    changed = b'{"schema":"ladon-changed-set-v1","paths":["Pkg.lean"]}\n'

    def mutate_manifest(_context: RunContext) -> None:
        manifest_path.write_bytes(changed)

    result = changed_run(
        repo,
        manifest_path,
        verification_hook=mutate_manifest,
    )

    mismatch = mismatch_for(result, "changed.json")
    assert mismatch["actual"]["sha256"] == (
        "sha256:" + hashlib.sha256(changed).hexdigest()
    )
    assert mismatch["collectionRefs"] == [
        "declaration_graph.declarations",
        "module_dag.modules",
        "report.findings",
        "report.review_regions",
    ]
