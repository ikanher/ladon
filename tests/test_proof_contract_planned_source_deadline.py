"""A completed replan cannot authorize later work after the shared deadline."""
from support.proof_contract_obligation_planner import request_kwargs, route_a_route_b

import ladon._proof_contract_planned_source_trace as trace
import ladon.proof_contract_planned_source as source
from ladon.proof_contract_obligation_planner import (
    ContractObligationPlanRequest,
    plan_contract_obligations,
)


def test_replan_expiry_stops_before_snapshot_verification(tmp_path, monkeypatch):
    plan = ContractObligationPlanRequest(**request_kwargs(route_a_route_b()))
    result = plan_contract_obligations(plan)
    index, row_index, identity = _selected_leaf(result)
    clock, verified = [100.0], []
    original = trace.plan_contract_obligations

    def expires_during_replan(value):
        fresh = original(value)
        clock[0] = 102.0
        return fresh

    monkeypatch.setattr(trace, 'plan_contract_obligations', expires_during_replan)
    monkeypatch.setattr(source.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(source, 'verify_formal_snapshot',
                        lambda *_args: verified.append(True))
    request = {'repoRoot': tmp_path, 'parentSnapshot': None, 'providerSnapshot': None,
               'parentReadingId': plan.desired_reading_identity['readingId'],
               'providerReadingId': 'reading:provider', 'planRequest': plan,
               'planResult': result, 'routeIndex': index, 'requirementIndex': row_index,
               'selectedIdentity': identity,
               'deadlineMonotonic': 101.0,
               'limits': {'timeout_seconds': 30, 'max_output_bytes': 8 * 1024**2,
                          'max_rss_bytes': 12 * 1024**3}}
    output = source.instantiate_planned_source_leaf_requirement(request)
    assert output['status'] == 'incomplete'
    assert verified == []
    assert output.get('capture') is None
    assert output['planVerified'] is True
    assert output['sourceBindingVerified'] is False


def _selected_leaf(result):
    index = next(i for i, r in enumerate(result['routeComparisons']) if r['describedRoute'])
    route = result['routeComparisons'][index]
    row_index = next(i for i, r in enumerate(route['backwardRequirements'])
                     if r['forwardContractRef']['kind'] == 'contract')
    row = route['backwardRequirements'][row_index]
    keys = ('stepRef', 'witnessRef', 'branchRef', 'branchIndex', 'premiseOrdinal',
            'forwardContractRef', 'statementRef', 'parentWitnessRef', 'interfaceId')
    return index, row_index, {'routeId': route['routeId']} | {k: row[k] for k in keys}
