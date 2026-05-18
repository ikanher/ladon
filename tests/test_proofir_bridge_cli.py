from __future__ import annotations

import json
from pathlib import Path

from ladon.proofir_bridge_cli import main


FIXTURES = Path(__file__).parent / "fixtures" / "proofir_bridge"


def test_bridge_cli_writes_json_report(tmp_path: Path) -> None:
    output = tmp_path / "bridge-report.json"

    status = main(
        [
            "--ladon-report",
            str(FIXTURES / "ladon-report-complex-quadratic.json"),
            "--proofir-index",
            str(FIXTURES / "proofir-bridge-index-complex-quadratic.json"),
            "--out",
            str(output),
        ]
    )

    assert status == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["artifactKind"] == "ladon_proofir_bridge_report"
    assert payload["summary"]["joinedSurfaceCount"] == 2


def test_bridge_cli_accepts_clean_core_report_without_explicit_declarations(tmp_path: Path) -> None:
    output = tmp_path / "bridge-report.json"

    status = main(
        [
            "--ladon-report",
            str(FIXTURES / "ladon-report-quux-clean-core-complex-quadratic.json"),
            "--proofir-index",
            str(FIXTURES / "proofir-bridge-index-quux-complex-quadratic.json"),
            "--out",
            str(output),
        ]
    )

    assert status == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["summary"]["declarationCount"] == 8
    assert payload["summary"]["joinedSurfaceCount"] == 2


def test_bridge_cli_accepts_absent_proofir_index(tmp_path: Path) -> None:
    output = tmp_path / "bridge-report.json"

    status = main(
        [
            "--ladon-report",
            str(FIXTURES / "ladon-report-complex-quadratic.json"),
            "--out",
            str(output),
        ]
    )

    assert status == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["summary"]["proofirIndexPresent"] is False


def test_bridge_cli_reports_bad_json_path(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "--ladon-report",
            str(tmp_path / "missing.json"),
            "--out",
            str(tmp_path / "bridge-report.json"),
        ]
    )

    assert status == 1
    assert "ladon-proofir-bridge:" in capsys.readouterr().err
