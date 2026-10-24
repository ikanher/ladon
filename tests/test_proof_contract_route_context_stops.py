"""A cooperative deadline stop must remain recognizable by the supervisor."""
import pytest

import ladon._proof_contract_route_context_preparation as preparation
import ladon.proof_contract_route_context_worker as worker
from ladon.proof_contract_bridge import _resource_stop


@pytest.mark.parametrize('operation', ['prepare-route-context', 'check-route-context-goal'])
def test_cooperative_timeout_remains_a_resource_stop(operation, monkeypatch):
    def expired(_request):
        raise TimeoutError('shared absolute deadline expired')

    monkeypatch.setattr(preparation, 'prepare_route_context', expired)
    monkeypatch.setattr(worker, '_check_goal', expired)
    result = worker._compute({'version': 1, 'operation': operation, 'request': {}})
    assert result['status'] == 'incomplete'
    assert result['code'] == 'timeout'
    assert _resource_stop(result, {'max_rss_bytes': 12 * 1024**3})['code'] == 'timeout'
