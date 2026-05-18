from __future__ import annotations

import json
import importlib.util
from pathlib import Path


def test_calibration_regression_script_reports_failures(tmp_path: Path, capsys) -> None:
    reports = tmp_path / "reports"
    (reports / "quux").mkdir(parents=True)
    (reports / "quux" / "project-quux.json").write_text(
        json.dumps({"module_dag": {"module_count": 1, "acyclic": False}}),
        encoding="utf-8",
    )

    status = script_main()(["--reports-root", str(reports)])

    captured = capsys.readouterr()
    assert status == 1
    assert "FAIL" in captured.out
    assert "missing report file" in captured.out


def test_calibration_regression_script_accepts_suite_argument(tmp_path: Path, capsys) -> None:
    reports = tmp_path / "reports"
    write_minimal_root_matrix_reports(reports)

    status = script_main()(["--reports-root", str(reports), "--suite", "root-matrix"])

    captured = capsys.readouterr()
    assert status == 0
    assert "PASS quux/quux-project.json" in captured.out


def write_minimal_root_matrix_reports(reports: Path) -> None:
    payload = {
        "module_dag": {
            "acyclic": True,
            "module_count": 370,
            "top_fan_in": [{"module": "Quux.Basic", "fan_in": 101}],
            "top_fan_out": [{"module": "Quux.Problems", "fan_out": 90}],
        },
        "findings": [
            {"kind": "composite_import_pressure"},
            {"kind": "facade_fanout_pressure"},
            {"kind": "root_scope_pressure", "root_scope": {"classification": "narrow_owner"}},
        ],
        "review_regions": [{"kind": "import_context_region", "signal_count": 2}],
        "declaration_graph": {
            "declaration_count": 11,
            "top_fan_in": [{"declaration": "Quux.Semantics.PropagationAlgebra", "fan_in": 8}],
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
        },
    }
    reports.joinpath("quux").mkdir(parents=True)
    reports.joinpath("matrix-factorization").mkdir(parents=True)
    writes = {
        "quux/quux-project.json": pressure_payload(payload),
        "quux/quux-propagation.json": payload,
        "quux/quux-bifr-rmse-problem.json": payload,
        "matrix-factorization/mf-project.json": matrix_project_payload(payload),
        "matrix-factorization/mf-bifr-packed-profile.json": bifr_payload(payload),
        "matrix-factorization/mf-gaussian-core.json": gaussian_payload(payload),
        "matrix-factorization/mf-bsr-factor-core.json": bsr_payload(payload),
        "matrix-factorization/mf-optimization-ftrl.json": ftrl_payload(payload),
    }
    for relative, report in writes.items():
        reports.joinpath(relative).write_text(json.dumps(report), encoding="utf-8")


def matrix_project_payload(payload: dict) -> dict:
    report = json.loads(json.dumps(payload))
    report["module_dag"]["module_count"] = 530
    report["module_dag"]["top_fan_in"] = [{"module": "Mf.DP.Sensitivity", "fan_in": 14}]
    report["module_dag"]["top_fan_out"] = [{"module": "Mf.NTK", "fan_out": 31}]
    report["findings"] = [
        {"kind": "composite_import_pressure"},
        {"kind": "facade_fanout_pressure"},
        {
            "kind": "root_scope_pressure",
            "root_scope": {"classification": "public_root_narrow_inventory"},
        },
    ]
    return report


def bifr_payload(payload: dict) -> dict:
    report = matrix_project_payload(payload)
    report["findings"].append({"kind": "proof_family_import_pressure"})
    report["findings"].append({"kind": "root_import_closure_hotspot"})
    report["findings"].append(
        {
            "kind": "root_scope_pressure",
            "root_scope": {"classification": "narrow_owner_broad_import"},
        }
    )
    report["declaration_graph"]["top_fan_in"] = [
        {"declaration": "Mf.DP.bifrHalfLinePackedProfileIndex", "fan_in": 14}
    ]
    report["review_regions"] = [
        {"kind": "import_pressure_region", "signal_count": 3},
        {"kind": "proof_family_region", "signal_count": 14},
    ]
    return report


def bsr_payload(payload: dict) -> dict:
    report = matrix_project_payload(payload)
    report["findings"].append({"kind": "proof_family_import_pressure"})
    report["review_regions"] = [
        {"kind": "import_pressure_region", "signal_count": 5},
        {"kind": "proof_family_region", "signal_count": 12},
    ]
    report["declaration_graph"]["declaration_count"] = 67
    return report


def gaussian_payload(payload: dict) -> dict:
    report = matrix_project_payload(payload)
    report["declaration_graph"]["declaration_count"] = 34
    return report


def ftrl_payload(payload: dict) -> dict:
    report = matrix_project_payload(payload)
    report["findings"] = [
        {"kind": "root_scope_pressure", "root_scope": {"classification": "narrow_owner"}}
    ]
    report["declaration_graph"]["declaration_count"] = 14
    return report


def pressure_payload(payload: dict) -> dict:
    report = json.loads(json.dumps(payload))
    report["review_regions"] = [
        {"kind": "import_pressure_region", "signal_count": 7},
    ]
    return report


def script_main():
    script = Path(__file__).parents[1] / "scripts" / "ladon_calibration_regression.py"
    spec = importlib.util.spec_from_file_location("ladon_calibration_regression", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main
