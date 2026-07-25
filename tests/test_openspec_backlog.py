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


def test_openspec_backlog_accepts_archived_child_reference(tmp_path: Path) -> None:
    parent = write_change(tmp_path, "parent", status="active", tasks=["- [ ] child"])
    (parent / "automation.json").write_text(
        '{"commands": ["openspec validate parent --strict"]}\n',
        encoding="utf-8",
    )
    (parent / "children").mkdir()
    (parent / "children" / "archived-child.md").write_text("# child\n", encoding="utf-8")
    archived = (
        tmp_path
        / "openspec"
        / "changes"
        / "archive"
        / "2026-07-25-archived-child"
    )
    archived.mkdir(parents=True)
    (archived / ".openspec.yaml").write_text(
        "schema: spec-driven\ncreated: 2026-07-25\n",
        encoding="utf-8",
    )

    summary = summarize_openspec_backlog(tmp_path / "openspec")

    assert summary["findings"] == []


def test_openspec_backlog_reuses_status_drift_signal(tmp_path: Path) -> None:
    change = write_change(tmp_path, "done-active", status="active", tasks=["- [x] implement"])
    (change / "automation.json").write_text(
        '{"commands": ["openspec validate done-active --strict"]}\n',
        encoding="utf-8",
    )

    summary = summarize_openspec_backlog(tmp_path / "openspec")

    assert summary["findings"][0]["kind"] == "openspec_status_drift"


def test_openspec_backlog_reports_completed_packet_without_delta(tmp_path: Path) -> None:
    change = write_change(tmp_path, "invalid-complete", status="completed", tasks=["- [x] implement"])
    (change / "automation.json").write_text(
        '{"commands": ["openspec validate invalid-complete --strict"]}\n',
        encoding="utf-8",
    )

    summary = summarize_openspec_backlog(tmp_path / "openspec")

    assert summary["findings"] == [
        {
            "kind": "invalid_completed_packet",
            "change_id": "invalid-complete",
            "detail": "completed packet has no OpenSpec delta requirements",
        }
    ]


def test_reconciliation_ledger_rejects_uncovered_completion(tmp_path: Path) -> None:
    change = write_change(tmp_path, "shipped", status="active", tasks=["- [ ] stale task"])
    write_delta(change, "Shipped capability")
    (change / "automation.json").write_text(
        '{"commands": ["openspec validate shipped --strict"]}\n',
        encoding="utf-8",
    )
    write_ledger(
        tmp_path,
        [
            {
                "id": "shipped",
                "disposition": "complete",
                "residualOwner": None,
                "requirementEvidence": [
                    {
                        "requirement": "Shipped capability",
                        "outcome": "blocked",
                        "source": [],
                        "tests": [],
                        "gates": [],
                    }
                ],
            }
        ],
    )

    summary = summarize_openspec_backlog(tmp_path / "openspec")
    kinds = {row["kind"] for row in summary["findings"]}

    assert "uncovered_completion" in kinds
    assert "verified_shipped_unchecked_tasks" in kinds


def test_reconciliation_ledger_rejects_unowned_transfer(tmp_path: Path) -> None:
    write_ledger(
        tmp_path,
        [
            {
                "id": "superseded",
                "disposition": "superseded-with-residuals",
                "residualOwner": None,
                "requirementEvidence": [
                    {
                        "requirement": "Residual capability",
                        "outcome": "transferred",
                        "source": ["source.py"],
                        "tests": ["test_source.py"],
                        "gates": ["pytest"],
                    }
                ],
            }
        ],
    )

    summary = summarize_openspec_backlog(tmp_path / "openspec")

    assert any(row["kind"] == "unowned_requirement" for row in summary["findings"])


def write_delta(change: Path, requirement: str) -> None:
    spec = change / "specs" / "capability" / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "## ADDED Requirements\n\n"
        f"### Requirement: {requirement}\n"
        "The system SHALL preserve the capability.\n\n"
        "#### Scenario: Capability is present\n"
        "- **WHEN** the gate runs\n"
        "- **THEN** the capability is present\n",
        encoding="utf-8",
    )


def write_ledger(tmp_path: Path, packets: list[dict]) -> None:
    dependency = (
        tmp_path
        / "openspec"
        / "changes"
        / "ladon-alpha-hardening-umbrella"
        / "children"
        / "dependency-ledger.json"
    )
    dependency.parent.mkdir(parents=True)
    dependency.write_text("{}\n", encoding="utf-8")
    ledger = tmp_path / "openspec" / "reconciliation" / "legacy-state-ledger.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        __import__("json").dumps(
            {
                "schemaVersion": 1,
                "dependencyLedgerRef": (
                    "openspec/changes/ladon-alpha-hardening-umbrella/"
                    "children/dependency-ledger.json"
                ),
                "baseline": {},
                "packets": packets,
                "archiveBatches": [],
                "selfArchiveHandoff": {},
            }
        ),
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
