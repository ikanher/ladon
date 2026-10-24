"""A valid local bridge does not acquire a spurious whole-goal mismatch."""
from support.proof_contract_obligation_planner import request_kwargs, unknown_feature_case
from test_proof_contract_obligation_planner_branches import _two_branch_case


def _plan(values):
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )
    return plan_contract_obligations(ContractObligationPlanRequest(**values))


def test_valid_distinct_premises_have_no_spurious_intermediate_mismatch_rows():
    case = _two_branch_case()
    choices = [{'stepRef': case['routeASteps'][-1], 'choices': {'lossSplits': [[1, 2]]}}]
    result = _plan(request_kwargs(case, backward_choices=choices))
    comparisons = result['routeComparisons'][0]['comparisons']
    intermediates = [row for row in comparisons
                     if row['statementRef']['localId'] in {'left-mid', 'right-mid'}]
    assert intermediates
    assert all(row['status'] == 'profile-related' for row in intermediates)
    assert all(row['mismatchDimensions'] == [] for row in intermediates)


def test_unknown_comparison_is_unresolved_rather_than_a_candidate_mismatch():
    result = _plan(request_kwargs(unknown_feature_case()))
    rows = result['routeComparisons'][0]['comparisons']
    unknown = [row for row in rows if row['comparison']['relation'] == 'unknown']
    assert unknown
    assert all(row['status'] == 'unresolved-bridge' for row in unknown)
