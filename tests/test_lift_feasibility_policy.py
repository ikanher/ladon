"""Fail-closed scoring and shared clocks for the native lift experiment."""
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/check_nat_rational_lift_feasibility.py"
SPEC = importlib.util.spec_from_file_location("lift_feasibility", PATH)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.mark.parametrize("observed", ["rejected", "trust-rejected"])
def test_concrete_proof_rejections_satisfy_negative_control(observed):
    assert runner._case_passed("proof-rejected", observed) is True


@pytest.mark.parametrize("observed", ["checked", "unsupported", "incomplete", "unresolved", "timeout"])
def test_unknown_and_resource_results_cannot_pass_negative_control(observed):
    assert runner._case_passed("proof-rejected", observed) is False


def test_explicit_trust_and_positive_controls_keep_exact_status_requirements():
    assert runner._case_passed("trust-rejected", "rejected") is False
    assert runner._case_passed("checked", "trust-rejected") is False
    assert runner._case_passed("unsupported", "checked") is False


def test_external_deadline_can_only_shorten_the_current_budget():
    assert runner._effective_deadline(100.0, 1800, None) == 1900.0
    assert runner._effective_deadline(100.0, 1800, 700.0) == 700.0
    assert runner._effective_deadline(100.0, 1800, 5000.0) == 1900.0
    assert runner._effective_deadline(100.0, 1800, 20.0) == 20.0


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "20"])
def test_external_deadline_must_be_finite_native_numeric(value):
    with pytest.raises(ValueError):
        runner._effective_deadline(100.0, 1800, value)
