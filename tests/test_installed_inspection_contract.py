from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from ladon.installed_contract import invoke
from ladon.inspection_models import INSPECTION_NOUNS
from ladon.source_index import build_source_index


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"
INSPECTION_FIXTURE_ROOT = (
    Path(__file__).parent / "fixtures" / "inspection_lean"
)


@pytest.mark.parametrize("noun", INSPECTION_NOUNS)
def test_installed_inspection_every_noun_has_text_json_parity(
    tmp_path: Path,
    noun: str,
) -> None:
    index = installed_source_index(tmp_path)
    json_result = invoke(
        analyzer_command(),
        "inspect",
        noun,
        "--source-index",
        str(index),
    )
    text_result = invoke(
        analyzer_command(),
        "inspect",
        noun,
        "--source-index",
        str(index),
        "--format",
        "text",
    )

    payload = successful_json(json_result)
    assert payload["query"]["noun"] == noun
    assert payload["rows"]
    assert payload["coverage"]["collection"]["id"]
    assert text_result.returncode == 0
    assert text_result.stderr == ""
    assert_inspection_text_matches_json(payload, text_result.stdout)


def test_installed_inspection_help_and_late_page(
    tmp_path: Path,
) -> None:
    report = installed_report(tmp_path)
    help_run = invoke(analyzer_command(), "inspect", "--help")
    assert help_run.returncode == 0
    assert "--report REPORT | --source-index SOURCE_INDEX" in help_run.stdout
    assert "proof-mechanisms" in help_run.stdout
    assert help_run.stderr == ""

    first = installed_inspection(
        report,
        "declarations",
        "--limit",
        "2",
    )
    first_page = successful_json(first)
    assert len(first_page["rows"]) == 2
    assert first_page["nextCursor"]

    late = installed_inspection(
        report,
        "declarations",
        "--limit",
        "2",
        "--cursor",
        first_page["nextCursor"],
    )
    late_page = successful_json(late)
    assert len(late_page["rows"]) == 1
    assert disjoint_page_ids(first_page, late_page)
    assert_exact_text_lookup(report, late_page["rows"][0]["id"])


def test_installed_inspection_is_artifact_only_outside_checkout(
    tmp_path: Path,
) -> None:
    report = installed_report(tmp_path)
    outside = tmp_path / "outside-checkout"
    outside.mkdir()
    fake_bin, marker = forbidden_process_directory(tmp_path)
    environment = dict(os.environ)
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"

    result = subprocess.run(
        [
            *analyzer_command(),
            "inspect",
            "modules",
            "--report",
            str(report),
            "--format",
            "json",
        ],
        cwd=outside,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )

    assert successful_json(result)["rows"]
    assert not marker.exists()


def test_installed_inspection_accepts_emitted_source_index_cache_path(
    tmp_path: Path,
) -> None:
    report = tmp_path / "report.json"
    analyzed = invoke(
        analyzer_command(),
        "--repo-root",
        str(INSPECTION_FIXTURE_ROOT),
        "--root",
        "Tiny.lean",
        "--cache-dir",
        str(tmp_path / "cache"),
        "--format",
        "json",
        "--projection",
        "full",
        "--output",
        str(report),
        "--progress",
        "off",
    )
    assert analyzed.returncode == 0
    assert analyzed.stdout == analyzed.stderr == ""
    payload = json.loads(report.read_text(encoding="utf-8"))
    cache_path = Path(
        payload["sections"]["module_dag"]["source_index"]["cache"]["path"]
    )

    inspected = invoke(
        analyzer_command(),
        "inspect",
        "audits",
        "--source-index",
        str(cache_path),
    )

    page = successful_json(inspected)
    assert cache_path.is_file()
    assert page["rows"]
    assert page["rows"][0]["fields"]["subject"] == "Tiny.Core.coreTruth"
    assert page["artifact"]["sourceFingerprint"] == (
        payload["snapshot"]["sourceIndexFingerprint"]
    )


def test_installed_inspection_rejects_stale_live_source_binding(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    shutil.copytree(FIXTURE_ROOT, repository)
    index = tmp_path / "source-index.json"
    index.write_text(
        json.dumps(
            build_source_index(repository, use_cache=False).index.to_payload(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (repository / "Tiny.lean").write_text(
        "import Tiny.Core\nimport Tiny.Helper\n\ndef drift := true\n",
        encoding="utf-8",
    )

    stale = invoke(
        analyzer_command(),
        "inspect",
        "modules",
        "--source-index",
        str(index),
        "--repo-root",
        str(repository),
    )

    assert stale.returncode == 1
    assert stale.stdout == ""
    assert "inspection.incompatible_evidence" in stale.stderr
    assert "stale source-index" in stale.stderr


def installed_report(tmp_path: Path) -> Path:
    """Create one full report through the installed candidate."""

    report = tmp_path / "report.json"
    result = invoke(
        analyzer_command(),
        "--repo-root",
        str(FIXTURE_ROOT),
        "--root",
        "Tiny.lean",
        "--format",
        "json",
        "--projection",
        "full",
        "--output",
        str(report),
        "--progress",
        "off",
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
    return report


def installed_source_index(tmp_path: Path) -> Path:
    """Create one portable artifact with a positive row for every noun."""

    payload = build_source_index(
        INSPECTION_FIXTURE_ROOT,
        use_cache=False,
    ).index.to_payload()
    module = payload["entries"][0]["module"]
    common = {
        "module": "Tiny",
        "path": "Tiny.lean",
        "sourceRange": {
            "start": {"line": 1, "column": 1, "offset": 0},
            "end": {"line": 1, "column": 2, "offset": 1},
        },
        "status": "parsed",
        "authority": "lexical_text",
    }
    module["optionRows"] = [
        {
            **common,
            "id": "option:installed",
            "option": "pp.universes",
            "optionClass": "generic",
            "lexicalScope": "module",
        }
    ]
    module["resourceSettings"] = [
        {
            **common,
            "id": "resource:installed",
            "option": "maxHeartbeats",
            "normalizedMeaning": "unlimited",
            "lexicalScope": "module",
        }
    ]
    module["proofMechanisms"] = [
        {
            **common,
            "id": "mechanism:installed",
            "declaration": "Tiny.example",
            "mechanism": "simp",
            "kind": "tactic-token",
        }
    ]
    index = tmp_path / "source-index.json"
    index.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return index


def installed_inspection(
    report: Path,
    noun: str,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    """Run one JSON inspection against an installed-produced report."""

    return invoke(
        analyzer_command(),
        "inspect",
        noun,
        "--report",
        str(report),
        *arguments,
    )


def successful_json(result: subprocess.CompletedProcess[str]) -> dict:
    """Require clean installed channels and decode one JSON document."""

    assert result.returncode == 0
    assert result.stderr == ""
    return json.loads(result.stdout)


def assert_inspection_text_matches_json(payload: dict, text: str) -> None:
    """Require the installed text view to preserve JSON page semantics."""

    _assert_inspection_text_header(payload, text)
    positions = [
        _assert_inspection_text_row(row, text)
        for row in payload["rows"]
    ]
    assert positions == sorted(positions)
    assert len(positions) == len(set(positions))
    if payload["nextCursor"] is not None:
        assert f"Next cursor: {payload['nextCursor']}\n" in text


def _assert_inspection_text_header(payload: dict, text: str) -> None:
    """Compare page-level identity and coverage fields."""

    query = payload["query"]
    artifact = payload["artifact"]
    coverage = payload["coverage"]
    collection = coverage["collection"]
    assert f"Ladon inspection: {query['noun']}\n" in text
    assert (
        f"Artifact: {artifact['kind']} {artifact['schema']} "
        f"{artifact['fingerprint']}\n"
    ) in text
    assert f"Query fingerprint: {query['fingerprint']}\n" in text
    assert (
        f"Rows: {coverage['pageVisible']} visible, "
        f"{coverage['matchingVisibleTotal']} observed matching, "
        f"{coverage['before']} before, {coverage['after']} after\n"
    ) in text
    assert (
        f"Collection: {collection.get('id')} "
        f"({collection.get('completeness')}; "
        f"total={_optional_text_count(collection.get('total'))}; "
        f"omitted={_optional_text_count(collection.get('omitted'))})\n"
    ) in text


def _assert_inspection_text_row(row: dict, text: str) -> int:
    """Compare one row and return its installed-text position."""

    heading = (
        f"{row['id']} | authority={row['authority']} | "
        f"population={row['population']} | "
        f"source={_inspection_source_text(row['sourceAnchor'])}\n"
    )
    assert f"  canonical: {row['canonicalRef']}\n" in text
    assert f"  coverage: {row['coverageRef']}\n" in text
    fields = _inspection_fields_text(row["fields"])
    if fields:
        assert f"  fields: {fields}\n" in text
    _assert_inspection_enrichments(row["enrichments"], text)
    _assert_inspection_nonclaims(row["nonclaims"], text)
    return text.index(heading)


def _inspection_fields_text(fields: dict) -> str:
    return " ".join(
        f"{key}={_inspection_field_text(value)}"
        for key, value in sorted(fields.items())
        if value is not None and value != ""
    )


def _assert_inspection_enrichments(enrichments: list, text: str) -> None:
    for enrichment in enrichments:
        encoded = json.dumps(
            enrichment,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        assert f"  enrichment: {encoded}\n" in text


def _assert_inspection_nonclaims(nonclaims: list, text: str) -> None:
    for nonclaim in nonclaims:
        assert f"  nonclaim: {nonclaim}\n" in text


def _inspection_source_text(anchor: dict) -> str:
    if anchor["status"] != "exact":
        return f"unavailable ({anchor['reason']})"
    source_range = anchor.get("range")
    if not isinstance(source_range, dict):
        return str(anchor["path"])
    start = source_range.get("start")
    if not isinstance(start, dict) or start.get("line") is None:
        return str(anchor["path"])
    column = start.get("column")
    suffix = (
        f":{start['line']}"
        if column is None
        else f":{start['line']}:{column}"
    )
    return f"{anchor['path']}{suffix}"


def _inspection_field_text(value: object) -> str:
    if isinstance(value, (list, dict)):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    return str(value)


def _optional_text_count(value: object) -> str:
    return "unknown" if value is None else str(value)


def disjoint_page_ids(first: dict, second: dict) -> bool:
    """Return whether two installed pages have no repeated stable IDs."""

    return {row["id"] for row in first["rows"]}.isdisjoint(
        row["id"] for row in second["rows"]
    )


def assert_exact_text_lookup(report: Path, identifier: str) -> None:
    """Require installed exact lookup and text/JSON model agreement."""

    selected = installed_inspection(
        report,
        "declarations",
        "--id",
        identifier,
        "--format",
        "text",
    )
    assert selected.returncode == 0
    assert selected.stderr == ""
    assert identifier in selected.stdout


def forbidden_process_directory(tmp_path: Path) -> tuple[Path, Path]:
    """Install PATH-local tripwires for target-controlled executables."""

    fake_bin = tmp_path / "forbidden-bin"
    fake_bin.mkdir()
    marker = tmp_path / "target-process-started"
    for name in ("git", "lake", "lean"):
        executable = fake_bin / name
        executable.write_text(
            f"#!/bin/sh\nprintf '%s\\n' {name} >> {marker}\nexit 99\n",
            encoding="utf-8",
        )
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    return fake_bin, marker


def analyzer_command() -> list[str]:
    """Return the installed analyzer selected by the distribution smoke."""

    return [
        os.environ.get(
            "LADON_CONSOLE",
            str(Path(sys.executable).with_name("ladon")),
        )
    ]
