"""The acceptance runner selects only an explicitly approved child suite."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _runner():
    path = Path(__file__).resolve().parents[1] / 'scripts/run_child_acceptance.py'
    spec = importlib.util.spec_from_file_location('child_runner_plan', path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('suite_id', ['correctness-acceptance', 'authority-acceptance', 'integration-acceptance', 'discovery-acceptance'])
def test_runner_accepts_each_approved_child_inventory(suite_id: str) -> None:
    suite = {'suiteId': suite_id, 'testTargets': ['tests/test_case.py']}
    inventory = {'schema': 'ladon-child-acceptance-inventory-v1', 'schemaVersion': 1,
                 'requiredRuntimes': ['py311', 'py312'], 'suites': [suite],
                 'pytestTargets': suite['testTargets']}
    assert _runner()._suite(inventory, 'py311', {'tests/test_case.py': 'digest'}) == suite


def test_runner_rejects_unapproved_suite_identity() -> None:
    inventory = {'schema': 'ladon-child-acceptance-inventory-v1', 'schemaVersion': 1,
                 'requiredRuntimes': ['py311'],
                 'suites': [{'suiteId': 'invented', 'testTargets': ['tests/test_case.py']}],
                 'pytestTargets': ['tests/test_case.py']}
    with pytest.raises(ValueError, match='suite'):
        _runner()._suite(inventory, 'py311', {'tests/test_case.py': 'digest'})
