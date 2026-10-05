"""Omission references must point to supplied source data, not invented fields."""
import copy

from test_result_assessments import assessment, companion, manifest
from test_result_checking import check_inputs, seal, target_owned_by_check

from ladon.result_inspection import inspect_result_manifest


def test_omitted_component_assessments_reference_companion():
    value = manifest()
    rows = [{**assessment(value['claims'][0], 'implication', targets=['finite-map']), 'id': f'a-{i}'}
            for i in range(15)]
    result = inspect_result_manifest(value, [], assessments=companion(value, rows))
    card = result['rows'][0]
    omission = next(row for row in card['fieldOmissions'] if row['path'] == '/assessments')
    assert omission['reference']['input'] == 'assessments'
    assert omission['reference']['pointer'] == '/assessments'


def test_omitted_check_bindings_reference_manifest_targets():
    value = manifest()
    artifacts = check_inputs()
    target_owned_by_check(value, artifacts)
    original = value['targets'][0]
    value['targets'] = [{**copy.deepcopy(original), 'id': f'target-{i}'} for i in range(20)]
    value['links'][0]['targetIds'] = [t['id'] for t in value['targets']]
    value['reviews'] = []
    seal(value)
    result = inspect_result_manifest(value, artifacts, section='checking')
    omission = next(row for row in result['rows'][0]['fieldOmissions'] if row['path'] == '/targetBindings')
    assert omission['reference']['input'] == 'manifest'
    assert omission['reference']['revision'] == value['revision']
    assert omission['reference']['pointer'] == '/targets'
    selected = inspect_result_manifest(value, artifacts, section='checking', target_id='target-19')
    assert selected['rows'][0]['targetBindings'][0]['targetId'] == 'target-19'
