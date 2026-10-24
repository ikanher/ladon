"""A proof term differing from the cached term follows the normal checker route."""
from test_probe_reuse_support import cache as _cache
from test_probe_reuse_support import prepared as _prepared
from test_probe_reuse_support import request as _request
from test_proof_contract_application_probe_contract import api


def test_changed_term_is_checked_again_instead_of_reusing_cached_support(tmp_path, monkeypatch):
    _, _, _, checker = api()
    import ladon.proof_contract_probes as probes

    request = _request(tmp_path)
    cache = _cache(tmp_path, request, plan_id=None)
    stages = []

    def stage(operation, payload, owned):
        stages.append(operation)
        if operation == 'prepare-probe':
            return {'status': 'completed', 'result': _prepared(request)}
        return {'status': 'rejected', 'result': None,
                'diagnostic': {'code': 'expected-recheck'}}

    monkeypatch.setattr(probes, '_stage', stage)
    result = checker(request, cache['planId'], {'probe': 'by trivial'}, cached_result=cache)
    assert stages == ['prepare-probe', 'check-probe-goal']
    assert result['status'] == 'unresolved'
    assert result['goals'][0]['reused'] is True
    assert result['goals'][1]['reused'] is False
    assert result['checkerAuthority'] == 'none'
