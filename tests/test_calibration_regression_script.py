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


def script_main():
    script = Path(__file__).parents[1] / "scripts" / "ladon_calibration_regression.py"
    spec = importlib.util.spec_from_file_location("ladon_calibration_regression", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main
