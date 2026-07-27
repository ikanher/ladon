from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pytest import MonkeyPatch

from ladon.inspection_adapters import load_inspection_dataset
from ladon.inspection_models import InspectionCompatibilityError
from ladon.inspection_query import inspect_dataset
from ladon.ir import (
    LeanModule,
    LeanOptionOccurrence,
    LeanProofMechanismOccurrence,
)
from ladon.pipeline import RunContext, run_pipeline
from ladon.pipeline_inspection_navigation import (
    INSPECTION_OPTIONS_COVERAGE,
    attach_inspection_navigation,
)
from ladon.report_v3 import build_report_v3
from ladon.source_index_models import (
    SOURCE_FAILURE_DIAGNOSTIC,
    SourceIndex,
    SourceIndexEntry,
)


def option(module: str, index: int) -> LeanOptionOccurrence:
    """Build one exact lexical row for bounded-navigation tests."""

    offset = index * 10
    return LeanOptionOccurrence(
        identifier=f"option:{module}:{index}",
        module=module,
        path=f"{module}.lean",
        option="trace.Meta.Tactic",
        option_class="diagnostic",
        raw_value="true",
        raw_value_total_characters=4,
        raw_value_truncated=False,
        lexical_scope="module",
        line=index + 1,
        column=1,
        start_offset=offset,
        end_offset=offset + 9,
        status="parsed",
    )


def mechanism(
    module: str,
    index: int,
    name: str,
) -> LeanProofMechanismOccurrence:
    """Build one exact lexical proof-token row."""

    offset = index * 10
    return LeanProofMechanismOccurrence(
        identifier=f"mechanism:{module}:{index}:{name}",
        module=module,
        path=f"{module}.lean",
        mechanism=name,
        kind="tactic-token",
        line=index + 1,
        column=1,
        start_offset=offset,
        end_offset=offset + len(name),
        declaration_id=f"declaration:{module}",
        declaration_candidate=f"{module}.proof",
    )


def test_navigation_cap_samples_modules_fairly_and_reports_unknown_total(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ladon.pipeline_inspection_navigation.MAX_INSPECTION_NAVIGATION_ROWS",
        3,
    )
    modules = {
        "A": LeanModule(
            name="A",
            path="A.lean",
            option_rows=tuple(option("A", index) for index in range(3)),
        ),
        "B": LeanModule(
            name="B",
            path="B.lean",
            option_rows=tuple(option("B", index) for index in range(2)),
        ),
    }
    dag = {
        "analysis_scope": {
            "fingerprint": "sha256:scope",
        }
    }

    attach_inspection_navigation(dag, modules, None)

    assert [row["id"] for row in dag["inspection_navigation"]["options"]] == [
        "option:A:0",
        "option:B:0",
        "option:A:1",
    ]
    assert {row["coverageRef"] for row in dag["inspection_navigation"]["options"]} == {
        INSPECTION_OPTIONS_COVERAGE
    }
    coverage = dag["inspection_option_coverage"]
    assert coverage["visible"] == 3
    assert coverage["observedLowerBound"] == 5
    assert coverage["totalKnown"] is False
    assert coverage["omitted"] is None
    assert {cause["id"] for cause in coverage["causes"]} == {
        "module_dag.inspection_options.source_index_unavailable",
        "module_dag.inspection_options.report_navigation_limit",
    }


def test_proof_navigation_reserves_rare_mechanisms_deterministically(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ladon.pipeline_inspection_navigation.MAX_INSPECTION_NAVIGATION_ROWS",
        2,
    )
    module_a = LeanModule(
        name="A",
        path="A.lean",
        proof_mechanisms=(
            mechanism("A", 0, "simp"),
            mechanism("A", 1, "simp"),
        ),
    )
    module_b = LeanModule(
        name="B",
        path="B.lean",
        proof_mechanisms=(
            mechanism("B", 0, "simp"),
            mechanism("B", 1, "tauto"),
        ),
    )
    expected = [
        "mechanism:A:0:simp",
        "mechanism:B:1:tauto",
    ]

    ordered = [("A", module_a), ("B", module_b)]
    for modules in (dict(ordered), dict(reversed(ordered))):
        dag: dict[str, Any] = {}
        attach_inspection_navigation(dag, modules, None)
        rows = dag["inspection_navigation"]["proofMechanisms"]
        assert [row["id"] for row in rows] == expected
        assert {row["evidenceKind"] for row in rows} == {
            "tactic-token:simp",
            "tactic-token:tauto",
        }


def test_navigation_propagates_partial_source_index_causes() -> None:
    module = LeanModule(
        name="A",
        path="A.lean",
        option_rows=(option("A", 0),),
        proof_mechanisms=(mechanism("A", 0, "simp"),),
    )
    source_index = SourceIndex(
        repo_root=Path("/fixture"),
        fingerprint="f" * 64,
        fingerprint_manifest={
            "sources": [
                {
                    "module": "A",
                    "path": "A.lean",
                    "status": "present",
                    "bytes": 100,
                    "sha256": "a" * 64,
                },
                {
                    "module": "Missing",
                    "path": "Missing.lean",
                    "status": "present",
                    "bytes": 100,
                    "sha256": "b" * 64,
                },
            ]
        },
        layout_status="complete",
        source_roots=(),
        entries=(
            SourceIndexEntry(
                module=module,
                content_sha256="a" * 64,
                source_bytes=100,
            ),
        ),
        options={},
        index_status="partial",
        diagnostics=(
            {
                "id": SOURCE_FAILURE_DIAGNOSTIC,
                "module": "Missing",
                "path": "Missing.lean",
                "cause": "parse_error",
                "detail": "fixture parser failure",
                "message": "Missing failed",
            },
        ),
    )
    dag: dict[str, Any] = {}

    attach_inspection_navigation(dag, {"A": module}, source_index)

    for key in (
        "inspection_option_coverage",
        "inspection_proof_mechanism_coverage",
    ):
        coverage = dag[key]
        assert coverage["visible"] == 1
        assert coverage["observedLowerBound"] == 1
        assert coverage["totalKnown"] is False
        assert coverage["omitted"] is None
        assert coverage["completeness"] == "partial"
        assert [cause["id"] for cause in coverage["causes"]] == [
            SOURCE_FAILURE_DIAGNOSTIC
        ]


def test_complete_report_cap_preserves_exact_total_and_uncertain_absence(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ladon.pipeline_inspection_navigation.MAX_INSPECTION_NAVIGATION_ROWS",
        3,
    )
    repository = tmp_path / "repo"
    repository.mkdir()
    source = "\n".join(
        f"set_option trace.Meta.Tactic true -- {index}" for index in range(5)
    )
    (repository / "Root.lean").write_text(source + "\n", encoding="utf-8")
    result = run_pipeline(
        RunContext(
            repo_root=repository,
            requested_root="Root.lean",
            source_cache_enabled=False,
        )
    )
    payload = build_report_v3(
        result.to_report_model(),
        projection="full",
    ).to_dict()
    report = tmp_path / "report.json"
    report.write_text(json.dumps(payload), encoding="utf-8")
    dataset = load_inspection_dataset(
        report,
        "options",
        artifact_kind="report",
    )
    assert result.context.source_index is not None
    source_rows = result.context.source_index.modules["Root"].option_rows

    assert (
        dataset.coverage["visible"],
        dataset.coverage["total"],
        dataset.coverage["omitted"],
        dataset.coverage["completeness"],
    ) == (3, 5, 2, "partial")
    assert inspect_dataset(dataset, identifier=source_rows[0].identifier).rows
    with pytest.raises(
        InspectionCompatibilityError,
        match="cannot establish absence",
    ):
        inspect_dataset(dataset, identifier=source_rows[-1].identifier)
