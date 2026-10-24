"""Every declared provider clock bounds even historical native validation work."""
from time import monotonic

import pytest
from test_proof_contract_provider_preflight import _request

from ladon import proof_contract_provider_expansion as expansion


@pytest.mark.parametrize('clock',['outer','saved','native'])
def test_expired_declared_clock_launches_no_worker(clock,monkeypatch):
    request = _request()
    if clock=='outer':
        request['deadlineMonotonic']=monotonic()-1
    elif clock=='saved':
        request['providerSliceRequest']['deadlineMonotonic']=monotonic()-1
    else:
        # Even an unvalidated expired declaration should stop without claiming
        # validity or spending a worker. No identity is accepted by this path.
        request['analysisArtifact']['payload']['request']['bounds']={
            'deadlineUtc':'2000-01-01T00:00:00Z'}
    monkeypatch.setattr(expansion,'run_obligation_validation',
        lambda *args, **_kwargs: pytest.fail('expired native validation launched'))
    result=expansion.expand_obligation_provider(request)
    assert result['status']=='incomplete'
    assert result['providerSnapshot'] is None
    assert result['slice'] is None
    assert result['wholeMethodAuthority']=='none'
