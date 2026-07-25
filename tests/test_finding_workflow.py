from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ladon.cli import main
from ladon.finding_workflow import (
    DanglingFindingEvidenceError,
    FindingNotFoundError,
    enrich_findings,
    inspect_findings,
    parse_finding_filter,
)


def enriched_rows() -> list[dict[str, object]]:
    return enrich_findings(
        [
            {
                "kind": "module_import_hub",
                "subject": "Pkg.Owner",
                "severity": "warning",
                "message": "owner is an import hub",
            },
            {
                "kind": "module_leaf",
                "subject": "Pkg.Leaf",
                "severity": "info",
                "message": "leaf module",
            },
        ],
        analysis_root_module="Pkg",
        inventory_root="/target",
        module_dag={
            "module_metadata": {
                "Pkg.Owner": {"path": "Pkg/Owner.lean"},
                "Pkg.Leaf": {"path": "Pkg/Leaf.lean"},
            }
        },
        scope={
            "kind": "owner",
            "analysisRootModule": "Pkg",
            "inventoryRoot": "/target",
        },
    )


def test_enrichment_adds_scope_identity_evidence_and_next_command() -> None:
    rows = enriched_rows()

    assert rows[0]["id"].startswith("ladon.finding.")
    assert rows[0]["scope"]["kind"] == "owner"
    assert rows[0]["evidenceRefs"] == [
        {
            "type": "source",
            "path": "Pkg/Owner.lean",
            "authority": "ladon_derived_heuristic",
        }
    ]
    assert rows[0]["priority"] == 200
    assert rows[0]["confidence"] == "derived"
    assert rows[0]["nextCommand"]["arguments"] == [
        "preview",
        "--root",
        "Pkg.Owner",
        "--scope",
        "owner",
    ]


def test_enrichment_preserves_rich_source_evidence_without_flattening() -> None:
    source_range = {
        "start": {"line": 7, "column": 3},
        "end": {"line": 9, "column": 11},
    }
    selection_range = {
        "start": {"line": 7, "column": 7},
        "end": {"line": 7, "column": 18},
    }
    rows = enrich_findings(
        [
            {
                "kind": "source_pattern.match",
                "subject": "Pkg/Owner.lean:7",
                "severity": "warning",
                "message": "matched",
                "sourcePath": "Pkg/Owner.lean",
                "sourceRange": source_range,
                "selectionRange": selection_range,
                "sourceLocation": {"module": "Pkg.Owner", "declaration": "old"},
                "contentHash": "sha256:owner",
                "confidence": "parser_source_range",
                "authority": "lexical_text",
            }
        ],
        analysis_root_module="Pkg",
        inventory_root="/target",
        module_dag={"module_metadata": {}},
    )

    assert rows[0]["evidenceRefs"] == [
        {
            "type": "source",
            "path": "Pkg/Owner.lean",
            "range": source_range,
            "selectionRange": selection_range,
            "location": {"module": "Pkg.Owner", "declaration": "old"},
            "contentHash": "sha256:owner",
            "confidence": "parser_source_range",
            "authority": "lexical_text",
        }
    ]


def test_enrichment_rejects_vague_section_fallback() -> None:
    rows = enrich_findings(
        [
            {
                "kind": "unknown_aggregate",
                "subject": "not-a-module",
                "severity": "info",
                "message": "no exact owner row",
            }
        ],
        analysis_root_module="Pkg",
        inventory_root="/target",
        module_dag={"module_metadata": {}},
    )

    assert rows[0]["evidenceRefs"][0]["type"] == "unavailable"
    assert "exact canonical-row" in rows[0]["evidenceRefs"][0]["reason"]
    assert "pointer" not in rows[0]["evidenceRefs"][0]


def test_finding_selection_is_exact_filtered_and_deterministic() -> None:
    payload = {"findings": list(reversed(enriched_rows()))}

    view = inspect_findings(payload, filters=[("severity", "warning")])
    selected = view["findings"][0]

    assert view["selected"] == 1
    assert selected["subject"] == "Pkg.Owner"
    assert inspect_findings(payload, identifier=selected["id"])["selected"] == 1
    with pytest.raises(FindingNotFoundError, match="not found"):
        inspect_findings(payload, identifier="ladon.finding.absent")


def test_finding_filters_include_confidence_priority_and_population() -> None:
    rows = enriched_rows()
    rows[0]["promotion_population"] = "target_owned"
    payload = {"findings": rows}

    for field, value, count in (
        ("confidence", "derived", 2),
        ("priority", "200", 1),
        ("population", "target_owned", 1),
    ):
        view = inspect_findings(payload, filters=[(field, value)])
        assert view["selected"] == count
        assert view["findings"][0]["subject"] == "Pkg.Owner"


def test_finding_inspection_rejects_dangling_canonical_evidence() -> None:
    row = enriched_rows()[0]
    row["evidenceRefs"] = [
        {
            "type": "canonical-row",
            "pointer": "#/sections/module_dag/missing/0",
            "identity": {"module": "Pkg.Owner"},
        }
    ]

    with pytest.raises(DanglingFindingEvidenceError, match="dangling pointer"):
        inspect_findings(
            {"sections": {"module_dag": {}}, "findings": [row]}
        )


def test_finding_inspection_rejects_canonical_identity_mismatch() -> None:
    row = enriched_rows()[0]
    row["evidenceRefs"] = [
        {
            "type": "canonical-row",
            "pointer": "#/sections/module_dag/rows/0",
            "identity": {"module": "Pkg.Other"},
        }
    ]

    with pytest.raises(DanglingFindingEvidenceError, match="identity mismatch"):
        inspect_findings(
            {
                "sections": {
                    "module_dag": {"rows": [{"module": "Pkg.Owner"}]}
                },
                "findings": [row],
            }
        )


def test_parse_finding_filter_rejects_undocumented_fields() -> None:
    assert parse_finding_filter("kind=module_leaf") == ("kind", "module_leaf")
    assert parse_finding_filter("population=target_owned") == (
        "population",
        "target_owned",
    )
    with pytest.raises(ValueError, match="invalid finding filter"):
        parse_finding_filter("message=anything")


def test_installed_findings_command_reads_report_without_analysis(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps({"findings": enriched_rows()}),
        encoding="utf-8",
    )

    status = main(
        [
            "findings",
            "--report",
            str(report),
            "--filter",
            "scope=owner",
            "--format",
            "text",
        ]
    )

    captured = capsys.readouterr()
    assert status == 0
    assert "Pkg.Owner" in captured.out
    assert "evidence: Pkg/Owner.lean" in captured.out
    assert captured.err == ""


def test_installed_findings_command_missing_id_is_operational(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps({"findings": enriched_rows()}),
        encoding="utf-8",
    )

    status = main(
        [
            "findings",
            "--report",
            str(report),
            "--id",
            "ladon.finding.absent",
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert "finding identifier not found" in captured.err


def test_installed_findings_command_rejects_dangling_evidence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = tmp_path / "report.json"
    row = enriched_rows()[0]
    row["evidenceRefs"] = [
        {
            "type": "canonical-row",
            "pointer": "#/sections/module_dag/rows/7",
            "identity": {"module": "Pkg.Owner"},
        }
    ]
    report.write_text(
        json.dumps(
            {
                "sections": {"module_dag": {"rows": []}},
                "findings": [row],
            }
        ),
        encoding="utf-8",
    )

    status = main(["findings", "--report", str(report)])

    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert "dangling pointer" in captured.err


def test_default_v3_report_round_trips_through_findings_command(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = tmp_path / "report-v3.json"

    analysis_status = main(
        [
            "--repo-root",
            str(Path(__file__).parent / "fixtures" / "tiny_lean"),
            "--root",
            "Tiny.lean",
            "--format",
            "json",
            "--output",
            str(report),
            "--progress",
            "off",
        ]
    )
    assert analysis_status == 0
    assert json.loads(report.read_text(encoding="utf-8"))["metadata"][
        "report_version"
    ] == "ladon-report-v3"
    capsys.readouterr()

    findings_status = main(
        [
            "findings",
            "--report",
            str(report),
            "--format",
            "json",
            "--output",
            "-",
        ]
    )

    captured = capsys.readouterr()
    assert findings_status == 0
    assert json.loads(captured.out)["schema"] == "ladon-finding-view-v1"
    assert captured.err == ""

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert_evidence_refs_resolve(payload)


def assert_evidence_refs_resolve(payload: dict[str, Any]) -> None:
    """Require exact local pointers or explicit external/unavailable evidence."""

    for finding in payload["sections"]["findings"]:
        assert finding["evidenceRefs"]
        for reference in finding["evidenceRefs"]:
            if reference["type"] in {"canonical-row", "aggregate"}:
                resolved = resolve_json_pointer(payload, reference["pointer"])
                identity = reference.get("identity", {})
                assert all(resolved.get(key) == value for key, value in identity.items())
            elif reference["type"] == "source":
                assert reference["path"]
            else:
                assert reference["type"] == "unavailable"
                assert reference["reason"]


def resolve_json_pointer(payload: Any, pointer: str) -> Any:
    """Resolve one local RFC 6901 pointer for evidence-link regressions."""

    value = payload
    for raw_token in pointer.removeprefix("#/").split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value
