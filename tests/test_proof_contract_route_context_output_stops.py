"""Expanded raw evidence overflow must stop the entire remaining check loop."""
import pytest

import ladon._proof_contract_route_context_preparation as preparation
import ladon.proof_contract_route_context_worker as worker
from ladon._proof_contract_context_goals import ContextOutputLimit
from ladon.proof_contract_bridge import _resource_stop


@pytest.mark.parametrize('operation', ['prepare-route-context', 'check-route-context-goal'])
def test_output_overflow_remains_a_resource_stop(operation, monkeypatch):
    def overflow(_request):
        raise ContextOutputLimit('raw goal evidence exceeds 8 MiB')

    monkeypatch.setattr(preparation, 'prepare_route_context', overflow)
    monkeypatch.setattr(worker, '_check_goal', overflow)
    result = worker._compute({'version': 1, 'operation': operation, 'request': {}})
    assert result['status'] == 'incomplete'
    assert result['code'] == 'output-limit'
    assert _resource_stop(result, {'max_rss_bytes': 12 * 1024**3})['code'] == 'output-limit'
