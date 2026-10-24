"""Pure lowering controls; these dictionaries are not Lean observations."""
import importlib


def _api():
    return importlib.import_module('ladon._proof_contract_bridge_goals')


def test_derived_offset_is_selected_requirement_not_provider():
    selected = {'contractRecord': {'features': {'regularity': {'offset': 0}}}}
    symbols = {'leftOperator': 'T.out', 'inputScale': 'T.input', 'map': 'T.map',
               'constantName': 'T.C', 'offset': 2}
    record = _api().bridge_interpretation(selected, symbols, {'path': 'derived.txt'})
    body = record['formula']['body']['body']
    assert body['right']['args'][1]['args'][0]['args'][1] == {'tag': 'const', 'name': '0'}
    assert record['symbols']['coefficient']['leanName'] == 'T.C'
    assert record['source']['path'] == 'derived.txt'


def test_goal_channels_are_separate_and_do_not_add_desired_assumption():
    selected = {'contractRecord': {'features': {'regularity': {'offset': 0}}}}
    symbols = {'leftOperator': 'T.out', 'inputScale': 'T.input', 'map': 'T.map',
               'constantName': 'T.C', 'offset': 2}
    record = _api().bridge_interpretation(selected, symbols, {'path': 'derived.txt'})
    prepared = {'interpretation': record, 'obligations': [
        {'id': 'object-map', 'kind': 'representation-transport', 'goal': 'typed map'},
        {'id': 'conclusion', 'kind': 'conclusion-transfer', 'goal': 'actual transfer'}]}
    construction = {'selectedIdentity': {'routeId': 'route-a'},
                    'backwardRequestDigest': 'sha256:original', 'desiredReadingId': 'original'}
    goals = _api().bridge_goals(prepared, construction)
    assert [g['id'] for g in goals] == ['source-requirement', 'domain', 'object-map', 'conclusion']
    assert len({g['kind'] for g in goals}) == 4
    assert goals[0]['goal'].startswith('(∀')
    assert '→' not in goals[0]['goal'].split('(_root_.T.out')[0]
    assert goals[1]['transportProfile'] == 'universal-nat-identity-v1'
    assert goals[2]['goal'] == 'typed map'
    assert goals[3]['goal'] == 'actual transfer'
    assert all(g['binding']['selectedIdentity'] == construction['selectedIdentity'] for g in goals)
    assert len({g['goalDigest'] for g in goals}) == 4
