from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ladon.inspection_adapters import load_inspection_dataset
from ladon.inspection_query import inspect_dataset
from ladon.pipeline import RunContext, run_pipeline
from ladon.report_v3 import build_report_v3

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"
PROOF_XRAY_POINTER = "#/sections/proof_xray/rows/"


def test_report_proof_xray_rows_retain_quoted_authority(
    tmp_path: Path,
) -> None:
    report = _proof_xray_report(
        tmp_path,
        [
            {
                **_proof_xray_row("proof-xray:tiny", "Tiny.Core.coreTruth", 3),
                "dependencies": ["Tiny.Core.helper"],
                "axioms": ["Classical.choice"],
            }
        ],
    )
    dataset = load_inspection_dataset(
        report,
        "proof-mechanisms",
        artifact_kind="report",
    )
    payload = json.loads(report.read_text(encoding="utf-8"))

    _assert_quoted_proof_rows(dataset, payload)


def _assert_quoted_proof_rows(dataset, payload: dict[str, Any]) -> None:
    """Require unique exact lookup and registered quoted-row coverage."""

    quoted = _quoted_rows(dataset)
    assert {row.identifier for row in quoted} == {
        "proof-xray:tiny:automation_hotspot",
        "proof-xray:tiny:dependency_context",
        "proof-xray:tiny:trust_footprint",
    }
    assert len({row.canonical_ref for row in quoted}) == 3
    assert {row.coverage_ref for row in quoted} == {"proof_xray.rows"}
    _assert_proof_xray_coverage(dataset, payload)
    _assert_exact_quoted_rows(dataset, quoted)


def _assert_proof_xray_coverage(dataset, payload: dict[str, Any]) -> None:
    coverage = payload["coverage"]["collections"]["proof_xray.rows"]
    assert (
        coverage["visible"],
        coverage["total"],
        coverage["omitted"],
        coverage["completeness"],
        coverage["authority"],
    ) == (3, 3, 0, "complete", "proof_xray_staging")
    assert dataset.coverage["authority"] == "multiple_registered_authorities"


def _assert_exact_quoted_rows(dataset, quoted) -> None:
    for row in quoted:
        assert row.authority == "lean_elaborated"
        assert row.enrichments[0]["quotedOnly"] is True
        assert row.source_anchor.path == "Tiny/Core.lean"
        exact = inspect_dataset(dataset, identifier=row.identifier)
        assert [selected.identifier for selected in exact.rows] == [row.identifier]


def test_report_proof_xray_disambiguates_duplicate_provider_ids(
    tmp_path: Path,
) -> None:
    report = _proof_xray_report(
        tmp_path,
        [
            _proof_xray_row("proof-xray:duplicate", "Tiny.Core.first", 3),
            _proof_xray_row("proof-xray:duplicate", "Tiny.Core.second", 7),
        ],
    )
    dataset = load_inspection_dataset(
        report,
        "proof-mechanisms",
        artifact_kind="report",
    )
    quoted = _quoted_rows(dataset)
    identifiers = {row.identifier for row in quoted}

    assert len(quoted) == 2
    assert len(identifiers) == 2
    assert "proof-xray:duplicate:automation_hotspot" not in identifiers
    _assert_exact_identifiers(dataset, identifiers)


def _assert_exact_identifiers(dataset, identifiers: set[str]) -> None:
    for identifier in identifiers:
        exact = inspect_dataset(dataset, identifier=identifier)
        assert [row.identifier for row in exact.rows] == [identifier]


def _quoted_rows(dataset):
    return [
        row
        for row in dataset.rows
        if row.canonical_ref.startswith(PROOF_XRAY_POINTER)
    ]


def _proof_xray_report(
    tmp_path: Path,
    rows: list[dict[str, Any]],
) -> Path:
    model = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            proof_xray={
                "artifactKind": "proof_xray",
                "schemaVersion": 1,
                "rows": rows,
            },
            source_cache_enabled=False,
        )
    ).to_report_model()
    report = tmp_path / "proof-xray-report.json"
    report.write_text(
        json.dumps(build_report_v3(model, projection="full").to_dict()),
        encoding="utf-8",
    )
    return report


def _proof_xray_row(
    row_id: str,
    declaration: str,
    line: int,
) -> dict[str, Any]:
    return {
        "rowId": row_id,
        "declarationName": declaration,
        "module": "Tiny.Core",
        "authority": "lean_elaborated",
        "backend": "fixture-helper",
        "toolVersion": "1",
        "confidence": "direct",
        "sourcePath": "Tiny/Core.lean",
        "sourceRange": {
            "start": {"line": line, "column": 1},
            "end": {"line": line, "column": 9},
        },
        "tacticSkeleton": ["intro", "simp", "rw", "exact", "done"],
    }
