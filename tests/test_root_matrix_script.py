from __future__ import annotations

import importlib.util
from pathlib import Path


def test_root_matrix_script_dry_run_prints_selected_command(capsys) -> None:
    status = script_main()(
        [
            "--dry-run",
            "--repository-root",
            "matrix-factorization=/repos/matrix-factorization",
            "--only",
            "mf-project",
        ]
    )

    captured = capsys.readouterr()
    assert status == 0
    assert "mf-project" in captured.out
    assert "--repo-root /repos/matrix-factorization" in captured.out


def script_main():
    script = Path(__file__).parents[1] / "scripts" / "ladon_root_matrix.py"
    spec = importlib.util.spec_from_file_location("ladon_root_matrix", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main
