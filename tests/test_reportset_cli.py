from __future__ import annotations

import json
from pathlib import Path

from ladon.cli import main
from ladon.pipeline import RunContext, run_pipeline

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


def write_report(path: Path) -> None:
    payload = run_pipeline(
        RunContext(repo_root=FIXTURE_ROOT, requested_root="Tiny.lean")
    ).to_report_payload()
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_installed_atlas_cards_and_workflow_delegate_to_libraries(
    tmp_path: Path,
) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    write_report(reports / "tiny.json")
    atlas = tmp_path / "atlas.json"
    cards = tmp_path / "cards.md"
    workflow = tmp_path / "workflow.json"

    assert main(
        [
            "atlas",
            "--reports-root",
            str(reports),
            "--output",
            str(atlas),
        ]
    ) == 0
    assert main(
        [
            "cards",
            "--atlas",
            str(atlas),
            "--format",
            "text",
            "--output",
            str(cards),
        ]
    ) == 0
    assert main(
        [
            "workflow",
            "--atlas",
            str(atlas),
            "--output",
            str(workflow),
        ]
    ) == 0

    atlas_payload = json.loads(atlas.read_text(encoding="utf-8"))
    assert atlas_payload["schema"] == "ladon-report-atlas-v1"
    assert atlas_payload["summary"]["inventory_modules"] == 3
    assert atlas_payload["summary"]["highlighted_modules"] <= 3
    assert "Ladon Atlas Reviewer Cards" in cards.read_text(encoding="utf-8")
    assert json.loads(workflow.read_text(encoding="utf-8"))["schema"] == (
        "ladon-atlas-workflow-v1"
    )


def test_reportset_json_stdout_is_one_document(
    tmp_path: Path,
    capsys,
) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    write_report(reports / "tiny.json")

    status = main(["atlas", "--reports-root", str(reports)])

    captured = capsys.readouterr()
    assert status == 0
    assert json.loads(captured.out)["schema"] == "ladon-report-atlas-v1"
    assert captured.err == ""


def test_reportset_unknown_input_version_is_operational(
    tmp_path: Path,
    capsys,
) -> None:
    atlas = tmp_path / "bad-atlas.json"
    atlas.write_text('{"schema":"ladon-report-atlas-v999"}', encoding="utf-8")

    status = main(
        [
            "cards",
            "--atlas",
            str(atlas),
            "--output",
            str(tmp_path / "cards.json"),
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert "supported schema" in captured.err
    assert not (tmp_path / "cards.json").exists()
