"""Dependency references describe expression traversal, not binder order."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ladon.semantic_local_context import validate_observed_local_context


def _captured_context():
    path = Path(__file__).parent / 'fixtures/semantic_context/reverse-dependency-order.json'
    return json.loads(path.read_text())


def test_real_dependency_traversal_order_can_differ_from_binder_order():
    captured = _captured_context()
    assert captured['observed'][2]['dependencies'] == ['local:1', 'local:0']
    validate_observed_local_context(captured['observed'], captured['requested'])


@pytest.mark.parametrize('dependencies', [[], ['local:0'], ['local:0', 'local:0'],
                                          ['local:0', 'unknown'], ['local:0', 'local:2']])
def test_dependent_expression_requires_exact_prior_dependency_membership(dependencies):
    captured = copy.deepcopy(_captured_context())
    captured['observed'][2]['dependencies'] = dependencies
    with pytest.raises(ValueError):
        validate_observed_local_context(captured['observed'], captured['requested'])


def test_forward_local_dependency_is_rejected():
    captured = _captured_context()
    observed = captured['observed']
    requested = captured['requested']
    with pytest.raises(ValueError):
        validate_observed_local_context([observed[2], *observed[:2]],
                                        [requested[2], *requested[:2]])
