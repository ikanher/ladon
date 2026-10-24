"""Bridge boundary and authority checks; no simulated row is Lean evidence."""
import copy
import importlib
from time import monotonic

import pytest
from test_proof_contract_planned_source_preflight import _invalid_request


def _api():
    return importlib.import_module('ladon.proof_contract_bridge')


def _forbid_construction(monkeypatch):
    monkeypatch.setattr(_api(), 'instantiate_planned_source_leaf_requirement',
        lambda *a, **_kwargs: pytest.fail('invalid or expired request reached source construction'))


@pytest.mark.parametrize('extra', ['callerFormula', 'proofContext'])
def test_caller_cannot_replace_formula_or_assumptions(extra, monkeypatch):
    _forbid_construction(monkeypatch)
    request = _invalid_request(); request[extra] = 'desired conclusion'
    assert _api().check_planned_source_bridge(request, {})['status'] == 'rejected'


@pytest.mark.parametrize('terms', [None, {'unknown': 'by trivial'},
    {'domain': 3}, {'domain': 'x'*(8*1024**2+1)},
    {'domain': 'a', 'object-map': 'b', 'conclusion': 'c', 'source-requirement': 'd', 'fifth': 'e'}])
def test_bad_terms_reject_before_source_construction(terms, monkeypatch):
    _forbid_construction(monkeypatch)
    assert _api().check_planned_source_bridge(_invalid_request(), terms)['status'] == 'rejected'


def test_cycle_rejects_before_copying(monkeypatch):
    _forbid_construction(monkeypatch)
    terms = {}; terms['domain'] = terms
    assert _api().check_planned_source_bridge(_invalid_request(), terms)['status'] == 'rejected'


def test_expired_source_is_incomplete_before_construction(monkeypatch):
    _forbid_construction(monkeypatch)
    request = _invalid_request(); request['deadlineMonotonic'] = monotonic()-1
    result = _api().check_planned_source_bridge(request, {})
    assert result['status'] == 'incomplete'
    assert result['wholeMethodAuthority'] == 'none'
    assert result['mathematicalFalsity'] == 'not-established'


def _accepted():
    return {'status': 'supported', 'completion': {'status': 'completed',
            'replay': {'status': 'accepted'}, 'trust': {'accepted': True}}}


def test_support_requires_structured_replay_and_trust():
    accepted = _api()._accepted_check
    assert accepted(_accepted())
    for field in ['replay', 'trust']:
        candidate = _accepted(); candidate['completion'][field] = 'accepted'
        assert not accepted(candidate)
    candidate = _accepted(); candidate['completion']['status'] = 'incomplete'
    assert not accepted(candidate)
    candidate = _accepted(); candidate['completion']['trust']['accepted'] = False
    assert not accepted(candidate)


def test_support_requires_every_ordered_channel():
    rows = [{'id': identity, 'status': 'checked-support', 'result': _accepted()} for identity in
            ['source-requirement', 'domain', 'object-map', 'conclusion']]
    supported = _api()._bridge_supported
    assert supported(rows)
    assert not supported(rows[:-1])
    assert not supported(list(reversed(rows)))
    for index in range(4):
        partial = copy.deepcopy(rows); partial[index]['status'] = 'unresolved'
        assert not supported(partial)
        partial[index]['status'] = 'checked-support'; partial[index]['result'] = {}
        assert not supported(partial)
