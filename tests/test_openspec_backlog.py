from __future__ import annotations

from pathlib import Path

from ladon.analysis.openspec_backlog import summarize_openspec_backlog


def test_openspec_backlog_reports_missing_automation(tmp_path: Path) -> None:
    write_change(tmp_path, "missing-auto", status="active", tasks=["- [ ] implement"])

    summary = summarize_openspec_backlog(tmp_path / "openspec")

    assert summary["findings"] == [
        {
            "kind": "missing_automation",
            "change_id": "missing-auto",
            "detail": "missing automation.json",
        }
    ]


def test_openspec_backlog_reports_missing_validation_command(tmp_path: Path) -> None:
    change = write_change(tmp_path, "no-validation", status="active", tasks=["- [ ] implement"])
    (change / "automation.json").write_text('{"commands": ["uv run pytest -q"]}\n', encoding="utf-8")

    summary = summarize_openspec_backlog(tmp_path / "openspec")

    assert summary["findings"][0]["kind"] == "missing_validation_command"


def test_openspec_backlog_reads_phased_automation_commands(tmp_path: Path) -> None:
    change = write_change(tmp_path, "phased", status="active", tasks=["- [ ] implement"])
    (change / "automation.json").write_text(
        '{"phases": {"verify": ["openspec validate phased --strict"]}}\n',
        encoding="utf-8",
    )

    summary = summarize_openspec_backlog(tmp_path / "openspec")

    assert summary["findings"] == []
    assert summary["packets"][0]["automation_command_count"] == 1
    assert summary["packets"][0]["has_validation_command"] is True


def test_openspec_backlog_reports_stale_child_reference(tmp_path: Path) -> None:
    parent = write_change(tmp_path, "parent", status="active", tasks=["- [ ] child"])
    (parent / "automation.json").write_text(
        '{"commands": ["openspec validate parent --strict"]}\n',
        encoding="utf-8",
    )
    (parent / "children").mkdir()
    (parent / "children" / "missing-child.md").write_text("# child\n", encoding="utf-8")

    summary = summarize_openspec_backlog(tmp_path / "openspec")

    assert summary["findings"] == [
        {"kind": "stale_child_reference", "change_id": "parent", "detail": "missing-child"}
    ]


def test_openspec_backlog_reuses_status_drift_signal(tmp_path: Path) -> None:
    change = write_change(tmp_path, "done-active", status="active", tasks=["- [x] implement"])
    (change / "automation.json").write_text(
        '{"commands": ["openspec validate done-active --strict"]}\n',
        encoding="utf-8",
    )

    summary = summarize_openspec_backlog(tmp_path / "openspec")

    assert summary["findings"][0]["kind"] == "openspec_status_drift"


def write_change(tmp_path: Path, change_id: str, *, status: str, tasks: list[str]) -> Path:
    change = tmp_path / "openspec" / "changes" / change_id
    change.mkdir(parents=True)
    (change / ".openspec.yaml").write_text(
        f"schema: spec-driven\nid: {change_id}\nstatus: {status}\n",
        encoding="utf-8",
    )
    (change / "tasks.md").write_text("# Tasks\n\n" + "\n".join(tasks) + "\n", encoding="utf-8")
    return change
