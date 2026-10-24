"""Planner bounds apply to executed work and shared DAGs retain occurrences."""

import sys

from support.proof_contract_obligation_planner import (
    composition_case,
    request_kwargs,
    route_a_route_b,
    run_forward,
)
from support.proofir_v3_native import ref
from test_proof_contract_propagation import (
    _binding,
    _contract,
    _derivation,
    _interface,
    _scope,
    _step,
)


def _api():
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )
    return ContractObligationPlanRequest, plan_contract_obligations


def test_executed_backward_transform_calls_stay_within_remaining_step_budget():
    from ladon.proof_contract_obligations import transform_backward_sufficient

    request_type, plan = _api()
    case = route_a_route_b()
    used = run_forward(case)['coverage']['counts']['steps']
    values = request_kwargs(case, bounds={'maxEvaluatedSteps': used + 1})
    calls = []
    target_code = transform_backward_sufficient.__code__

    def observe(frame, event, _arg):
        if event == 'call' and frame.f_code is target_code:
            calls.append(1)

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        result = plan(request_type(**values))
    finally:
        sys.setprofile(previous)
    assert len(calls) <= 1
    assert result['coverage']['workBudget']['totalSteps'] <= used + 1
    assert result['coverage']['pendingBranches'] or result['coverage']['unvisitedApplications']


def _shared_case(depth):
    source = _contract('shared-source', offset=3, dependencies=())
    evidence = ref('check-run', 'check:interface')
    parameters = {key: [evidence] for key in ('leftEmbeddingRefs', 'rightEmbeddingRefs', 'nestednessRefs')}
    steps = []
    parent = 'shared-source'
    for index in range(depth):
        output = 'goal' if index == depth - 1 else f'mid:{index}'
        steps.append(_step(f'shared:{index}', [parent, parent], output))
        parent = output
    return {
        'graph': _derivation(steps), 'artifacts': [source], 'steps': steps,
        'interfaces': [_interface('out'), _interface('in', contract=source)],
        'scopes': [_scope(source, statement='shared-source')],
        'bindings': [_binding(step, rule_id='combine-estimates', arity=2, parameters=parameters)
                     for step in steps],
        'desired': source['payload']['record'], 'goalRef': ref('statement', 'goal'),
        'routeASteps': [step['stepRef'] for step in steps], 'routeBSteps': [],
    }


def test_repeated_shared_subproofs_keep_one_dag_route_and_ordered_occurrences():
    request_type, plan = _api()
    depth = 6
    case = _shared_case(depth)
    result = plan(request_type(**request_kwargs(case)))
    described = next(row for row in result['routeComparisons'] if row['describedRoute'])
    assert described['stepRefs'] == case['routeASteps']
    assert len(described['backwardRequirements']) <= 2 * depth
    assert described['endpoint']['status'] == 'conditional-profile-support'


def test_all_selected_backward_split_branches_are_retained_or_explicitly_pending():
    request_type, plan = _api()
    case = composition_case()
    choices = [{'stepRef': case['routeASteps'][0], 'choices': {'lossSplits': [[0, 3], [1, 2]]}}]
    result = plan(request_type(**request_kwargs(case, backward_choices=choices)))
    rows = result['routeComparisons'][0]['backwardRequirements']
    branches = {}
    for row in rows:
        branches.setdefault(row['branchRef'], []).append(row)
    offsets = {tuple(row['contractRecord']['features']['regularity']['offset']
                     for row in sorted(group, key=lambda item: item['premiseOrdinal']))
               for group in branches.values()}
    assert offsets == {(0, 3), (1, 2)}
