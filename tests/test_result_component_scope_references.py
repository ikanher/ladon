"""Clipped derived coverage and multiple mapping contributors stay recoverable."""
import copy

from test_result_assessments import manifest

from ladon.result_inspection import inspect_result_manifest
from ladon.result_manifest_io import content_revision


def _multiple_targets():
    value = manifest()
    original = value['targets'][0]
    for index in range(12):
        target = {**copy.deepcopy(original), 'id': f'extra-{index}'}
        target['revision'] = content_revision('target', target)
        value['targets'].append(target)
    return value


def test_clipped_coverage_target_ids_refer_to_mapping_population():
    value = _multiple_targets()
    value['links'][0]['targetIds'] = [row['id'] for row in value['targets']]
    value['revision'] = content_revision('manifest', value)
    result = inspect_result_manifest(value, [], claim_id='paper-theorem-1', component_id='implication')
    omission = next(row for row in result['rows'][0]['fieldOmissions']
                    if row['path'] == '/claimComponentCoverage/components/0/targetIds')
    assert omission['reference']['input'] == 'manifest'
    assert omission['reference']['pointer'] == '/links'
    assert omission['reference'].get('appendPath', False) is False


def test_component_retains_each_mapping_contributor_with_exact_references():
    value = _multiple_targets()
    value['links'].append({**copy.deepcopy(value['links'][0]), 'id': 'second-link',
                           'targetIds': ['extra-0']})
    value['revision'] = content_revision('manifest', value)
    row = inspect_result_manifest(value, [], claim_id='paper-theorem-1', component_id='implication')['rows'][0]
    assert row['mapping']['targetIds'] == ['extra-0', 'finite-map']
    sources = row['mappingSources']
    assert [source['id'] for source in sources] == ['mapping-1', 'second-link']
    assert [source['targetIds'] for source in sources] == [['finite-map'], ['extra-0']]
    assert [source['references']['']['pointer'] for source in sources] == ['/links/0', '/links/1']
    assert all(source['references']['']['input'] == 'manifest' for source in sources)
