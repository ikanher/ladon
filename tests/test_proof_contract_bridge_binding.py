"""Per-goal binding propagation, using synthetic bookkeeping subjects only."""
import hashlib
import json

from test_proof_contract_bridge_demand import _construction

from ladon._proof_contract_bridge_goals import bridge_goals, bridge_interpretation
from ladon._proof_contract_bridge_preparation import _selected_demand


def test_all_goal_bindings_own_exact_full_demand_and_independent_digest():
    construction = _construction()
    demand = _selected_demand(construction)
    digest = 'sha256:'+hashlib.sha256(json.dumps(demand, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()
    construction.update(selectedDemand=demand, selectedDemandDigest=digest,
                        selectedIdentity={'routeId': 'route'})
    record = bridge_interpretation(
        {'contractRecord': {'features': {'regularity': {'offset': 0}}}},
        {'leftOperator': 'T.out', 'inputScale': 'T.inp', 'map': 'T.map',
         'constantName': 'T.C'}, {'path': 'generated.txt'})
    prepared = {'interpretation': record, 'obligations': [
        {'id': 'object-map', 'kind': 'representation-transport', 'goal': 'typed map'},
        {'id': 'conclusion', 'kind': 'conclusion-transfer', 'goal': 'transfer'}]}
    goals = bridge_goals(prepared, construction)
    assert len(goals) == 4
    for goal in goals:
        assert goal['binding']['selectedDemand'] == demand
        assert goal['binding']['selectedDemandDigest'] == digest
        assert [o['premiseOrdinal'] for o in goal['binding']['selectedDemand']['incomingOccurrences']] == [0, 1]
    goals[0]['binding']['selectedDemand']['incomingOccurrences'].clear()
    assert len(goals[1]['binding']['selectedDemand']['incomingOccurrences']) == 2
    assert len(demand['incomingOccurrences']) == 2
