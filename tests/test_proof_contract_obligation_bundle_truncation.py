"""A truncated AND alternative must name omitted premises explicitly."""
from ladon._proof_contract_obligation_bundle_walk import _append_branches


class RejectLeftChild:
    def reserve(self, value, **_kwargs):
        return value.get('witnessRef') != 'left'


def test_missing_child_budget_cannot_label_shortened_and_generated():
    parent = {'demandId': 'parent', 'alternatives': [], 'status': 'generated'}
    rows = [{'branchRef': 'branch', 'branchIndex': 0, 'premiseOrdinal': i,
             'contractRecord': {'control': i}} for i in range(2)]
    witness = {'premiseOccurrences': [{'parentWitnessRef': name} for name in ('left', 'right')]}
    witnesses = {name: {'sourceContractRef': {'localId': name}} for name in ('left', 'right')}
    bundle, index, queue, pending = {'demands': []}, {}, [], []
    stopped = _append_branches(parent, rows, witness, witnesses, 'route', bundle,
                               index, RejectLeftChild(), queue, pending)
    assert stopped is True
    branch = parent['alternatives'][0]
    _assert_truncated_branch(branch)
    assert parent['status'] == 'partial'
    assert pending


def _assert_truncated_branch(branch):
    assert branch['status'] == 'partial'
    assert branch['expectedPremiseOrdinals'] == [0, 1]
    assert branch['pendingPremiseOrdinals'] == [0]
    assert [r['premiseOrdinal'] for r in branch['requirements']] == [1]
