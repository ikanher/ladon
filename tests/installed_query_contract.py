"""Reusable installed-process contract for coverage-aware atlas queries."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from ladon.installed_contract import invoke


def assert_installed_exhaustive_query_contract(
    command: Sequence[str],
    tmp_path: Path,
) -> None:
    """Require exact atlas coverage to support an exhaustive installed query."""

    reports = tmp_path / "reports"
    reports.mkdir()
    report_path = reports / "complete.json"
    report_path.write_text(
        json.dumps(_complete_query_report()),
        encoding="utf-8",
    )
    sqlite_path = tmp_path / "atlas.sqlite"
    _require_file_output(
        command,
        "atlas",
        "--reports-root",
        str(reports),
        "--output-sqlite",
        str(sqlite_path),
        "--output",
        str(tmp_path / "atlas.json"),
    )

    result = invoke(
        command,
        "query",
        "--db",
        str(sqlite_path),
        "--query",
        "hotspots",
        "--exhaustive",
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "complete"
    assert payload["exhaustive"] is True
    assert payload["rows"][0]["subject"] == "Pkg.hotspot"
    assert payload["requiredCoverage"][0]["completeness"] == "complete"
    assert payload["nonclaim"] is None


def assert_installed_query_help_contract(command: Sequence[str]) -> None:
    """Require installed help to disclose exhaustive authority semantics."""

    result = invoke(command, "query", "--help")

    assert result.returncode == 0
    assert result.stderr == ""
    assert "--exhaustive" in result.stdout
    assert "complete authority" in result.stdout


def _require_file_output(command: Sequence[str], *arguments: str) -> None:
    result = invoke(command, *arguments)
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def _complete_query_report() -> dict:
    """Return a minimal full v3 report with exact finding coverage."""

    return {
        "metadata": {
            "report_version": "ladon-report-v3",
            "analysis_root_module": "Pkg",
        },
        "projection": {
            "name": "full",
            "analysis_fingerprint": "sha256:analysis",
            "omissions": [],
        },
        "snapshot": {
            "schema": "ladon-analysis-snapshot-v1",
            "identity": "sha256:snapshot",
            "sourceIndexFingerprint": "sha256:source",
        },
        "coverage": {
            "schema": "ladon-collection-coverage-v1",
            "collections": {
                "report.findings": _exact_finding_coverage(),
            },
        },
        "phases": {},
        "sections": {
            "module_dag": {
                "module_count": 1,
                "module_metadata": {},
            },
            "findings": [
                {
                    "kind": "declaration_fan_in_hotspot",
                    "subject": "Pkg.hotspot",
                    "count": 7,
                }
            ],
        },
    }


def _exact_finding_coverage() -> dict:
    return {
        "id": "report.findings",
        "pointer": "#/sections/findings",
        "visible": 1,
        "observedLowerBound": 1,
        "totalKnown": True,
        "total": 1,
        "omitted": 0,
        "completeness": "complete",
        "population": "selected findings",
        "scope": "Pkg",
        "authority": "ladon_analysis",
        "sourceFingerprint": "sha256:source",
        "scopeFingerprint": "sha256:scope",
        "analysisFingerprint": "sha256:analysis",
        "causes": [],
    }
