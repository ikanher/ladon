from __future__ import annotations

import json
from pathlib import Path

from ladon.calibration import (
    BUILTIN_EXPECTATION_SUITES,
    evaluate_expectations,
    evaluate_report_suite,
    evaluate_reports_root,
)


def sample_payload() -> dict:
    return {
        "module_dag": {
            "module_count": 370,
            "acyclic": True,
            "top_fan_in": [
                {"module": "Quux.Basic", "fan_in": 101},
                {"module": "Quux.Semantics.Linear", "fan_in": 10},
            ],
            "top_fan_out": [
                {"module": "Quux.Problems", "fan_out": 90},
            ],
        },
        "findings": [
            {"kind": "module_fan_in_hotspot"},
            {"kind": "composite_import_pressure"},
            {"kind": "facade_fanout_pressure"},
            {"kind": "unresolved_reference_hotspot"},
        ],
        "declaration_graph": {
            "declaration_count": 11,
            "top_fan_in": [
                {"declaration": "Quux.Semantics.PropagationAlgebra", "fan_in": 8}
            ],
            "declaration_name_families": [],
            "proof_family_similarity_candidates": [],
        },
    }


def test_evaluate_expectations_returns_pass_and_fail_rows() -> None:
    rows = evaluate_expectations(
        sample_payload(),
        [
            {"type": "acyclic"},
            {
                "type": "top_module_fan_in",
                "module": "Quux.Basic",
                "max_rank": 1,
                "min_value": 100,
            },
            {"type": "finding_kind_present", "kind": "missing"},
        ],
        report_name="quux",
    )

    assert [row["passed"] for row in rows] == [True, True, False]
    assert rows[2]["predicate"] == "finding_kind_present"
    assert rows[2]["report"] == "quux"


def test_evaluate_report_suite_handles_missing_reports(tmp_path: Path) -> None:
    rows = evaluate_report_suite(
        tmp_path,
        {
            "missing.json": [{"type": "acyclic"}],
        },
    )

    assert rows == [
        {
            "report": "missing.json",
            "predicate": "report_exists",
            "passed": False,
            "message": "missing report file",
        }
    ]


def test_evaluate_reports_root_uses_builtin_quux_mf_layout(tmp_path: Path) -> None:
    write_report(tmp_path / "quux" / "project-quux.json", sample_payload())
    write_report(tmp_path / "quux" / "owner-propagation-lean.json", sample_payload())
    write_report(tmp_path / "matrix-factorization" / "project-mf.json", mf_project_payload())
    write_report(
        tmp_path / "matrix-factorization" / "owner-bifr-packed-profile-lean.json",
        mf_bifr_payload(),
    )
    write_report(
        tmp_path / "matrix-factorization" / "owner-bifr-r37-packet.json",
        mf_packet_payload(),
    )

    rows = evaluate_reports_root(tmp_path, BUILTIN_EXPECTATION_SUITES)

    assert rows
    assert all(row["passed"] for row in rows)


def write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def mf_project_payload() -> dict:
    payload = sample_payload()
    payload["module_dag"] = {
        "module_count": 530,
        "acyclic": True,
        "top_fan_in": [
            {"module": "Mf.DP.Sensitivity", "fan_in": 14},
            {"module": "Mf.DP.PLDRandomAllocation", "fan_in": 12},
        ],
        "top_fan_out": [
            {"module": "Mf.NTK", "fan_out": 31},
            {"module": "Mf.DP.BNB", "fan_out": 10},
        ],
    }
    return payload


def mf_bifr_payload() -> dict:
    payload = mf_project_payload()
    payload["findings"] = [
        {"kind": "root_import_closure_hotspot"},
        {"kind": "proof_family_import_pressure"},
    ]
    payload["declaration_graph"] = {
        "declaration_count": 46,
        "top_fan_in": [
            {"declaration": "Mf.DP.bifrHalfLinePackedProfileIndex", "fan_in": 14}
        ],
        "declaration_name_families": [
            {"suffix": "ge_one_add_firstLag", "count": 6},
            {"suffix": "nonneg", "count": 6},
        ],
        "proof_family_similarity_candidates": [
            {"suffix": "eq_forward"},
            {"suffix": "ge_one"},
            {"suffix": "last"},
            {"suffix": "nonneg"},
            {"suffix": "rev"},
        ],
    }
    return payload


def mf_packet_payload() -> dict:
    payload = mf_project_payload()
    payload["findings"] = [{"kind": "root_import_closure_hotspot"}]
    payload["packet_evidence"] = [
        {
            "packet_dir": "/tmp/r37",
            "status": "partial",
            "score": 3,
            "max_score": 6,
        }
    ]
    return payload
