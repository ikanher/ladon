"""Reject expanded output before repeatedly copying its checkpoint binding."""
import json
from pathlib import Path

import pytest

from ladon import _proof_contract_context_goals as goals
from ladon import proof_contract_context_worker as worker


def test_expansion_budget_checked_before_full_binding_copies(monkeypatch):
    path = Path(__file__).parent / 'fixtures/proof_contract_context_bridge/observed-plan.json'
    prepared = json.loads(path.read_text())
    binding = {'untrusted-large-bookkeeping': 'x' * (2 * 1024**2)}
    original = goals.copy.deepcopy
    copies = []

    def track(value):
        if value is binding:
            copies.append(True)
        return original(value)

    monkeypatch.setattr(goals.copy, 'deepcopy', track)
    with pytest.raises(ValueError, match='output|budget'):
        goals.build_context_goals(prepared, binding)
    assert copies == []


def test_worker_oversized_preparation_is_a_small_incomplete_resource_stop():
    result = {'status': 'prepared', 'goals': ['x' * (8 * 1024**2 + 1)]}
    body = worker._response(result)
    decoded = json.loads(body)
    assert len(body.encode()) < 4096
    assert decoded['status'] == 'completed'
    assert decoded['result']['status'] == 'output-limit'
