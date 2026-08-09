from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon import calibration, root_matrix

ROOT = Path(__file__).parents[1]


def test_runtime_and_calibration_surfaces_have_no_quux_route() -> None:
    assert root_matrix.ROOT_ENVIRONMENT == {
        "matrix-factorization": "LADON_MATRIX_FACTORIZATION_ROOT"
    }
    with pytest.raises(ValueError, match="unknown optional repository roots"):
        root_matrix.default_root_matrix({"quux": "/separated/quux"}, environment={})
    assert "quux" not in json.dumps(
        {
            "builtin": calibration._BUILTIN_EXPECTATION_SUITES,
            "rootMatrix": calibration._ROOT_MATRIX_EXPECTATION_SUITES,
        }
    ).casefold()


def test_scripts_expose_no_quux_environment_or_benchmark_option() -> None:
    for relative in (
        "scripts/ladon_root_matrix.py",
        "scripts/lean_runtime_benchmark.py",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8").casefold()
        assert "quux" not in text
