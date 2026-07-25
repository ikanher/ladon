from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ladon.cli import main


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "runsets"
MANIFEST_PATH = FIXTURE_ROOT / "manifest-v1.json"


def create_bundle(tmp_path: Path, capsys) -> Path:
    """Create a real portable bundle through the installed command path."""

    bundle_dir = tmp_path / "source"
    status = main(
        [
            "runset",
            "--manifest",
            str(MANIFEST_PATH),
            "--bundle-dir",
            str(bundle_dir),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--no-resume",
            "--progress",
            "off",
            "--output",
            str(tmp_path / "selected.json"),
        ]
    )
    captured = capsys.readouterr()
    assert status == 0
    assert captured.out == ""
    assert captured.err == ""
    return bundle_dir


def load_bundle(bundle_dir: Path) -> dict[str, Any]:
    return json.loads(
        (bundle_dir / "bundle.json").read_text(encoding="utf-8")
    )


def write_bundle(bundle_dir: Path, payload: dict[str, Any]) -> None:
    (bundle_dir / "bundle.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def invoke_atlas(bundle_dir: Path, capsys) -> tuple[int, str, str]:
    status = main(
        [
            "atlas",
            "--bundle",
            str(bundle_dir / "bundle.json"),
        ]
    )
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def write_unreported_entry_states(bundle_dir: Path) -> None:
    """Replace reports with four valid terminal workflow-only entries."""

    payload = load_bundle(bundle_dir)
    templates = payload["entries"]
    specifications = (
        ("failed", "runner failed before report publication"),
        ("skipped", "dependency did not provide a usable report"),
        ("interrupted", "target process interrupted by signal 15"),
        ("interrupted", "cancelled_before_entry_start"),
    )
    entries = []
    for index, (status, reason) in enumerate(specifications):
        entry = deepcopy(templates[min(index, len(templates) - 1)])
        report = entry.get("report")
        if isinstance(report, dict):
            (bundle_dir / report["path"]).unlink(missing_ok=True)
        if index >= len(templates):
            entry["id"] = "cancelled"
            entry["runIdentity"] = f"run:cancelled:{'d' * 24}"
            entry["entryFingerprint"] = f"sha256:{'d' * 64}"
        entry["diagnostics"] = [
            {
                "id": f"runset.entry_{status}",
                "message": reason,
                "severity": "warning" if status == "skipped" else "error",
            }
        ]
        entry["phaseSummary"] = {}
        entry["report"] = None
        entry["resourceCounters"] = {}
        entry["status"] = status
        entries.append(entry)
    payload["completeness"] = "interrupted"
    payload["entries"] = entries
    write_bundle(bundle_dir, payload)


def assert_unreported_atlas_contract(
    atlas: dict[str, Any],
) -> list[dict[str, Any]]:
    """Check quoted workflow state without treating it as report evidence."""

    diagnostics = atlas["workflowDiagnostics"]
    assert atlas["summary"].get("reports", 0) == 0
    assert atlas["summary"]["workflow_diagnostics"] == 4
    assert {row["state"] for row in diagnostics} == {
        "cancelled",
        "failed",
        "interrupted",
        "skipped",
    }
    for row in diagnostics:
        assert row["reportPresent"] is False
        assert row["authority"] == "ladon_analysis_bundle"
        assert "no canonical analysis report" in row["nonclaim"]
    assert atlas["nodes"] == []
    return diagnostics


def assert_workflow_routes_bundle_diagnostics(
    workflow: dict[str, Any],
    diagnostics: list[dict[str, Any]],
) -> None:
    """Check the reviewer workflow retains every unreported entry."""

    assert workflow["inputs"]["workflowDiagnosticCount"] == 4
    assert workflow["sections"]["workflowDiagnostics"] == diagnostics
    evidence = workflow["sections"]["incompleteOrStaleEvidence"]
    routed = {
        row["subject"]
        for row in evidence
        if row["kind"] == "runset_entry_state"
    }
    assert routed == {row["entryId"] for row in diagnostics}


def test_atlas_bundle_is_portable_and_ignores_unreferenced_json(
    tmp_path: Path,
    capsys,
) -> None:
    source = create_bundle(tmp_path, capsys)
    moved = tmp_path / "moved"
    shutil.copytree(source, moved)
    (moved / "reports" / "stale.json").write_text(
        "this is deliberately not a report",
        encoding="utf-8",
    )

    status, stdout, stderr = invoke_atlas(moved, capsys)

    assert status == 0
    assert stderr == ""
    atlas = json.loads(stdout)
    assert atlas["schema"] == "ladon-report-atlas-v1"
    assert atlas["summary"]["reports"] == 3


def test_atlas_bundle_preserves_entries_without_reports_as_workflow_state(
    tmp_path: Path,
    capsys,
) -> None:
    bundle_dir = create_bundle(tmp_path, capsys)
    write_unreported_entry_states(bundle_dir)

    status, stdout, stderr = invoke_atlas(bundle_dir, capsys)

    assert status == 0
    assert stderr == ""
    atlas = json.loads(stdout)
    diagnostics = assert_unreported_atlas_contract(atlas)

    atlas_path = tmp_path / "atlas.json"
    atlas_path.write_text(stdout, encoding="utf-8")
    workflow_status = main(
        [
            "workflow",
            "--atlas",
            str(atlas_path),
        ]
    )
    workflow_output = capsys.readouterr()

    assert workflow_status == 0
    assert workflow_output.err == ""
    workflow = json.loads(workflow_output.out)
    assert_workflow_routes_bundle_diagnostics(workflow, diagnostics)


def test_atlas_bundle_rejects_report_hash_mismatch(
    tmp_path: Path,
    capsys,
) -> None:
    bundle_dir = create_bundle(tmp_path, capsys)
    payload = load_bundle(bundle_dir)
    report = bundle_dir / payload["entries"][0]["report"]["path"]
    content = report.read_bytes()
    assert content.endswith(b"\n")
    report.write_bytes(content[:-1] + b" ")

    status, stdout, stderr = invoke_atlas(bundle_dir, capsys)

    assert status == 1
    assert stdout == ""
    assert "report content hash does not match" in stderr


def test_atlas_bundle_rejects_dangling_report_reference(
    tmp_path: Path,
    capsys,
) -> None:
    bundle_dir = create_bundle(tmp_path, capsys)
    payload = load_bundle(bundle_dir)
    (bundle_dir / payload["entries"][0]["report"]["path"]).unlink()

    status, stdout, stderr = invoke_atlas(bundle_dir, capsys)

    assert status == 1
    assert stdout == ""
    assert "cannot read report" in stderr


@pytest.mark.parametrize("version", [2, True])
def test_atlas_bundle_rejects_unsupported_bundle_schema_version(
    tmp_path: Path,
    capsys,
    version: object,
) -> None:
    bundle_dir = create_bundle(tmp_path, capsys)
    payload = load_bundle(bundle_dir)
    payload["schemaVersion"] = version
    write_bundle(bundle_dir, payload)

    status, stdout, stderr = invoke_atlas(bundle_dir, capsys)

    assert status == 1
    assert stdout == ""
    assert "unsupported bundle schemaVersion" in stderr


def test_atlas_bundle_rejects_unsupported_report_version(
    tmp_path: Path,
    capsys,
) -> None:
    bundle_dir = create_bundle(tmp_path, capsys)
    payload = load_bundle(bundle_dir)
    payload["entries"][0]["report"]["version"] = "ladon-report-v999"
    write_bundle(bundle_dir, payload)

    status, stdout, stderr = invoke_atlas(bundle_dir, capsys)

    assert status == 1
    assert stdout == ""
    assert "unsupported report version" in stderr
