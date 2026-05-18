from __future__ import annotations

from pathlib import Path

from ladon.analysis.openspec_hygiene import (
    normalize_completed_active_statuses,
    replace_metadata_status,
    summarize_openspec_hygiene,
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


def write_change(tmp_path: Path, change_id: str, *, status: str, tasks: list[str]) -> Path:
    change = tmp_path / "openspec" / "changes" / change_id
    change.mkdir(parents=True)
    (change / ".openspec.yaml").write_text(
        f"schema: spec-driven\nid: {change_id}\nstatus: {status}\n",
        encoding="utf-8",
    )
    (change / "tasks.md").write_text("# Tasks\n\n" + "\n".join(tasks) + "\n", encoding="utf-8")
    return change
