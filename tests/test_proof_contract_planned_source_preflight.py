"""Bounded public failure behavior for plan-bound source materialization."""
import importlib
from time import monotonic

import pytest


def _invoke(request):
    module = importlib.import_module('ladon.proof_contract_source_obligations')
    operation = getattr(module, 'instantiate_planned_source_leaf_requirement', None)
    assert callable(operation), 'missing planned source constructor'
    return operation(request)


def _invalid_request():
    return {'repoRoot': '.', 'parentSnapshot': None, 'providerSnapshot': None,
            'parentReadingId': 'reading:parent', 'providerReadingId': 'reading:provider',
            'planRequest': None, 'planResult': {}, 'routeIndex': 0, 'requirementIndex': 0,
            'selectedIdentity': {}, 'deadlineMonotonic': monotonic() + 30,
            'limits': {'timeout_seconds': 30, 'max_output_bytes': 8 * 1024**2,
                       'max_rss_bytes': 12 * 1024**3}}


@pytest.mark.parametrize('candidate', [None, [], {}, {'allowParentMismatch': True}])
def test_invalid_request_has_small_structured_rejection(candidate):
    result = _invoke(candidate)
    assert result['status'] == 'rejected'
    assert result.get('capture') is None
    assert result['wholeMethodAuthority'] == 'none'


def test_invalid_planner_type_does_not_escape_as_attribute_error():
    result = _invoke(_invalid_request())
    assert result['status'] == 'rejected'
    assert result.get('capture') is None


def test_oversized_untrusted_plan_is_not_echoed_as_evidence():
    request = _invalid_request()
    request['planResult'] = {'routeComparisons': [{'payload': 'x' * (8 * 1024**2)}]}
    result = _invoke(request)
    assert result['status'] == 'rejected'
    assert result.get('capture') is None
    assert not result.get('routeComparisons')
    assert result.get('planCoverage') is None


def test_deeply_nested_untrusted_plan_is_bounded_before_copying():
    request = _invalid_request()
    nested = {}
    for _ in range(150):
        nested = {'nested': nested}
    request['planResult'] = {'routeComparisons': [nested]}
    result = _invoke(request)
    assert result['status'] == 'rejected'
    assert result.get('capture') is None
    assert not result.get('routeComparisons')
