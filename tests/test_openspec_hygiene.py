from __future__ import annotations

from pathlib import Path

from ladon.analysis.openspec_hygiene import (
    normalize_completed_active_statuses,
    replace_metadata_status,
    summarize_openspec_hygiene,
)
from ladon.analysis.openspec_canonical import (
    CanonicalGateError,
    check_legacy_cli_profile,
)


def test_openspec_hygiene_flags_completed_active_drift(tmp_path: Path) -> None:
    write_change(tmp_path, "done-active", status="active", tasks=["- [x] implement", "- [X] test"])
    write_change(tmp_path, "partial-active", status="active", tasks=["- [x] implement", "- [ ] test"])

    summary = summarize_openspec_hygiene(tmp_path / "openspec")

    assert summary["change_count"] == 2
    assert summary["completed_active_drift_count"] == 1
    assert [row["id"] for row in summary["drifts"]] == ["done-active"]


def test_openspec_hygiene_reports_completed_metadata_with_open_tasks(tmp_path: Path) -> None:
    write_change(tmp_path, "bad-completed", status="completed", tasks=["- [ ] implement"])

    summary = summarize_openspec_hygiene(tmp_path / "openspec")

    assert summary["drifts"][0]["drift_kind"] == "open_tasks_marked_completed"


def test_openspec_hygiene_treats_missing_tasks_as_unknown_not_drift(tmp_path: Path) -> None:
    change = tmp_path / "openspec" / "changes" / "metadata-only"
    change.mkdir(parents=True)
    (change / ".openspec.yaml").write_text("id: metadata-only\nstatus: active\n", encoding="utf-8")

    summary = summarize_openspec_hygiene(tmp_path / "openspec")

    assert summary["changes"][0]["inferred_status"] == "unknown"
    assert summary["drift_count"] == 0


def test_normalize_completed_active_statuses_rewrites_only_safe_drift(tmp_path: Path) -> None:
    done = write_change(tmp_path, "done-active", status="active", tasks=["- [x] implement"])
    partial = write_change(tmp_path, "partial-active", status="active", tasks=["- [ ] implement"])

    changed = normalize_completed_active_statuses(tmp_path / "openspec")

    assert changed == ["done-active"]
    assert "status: completed\n" in done.joinpath(".openspec.yaml").read_text(encoding="utf-8")
    assert "status: active\n" in partial.joinpath(".openspec.yaml").read_text(encoding="utf-8")


def test_replace_metadata_status_preserves_surrounding_metadata(tmp_path: Path) -> None:
    metadata = tmp_path / ".openspec.yaml"
    metadata.write_text(
        "schema: spec-driven\nstatus: active\nlabels:\n  - ladon\n",
        encoding="utf-8",
    )

    replace_metadata_status(metadata, "completed")

    assert metadata.read_text(encoding="utf-8") == (
        "schema: spec-driven\nstatus: completed\nlabels:\n  - ladon\n"
    )


def test_canonical_gate_accepts_declared_active_delta_chain(tmp_path: Path) -> None:
    openspec_root = tmp_path / "openspec"
    write_archive_ledger(openspec_root)
    write_delta(
        openspec_root,
        "ladon-pipeline-phase-boundaries-timing",
        "ladon-pipeline",
        "ADDED",
        "Ladon SHALL separate pure analysis kernels from side effects",
    )
    write_delta(
        openspec_root,
        "ladon-clean-core-radon-gate",
        "ladon-python-quality",
        "ADDED",
        "Ladon's clean core SHALL preserve tested module-DAG reporting",
    )
    write_delta(
        openspec_root,
        "ladon-root-matrix-lean-expansion",
        "ladon-root-matrix",
        "ADDED",
        "Lean-Backed Owner Matrix Entries",
    )
    write_delta(
        openspec_root,
        "ladon-openspec-state-reconciliation",
        "ladon-python-quality",
        "MODIFIED",
        "Ladon's clean core SHALL preserve tested module-DAG reporting",
    )
    write_delta(
        openspec_root,
        "ladon-openspec-state-reconciliation",
        "ladon-root-matrix",
        "MODIFIED",
        "Lean-Backed Owner Matrix Entries",
    )

    state = check_legacy_cli_profile(openspec_root, allow_active_delta=True)

    assert state == "active-delta"


def test_canonical_gate_rejects_wrong_archive_order(tmp_path: Path) -> None:
    openspec_root = tmp_path / "openspec"
    write_archive_ledger(openspec_root, reverse=True)
    (openspec_root / "changes" / "ladon-openspec-state-reconciliation").mkdir(parents=True)

    try:
        check_legacy_cli_profile(openspec_root, allow_active_delta=True)
    except CanonicalGateError as exc:
        assert "archive chain must be" in str(exc)
    else:
        raise AssertionError("wrong archive order passed")


def test_canonical_gate_accepts_negative_removed_flag_scenario(tmp_path: Path) -> None:
    openspec_root = tmp_path / "openspec"
    archive = (
        openspec_root
        / "changes"
        / "archive"
        / "2026-07-25-ladon-openspec-state-reconciliation"
    )
    archive.mkdir(parents=True)
    write_canonical(
        openspec_root,
        "ladon-python-quality",
        "Ladon's clean core SHALL preserve tested module-DAG reporting",
        "- **WHEN** the smoke runs without `--build`",
    )
    write_canonical(
        openspec_root,
        "ladon-root-matrix",
        "Lean-Backed Owner Matrix Entries",
        "- **THEN** commands SHALL NOT include the removed\n"
        "  `--skip-build` option",
    )

    state = check_legacy_cli_profile(openspec_root, require_canonical=True)

    assert state == "canonical"


def test_canonical_gate_rejects_positive_removed_flag_scenario(tmp_path: Path) -> None:
    openspec_root = tmp_path / "openspec"
    archive = (
        openspec_root
        / "changes"
        / "archive"
        / "2026-07-25-ladon-openspec-state-reconciliation"
    )
    archive.mkdir(parents=True)
    write_canonical(
        openspec_root,
        "ladon-python-quality",
        "Ladon's clean core SHALL preserve tested module-DAG reporting",
        "- **WHEN** the smoke runs without `--build`",
    )
    write_canonical(
        openspec_root,
        "ladon-root-matrix",
        "Lean-Backed Owner Matrix Entries",
        "- **THEN** commands SHALL NOT include the removed `--skip-build` option\n"
        "- **AND** a legacy command includes `--skip-build`",
    )

    try:
        check_legacy_cli_profile(openspec_root, require_canonical=True)
    except CanonicalGateError as exc:
        assert "positively prescribe --skip-build" in str(exc)
    else:
        raise AssertionError("positive removed-flag prescription passed")


def write_archive_ledger(openspec_root: Path, *, reverse: bool = False) -> None:
    import json

    changes = [
        "ladon-pipeline-phase-boundaries-timing",
        "ladon-clean-core-radon-gate",
        "ladon-root-matrix-lean-expansion",
        "ladon-proof-xray-staging",
        "ladon-openspec-state-reconciliation",
    ]
    if reverse:
        changes.reverse()
    path = openspec_root / "reconciliation" / "legacy-state-ledger.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"archiveBatches": [{"change": change} for change in changes]}),
        encoding="utf-8",
    )


def write_delta(
    openspec_root: Path,
    change: str,
    capability: str,
    delta_kind: str,
    requirement: str,
) -> None:
    path = openspec_root / "changes" / change / "specs" / capability / "spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"## {delta_kind} Requirements\n\n"
        f"### Requirement: {requirement}\n"
        "The system SHALL preserve this contract.\n\n"
        "#### Scenario: Contract\n"
        "- **WHEN** the gate runs\n"
        "- **THEN** the contract holds\n",
        encoding="utf-8",
    )


def write_canonical(
    openspec_root: Path,
    capability: str,
    requirement: str,
    scenario_line: str,
) -> None:
    path = openspec_root / "specs" / capability / "spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"# {capability} Specification\n\n"
        f"### Requirement: {requirement}\n"
        "The system SHALL preserve this contract.\n\n"
        "#### Scenario: Contract\n"
        f"{scenario_line}\n",
        encoding="utf-8",
    )


def write_change(tmp_path: Path, change_id: str, *, status: str, tasks: list[str]) -> Path:
    change = tmp_path / "openspec" / "changes" / change_id
    change.mkdir(parents=True)
    (change / ".openspec.yaml").write_text(
        f"schema: spec-driven\nid: {change_id}\nstatus: {status}\n",
        encoding="utf-8",
    )
    (change / "tasks.md").write_text("# Tasks\n\n" + "\n".join(tasks) + "\n", encoding="utf-8")
    return change
