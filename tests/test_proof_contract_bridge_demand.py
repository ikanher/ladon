"""Demand lookup bookkeeping preserves every repeated incoming occurrence."""
import copy

import pytest

from ladon._contract_propagation_budget import fingerprint


def _construction():
    record = {'pure': 'bookkeeping'}
    demand = {'demandId': 'demand', 'witnessRef': 'witness',
              'outputContractDigest': 'sha256:'+fingerprint(record).hex(),
              'status': 'requires-source-check', 'incomingOccurrences': [
                  {'parentDemandId': 'parent', 'branchRef': 'branch', 'premiseOrdinal': i}
                  for i in range(2)]}
    return {'selectedRouteId': 'route',
        'selectedRequirement': {'parentWitnessRef': 'witness', 'contractRecord': record},
        'routeComparisons': [{'routeId': 'route', 'obligationBundle': {'demands': [demand]}}]}


def test_demand_binding_retains_repeated_occurrences_and_owns_copy():
    from ladon._proof_contract_bridge_preparation import _selected_demand
    construction = _construction()
    demand = _selected_demand(construction)
    assert [o['premiseOrdinal'] for o in demand['incomingOccurrences']] == [0, 1]
    demand['incomingOccurrences'].clear()
    assert len(_selected_demand(construction)['incomingOccurrences']) == 2


@pytest.mark.parametrize('field', ['witnessRef', 'outputContractDigest', 'status'])
def test_drift_cannot_select_a_different_demand(field):
    from ladon._proof_contract_bridge_preparation import _selected_demand
    construction = copy.deepcopy(_construction())
    construction['routeComparisons'][0]['obligationBundle']['demands'][0][field] = 'different'
    with pytest.raises(ValueError):
        _selected_demand(construction)
