"""Reject invalid provider selections and oversized direct builder inputs early."""
from time import monotonic

import pytest
from test_proof_contract_provider_expansion import _limits, _native

from ladon import proof_contract_provider_expansion as expansion


def _request():
    _, _, analysis, context, route, demand, requirement = _native()
    deadline = monotonic()+30
    selected = expansion.make_provider_slice_request(analysis, context, route, demand,
                                                    requirement, deadline, _limits())
    return {'repoRoot': '.', 'analysisArtifact': analysis, 'context': context,
        'providerSliceRequest': selected, 'application': 'Eq.trans', 'occurrence': 0,
        'deadlineMonotonic': deadline, 'limits': _limits()}


@pytest.mark.parametrize('field,value', [('application','bad; command'),
    ('application',''), ('occurrence',{}), ('occurrence',True),
    ('occurrence',-1), ('occurrence',4096)])
def test_bad_application_selection_never_launches_native_worker(field, value, monkeypatch):
    request = _request(); request[field] = value
    monkeypatch.setattr(expansion,'run_obligation_validation',
        lambda *args, **_kwargs: pytest.fail('invalid selection launched a worker'))
    result = expansion.expand_obligation_provider(request)
    assert result['status'] == 'rejected'
    assert result['providerSnapshot'] is None
    assert result['slice'] is None


def test_direct_builder_admits_aggregate_size_before_owner_validation(monkeypatch):
    import ladon._proof_contract_provider_requests as builder
    _, _, analysis, context, route, demand, requirement = _native()
    context['oversized'] = 'x'*(8*1024**2)
    monkeypatch.setattr(builder,'validate_envelope',
        lambda *args, **_kwargs: pytest.fail('oversized builder reached owner validation'))
    with pytest.raises(ValueError, match='8 MiB'):
        expansion.make_provider_slice_request(analysis,context,route,demand,requirement,
                                              monotonic()+30,_limits())
