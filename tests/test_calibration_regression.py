from __future__ import annotations

import json
from pathlib import Path

from ladon.calibration import (
    BUILTIN_EXPECTATION_SUITES,
    ROOT_MATRIX_EXPECTATION_SUITES,
    evaluate_expectations,
    evaluate_report_suite,
    evaluate_reports_root,
    expectation_suites_by_name,
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
            {
                "kind": "root_scope_pressure",
                "root_scope": {"classification": "narrow_owner"},
            },
        ],
        "review_regions": [
            {"kind": "import_context_region", "signal_count": 2},
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
            {"type": "finding_kind_absent", "kind": "unresolved_reference_hotspot"},
            {"type": "root_scope_classification", "classification": "narrow_owner"},
            {"type": "review_region_present", "kind": "import_context_region", "min_signals": 2},
        ],
        report_name="quux",
    )

    assert [row["passed"] for row in rows] == [True, True, False, True, True, True]
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


def test_evaluate_reports_root_uses_root_matrix_suite(tmp_path: Path) -> None:
    write_report(tmp_path / "quux" / "quux-project.json", pressure_region_payload())
    write_report(tmp_path / "quux" / "quux-propagation.json", sample_payload())
    write_report(tmp_path / "quux" / "quux-bifr-rmse-problem.json", context_region_payload())
    write_report(tmp_path / "matrix-factorization" / "mf-project.json", mf_project_payload())
    write_report(
        tmp_path / "matrix-factorization" / "mf-bifr-packed-profile.json",
        mf_bifr_payload(),
    )
    write_report(
        tmp_path / "matrix-factorization" / "mf-gaussian-core.json",
        gaussian_core_payload(),
    )
    write_report(
        tmp_path / "matrix-factorization" / "mf-bsr-factor-core.json",
        bsr_factor_payload(),
    )
    write_report(
        tmp_path / "matrix-factorization" / "mf-optimization-ftrl.json",
        ftrl_payload(),
    )

    rows = evaluate_reports_root(tmp_path, ROOT_MATRIX_EXPECTATION_SUITES)

    assert rows
    assert all(row["passed"] for row in rows)


def test_expectation_suites_by_name_exposes_named_suites() -> None:
    suites = expectation_suites_by_name()

    assert suites["live"] is BUILTIN_EXPECTATION_SUITES
    assert suites["root-matrix"] is ROOT_MATRIX_EXPECTATION_SUITES


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
    payload["findings"] = [
        {"kind": "module_fan_in_hotspot"},
        {"kind": "composite_import_pressure"},
        {"kind": "facade_fanout_pressure"},
        {
            "kind": "root_scope_pressure",
            "root_scope": {"classification": "public_root_narrow_inventory"},
        },
    ]
    return payload


def mf_bifr_payload() -> dict:
    payload = mf_project_payload()
    payload["findings"] = [
        {"kind": "root_import_closure_hotspot"},
        {"kind": "proof_family_import_pressure"},
        {
            "kind": "root_scope_pressure",
            "root_scope": {"classification": "narrow_owner_broad_import"},
        },
    ]
    payload["review_regions"] = [
        {"kind": "import_pressure_region", "signal_count": 3},
        {"kind": "proof_family_region", "signal_count": 14},
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


def context_region_payload(module_count: int = 370) -> dict:
    payload = sample_payload()
    payload["module_dag"]["module_count"] = module_count
    payload["review_regions"] = [
        {"kind": "import_context_region", "signal_count": 2},
    ]
    return payload


def gaussian_core_payload() -> dict:
    payload = context_region_payload(module_count=530)
    payload["declaration_graph"]["declaration_count"] = 34
    return payload


def bsr_factor_payload() -> dict:
    payload = mf_project_payload()
    payload["declaration_graph"]["declaration_count"] = 67
    payload["findings"].append({"kind": "proof_family_import_pressure"})
    payload["review_regions"] = [
        {"kind": "import_pressure_region", "signal_count": 5},
        {"kind": "proof_family_region", "signal_count": 12},
    ]
    return payload


def ftrl_payload() -> dict:
    payload = mf_project_payload()
    payload["declaration_graph"]["declaration_count"] = 14
    payload["findings"] = [
        {"kind": "root_scope_pressure", "root_scope": {"classification": "narrow_owner"}}
    ]
    return payload


def pressure_region_payload() -> dict:
    payload = sample_payload()
    payload["review_regions"] = [
        {"kind": "import_pressure_region", "signal_count": 7},
    ]
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
