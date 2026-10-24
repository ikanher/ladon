"""Whole-route demand provenance must preserve OR choices and ordered AND edges."""
import copy
import json
from pathlib import Path

import pytest
from support.proof_contract_obligation_planner import repeated_and_case, request_kwargs

import ladon.proof_contract_obligation_planner as planner
from ladon.proof_contract_obligation_planner import ContractObligationPlanRequest

FIXTURE = Path(__file__).parent / 'fixtures/proof_contract_obligation_bundles/shared-demand-or.json'


def _request():
    fixture = json.loads(FIXTURE.read_text())
    return fixture, ContractObligationPlanRequest(**fixture['request'])


def _run(request):
    operation = getattr(planner, 'plan_contract_obligation_bundles', planner.plan_contract_obligations)
    return operation(request)


def _root_bundle(result, fixture):
    route = next(row for row in result['routeComparisons']
                 if row['routeId'] == fixture['targetRouteId'])
    bundle = route['obligationBundle']
    demands = {row['demandId']: row for row in bundle['demands']}
    return route, bundle, demands[bundle['rootDemandId']], demands


def test_legacy_result_and_identities_remain_exact():
    fixture, request = _request()
    assert planner.plan_contract_obligations(request) == fixture['result']


def test_shared_children_retain_both_parent_alternatives():
    fixture, request = _request()
    result = _run(request)
    route, bundle, root, demands = _root_bundle(result, fixture)
    assert len(root['alternatives']) == 2
    assert {r['branchRef'] for r in root['alternatives']} == set(fixture['rootBranchRefs'])
    _assert_shared_incoming_edges(root, demands)
    assert bundle['requestDigest'] == result['requestDigest']
    assert bundle['residuals'] == route['residuals']
    assert result['checkerAuthority'] == 'none'
    assert result['mathematicalFalsity'] == 'not-established'


def test_versioned_bundle_recomputation_is_deterministic_and_owned():
    fixture, request = _request()
    first = _run(request)
    second = _run(copy.deepcopy(request))
    assert first == second
    assert first['schema'] == 'ladon-contract-obligation-planner-v2'
    assert first['requestDigest'] == fixture['result']['requestDigest']
    assert first['analysisId'] != fixture['result']['analysisId']
    _, bundle, _, _ = _root_bundle(first, fixture)
    assert 'analysisId' not in bundle


def test_repeated_premises_keep_two_occurrences_even_with_one_child():
    request = ContractObligationPlanRequest(**request_kwargs(repeated_and_case()))
    result = _run(request)
    route = result['routeComparisons'][0]
    bundle = route['obligationBundle']
    root = next(d for d in bundle['demands'] if d['demandId'] == bundle['rootDemandId'])
    edges = root['alternatives'][0]['requirements']
    assert [edge['premiseOrdinal'] for edge in edges] == [0, 1]
    assert edges[0]['childDemandId'] == edges[1]['childDemandId']
    child = next(d for d in bundle['demands'] if d['demandId'] == edges[0]['childDemandId'])
    assert [r['premiseOrdinal'] for r in child['incomingOccurrences']] == [0, 1]
    assert child['alternatives'] == []
    assert child['status'] == 'requires-source-check'


@pytest.mark.parametrize('cap', [1, 2, 3])
def test_budget_stop_never_produces_an_empty_supported_bundle(cap):
    _, request = _request()
    request = type(request)(**{**vars(request), 'bounds': {'maxEvaluatedSteps': cap}})
    result = _run(request)
    assert result['status'] == 'partial'
    assert result['coverage']['pendingBranches']
    for route in result['routeComparisons']:
        bundle = route['obligationBundle']
        assert bundle['checkerAuthority'] == 'none'
        assert bundle['status'] in {'generated', 'partial', 'unsupported'}
        assert bundle['wholeMethodAuthority'] == 'none'


def _assert_shared_incoming_edges(root, demands):
    for branch in root['alternatives']:
        assert [r['premiseOrdinal'] for r in branch['requirements']] == [0, 1]
        for edge in branch['requirements']:
            child = demands[edge['childDemandId']]
            assert any(incoming['parentDemandId'] == root['demandId']
                       and incoming['branchRef'] == branch['branchRef']
                       and incoming['premiseOrdinal'] == edge['premiseOrdinal']
                       for incoming in child['incomingOccurrences'])
            assert len(child['incomingOccurrences']) == 2
