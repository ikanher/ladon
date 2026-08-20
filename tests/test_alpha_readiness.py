from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_ROOT = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

import alpha_readiness as readiness_cli
import alpha_readiness_run as readiness_run
from alpha_readiness_plan import (
    ChildPacket,
    build_readiness_plan,
    milestone_from_row,
    milestone_task_ids,
    milestone_tasks_complete,
)
from alpha_readiness_run import (
    REPORT_AUTHORITY_VOCABULARY,
    ReadinessFailure,
    child_blockers,
    execute_readiness_plan,
    is_stale_active_validation,
    normalized_command,
    require_authority_ledger,
)
from release_gate_types import GateError

AUTHORITY_CLASSES = [
    {
        "id": "lexical_text",
        "owner": "signal",
        "reportValues": [
            "lexical_text",
            "module_import_graph",
            "source_declaration_inventory",
            "ladon_derived_heuristic",
        ],
    },
    {
        "id": "parser_candidate",
        "owner": "runtime",
        "reportValues": ["lean_parser", "parser_observed"],
    },
    {
        "id": "lean_elaborated",
        "owner": "declarations",
        "reportValues": [
            "lean_environment",
            "lean_elaborated",
            "lean-environment-direct",
        ],
    },
    {
        "id": "quoted_external",
        "owner": "report",
        "reportValues": ["external_tool_quoted", "unknown"],
    },
    {
        "id": "ladon_report_metadata",
        "owner": "report",
        "reportValues": ["capability-owner", "ladon-analysis"],
    },
]


def test_plan_resolves_one_active_and_one_unique_archive(tmp_path: Path) -> None:
    write_packet(tmp_path / "openspec" / "changes" / "active", checked=True)
    write_packet(
        tmp_path
        / "openspec"
        / "changes"
        / "archive"
        / "2026-07-25-archived",
        checked=True,
    )
    ledger = ledger_fixture([child("active"), child("archived")])

    plan = build_readiness_plan(tmp_path, ledger)

    assert plan.packets["active"].state == "active"
    assert plan.packets["archived"].state == "archived"
    assert plan.packets["active"].complete is True
    assert plan.child_order == ("active", "archived")


def test_plan_rejects_ambiguous_active_and_archived_child(tmp_path: Path) -> None:
    write_packet(tmp_path / "openspec" / "changes" / "same", checked=True)
    write_packet(
        tmp_path
        / "openspec"
        / "changes"
        / "archive"
        / "2026-07-25-same",
        checked=True,
    )

    with pytest.raises(GateError, match="resolves ambiguously"):
        build_readiness_plan(tmp_path, ledger_fixture([child("same")]))


def test_expanded_graph_orders_post_archive_and_preclose_milestones(
    tmp_path: Path,
) -> None:
    for change in ("reconcile", "cli", "clean", "report"):
        write_packet(tmp_path / "openspec" / "changes" / change, checked=True)
    rows = [
        child(
            "reconcile",
            milestones=[
                milestone("canonical", "post-archive", "archive handoff")
            ],
        ),
        child("cli", start_after=["reconcile#canonical"]),
        child(
            "clean",
            close_after=["report"],
            milestones=[
                milestone("baseline", "pre-close", "task 1.1")
            ],
        ),
        child("report", integration=["clean#baseline"]),
    ]

    plan = build_readiness_plan(tmp_path, ledger_fixture(rows))
    positions = {event: index for index, event in enumerate(plan.event_order)}

    assert positions["reconcile@close"] < positions["reconcile#canonical"]
    assert positions["reconcile#canonical"] < positions["cli@start"]
    assert positions["clean#baseline"] < positions["report@close"]
    assert positions["report@close"] < positions["clean@close"]


def test_expanded_graph_rejects_unresolvable_close_cycle(tmp_path: Path) -> None:
    for change in ("left", "right"):
        write_packet(tmp_path / "openspec" / "changes" / change, checked=True)
    rows = [
        child("left", close_after=["right"]),
        child("right", close_after=["left"]),
    ]

    with pytest.raises(GateError, match="unresolvable cycle"):
        build_readiness_plan(tmp_path, ledger_fixture(rows))


def test_preclose_milestone_reads_its_declared_task_state(
    tmp_path: Path,
) -> None:
    packet_path = tmp_path / "openspec" / "changes" / "clean"
    write_packet(packet_path, checked=False)
    ledger = ledger_fixture(
        [
            child(
                "clean",
                milestones=[
                    milestone("baseline", "pre-close", "task 1.1")
                ],
            )
        ]
    )
    plan = build_readiness_plan(tmp_path, ledger)

    assert milestone_tasks_complete(
        plan.packets["clean"],
        plan.milestones["clean#baseline"],
    ) is False
    assert child_blockers(plan) == {"clean": ["unchecked task 1.1"]}


def test_command_normalization_binds_worktree_without_a_shell() -> None:
    root = Path("/candidate/root")

    assert normalized_command(
        "uv run tool --candidate worktree --required",
        root,
    ) == ["uv", "run", "tool", "--candidate", str(root), "--required"]
    assert is_stale_active_validation(
        "openspec validate archived --strict",
        "archived",
    )
    with pytest.raises(GateError, match="unsupported shell syntax"):
        normalized_command("uv run first && uv run second", root)


def test_authority_ledger_requires_classes_owners_and_real_values() -> None:
    ledger = authority_ledger()
    require_authority_ledger(ledger)
    values = {
        value
        for row in ledger["authorityClasses"]
        for value in row["reportValues"]
    }
    assert values == REPORT_AUTHORITY_VOCABULARY

    with pytest.raises(GateError, match="omits authority classes"):
        require_authority_ledger(
            {**ledger, "authorityClasses": AUTHORITY_CLASSES[:-1]}
        )

    unknown_class = [
        *AUTHORITY_CLASSES,
        {**AUTHORITY_CLASSES[0], "id": "not-a-real-class"},
    ]
    with pytest.raises(GateError, match="unknown authority classes"):
        require_authority_ledger({**ledger, "authorityClasses": unknown_class})

    unknown_owner = [dict(row) for row in AUTHORITY_CLASSES]
    unknown_owner[0]["owner"] = "missing"
    with pytest.raises(GateError, match="unknown owner"):
        require_authority_ledger({**ledger, "authorityClasses": unknown_owner})

    unknown_value = [dict(row) for row in AUTHORITY_CLASSES]
    unknown_value[0]["reportValues"] = [
        *unknown_value[0]["reportValues"],
        "not-a-real-authority",
    ]
    with pytest.raises(GateError, match="unknown report authority"):
        require_authority_ledger({**ledger, "authorityClasses": unknown_value})


def test_project_dependency_ledger_uses_the_validated_authority_vocabulary() -> None:
    path = (
        Path(__file__).parents[1]
        / "openspec"
        / "changes"
        / "ladon-alpha-hardening-umbrella"
        / "children"
        / "dependency-ledger.json"
    )

    require_authority_ledger(json.loads(path.read_text(encoding="utf-8")))


def test_active_packet_is_strictly_validated_independently_of_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet_path = tmp_path / "openspec" / "changes" / "active"
    write_packet(packet_path, checked=True)
    plan = build_readiness_plan(
        tmp_path,
        ledger_fixture([child("active")], authority_owner="active"),
    )
    observed: list[list[str]] = []

    def fake_run(command, *, cwd, environment) -> None:
        observed.append(list(command))
        assert cwd == tmp_path
        assert environment == {"CI": "1"}

    monkeypatch.setattr(readiness_run, "run_checked", fake_run)

    summary = execute_readiness_plan(
        plan,
        candidate_root=tmp_path,
        environment={"CI": "1"},
        require_all_children=True,
    )

    assert observed[0] == [
        "openspec",
        "validate",
        "active",
        "--type",
        "change",
        "--strict",
    ]
    assert observed[1] == ["python", "--version"]
    assert summary["ready"] is True


def test_failed_command_names_owner_in_machine_readable_blockers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet_path = tmp_path / "openspec" / "changes" / "active"
    write_packet(packet_path, checked=True)
    plan = build_readiness_plan(
        tmp_path,
        ledger_fixture([child("active")], authority_owner="active"),
    )

    def fake_run(command, *, cwd, environment) -> None:
        if list(command) == ["python", "--version"]:
            raise GateError("synthetic command failure")

    monkeypatch.setattr(readiness_run, "run_checked", fake_run)

    with pytest.raises(ReadinessFailure, match="child active gate failed") as raised:
        execute_readiness_plan(
            plan,
            candidate_root=tmp_path,
            environment={"CI": "1"},
            require_all_children=True,
        )

    summary = raised.value.summary
    active = next(row for row in summary["children"] if row["change"] == "active")
    assert active["blockers"] == [
        "required gate failed: synthetic command failure"
    ]
    assert summary["ready"] is False
    assert summary["commands"][-1] == {
        "owner": "active",
        "command": "python --version",
        "status": "failed",
        "error": "synthetic command failure",
    }


def test_cli_renders_readiness_failure_summary_as_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    summary = {"artifactKind": "ladon_alpha_readiness", "ready": False}

    def fail_readiness(**_kwargs) -> dict:
        raise ReadinessFailure("child active gate failed", summary)

    monkeypatch.setattr(readiness_cli, "run_readiness", fail_readiness)

    result = readiness_cli.main(
        [
            "--candidate",
            "worktree",
            "--ledger",
            "ledger.json",
            "--require-all-children",
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert json.loads(captured.out) == summary
    assert "child active gate failed" in captured.err


def test_milestone_task_ranges_expand_within_one_section() -> None:
    plan_row = milestone("release", "pre-close", "tasks 5.5-5.7")
    ledger = ledger_fixture(
        [child("clean", milestones=[plan_row])]
    )
    owner = str(ledger["children"][0]["change"])

    assert milestone_task_ids(milestone_from_row(owner, plan_row)) == (
        "5.5",
        "5.6",
        "5.7",
    )


def test_archived_validation_uses_an_isolated_typed_change_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    archive = tmp_path / "candidate" / "openspec" / "changes" / "archive"
    packet_path = archive / "2026-07-25-done"
    write_packet(packet_path, checked=True)
    candidate = tmp_path / "candidate"
    canonical = candidate / "openspec" / "specs" / "done"
    canonical.mkdir(parents=True)
    canonical.joinpath("spec.md").write_text("## Requirements\n", encoding="utf-8")
    packet = ChildPacket(
        change="done",
        path=packet_path,
        state="archived",
        automation=("openspec validate done --strict",),
        incomplete_tasks=(),
    )
    observed: list[str] = []

    def fake_run(command, *, cwd, environment) -> None:
        observed.extend(command)
        assert cwd.joinpath("openspec/changes/done/tasks.md").is_file()
        assert cwd.joinpath("openspec/specs/done/spec.md").is_file()
        assert environment == {"CI": "1"}

    monkeypatch.setattr(readiness_run, "run_checked", fake_run)

    readiness_run.validate_archived_packet(
        packet,
        candidate,
        {"CI": "1"},
    )

    assert observed == [
        "openspec",
        "validate",
        "done",
        "--type",
        "change",
        "--strict",
    ]


def child(
    change: str,
    *,
    start_after: list[str] | None = None,
    integration: list[str] | None = None,
    close_after: list[str] | None = None,
    milestones: list[dict] | None = None,
) -> dict:
    """Return one compact child ledger row."""

    return {
        "change": change,
        "startAfter": start_after or [],
        "integrationDependsOn": integration or [],
        "closeAfter": close_after or [],
        "milestones": milestones or [],
    }


def milestone(name: str, phase: str, defined_by: str) -> dict:
    """Return one compact milestone ledger row."""

    return {
        "name": name,
        "phase": phase,
        "definedBy": defined_by,
        "gates": [],
    }


def ledger_fixture(
    children: list[dict],
    *,
    authority_owner: str | None = None,
) -> dict:
    """Return a minimal valid dependency ledger."""

    classes = AUTHORITY_CLASSES
    if authority_owner is not None:
        classes = [
            {**row, "owner": authority_owner}
            for row in AUTHORITY_CLASSES
        ]
    return {
        "program": "test",
        "authorityClasses": classes,
        "children": children,
    }


def authority_ledger() -> dict:
    """Return the complete report-authority ownership fixture."""

    return {
        "program": "test",
        "authorityClasses": AUTHORITY_CLASSES,
        "children": [
            child("signal"),
            child("runtime"),
            child("declarations"),
            child("report"),
        ],
    }


def write_packet(path: Path, *, checked: bool) -> None:
    """Write one minimal active/archive packet for planning tests."""

    path.mkdir(parents=True)
    state = "x" if checked else " "
    (path / "tasks.md").write_text(
        f"- [{state}] 1.1 Complete the packet.\n",
        encoding="utf-8",
    )
    (path / "automation.json").write_text(
        json.dumps({"commands": ["python --version"]}),
        encoding="utf-8",
    )
