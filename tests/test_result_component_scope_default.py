"""Default component reading and large sibling populations keep scope visible."""
from test_result_assessments import manifest

from ladon.result_inspection import inspect_result_manifest
from ladon.result_inspection_page import text_projection
from ladon.result_manifest_io import canonical_json, content_revision


def test_default_component_pages_label_each_whole_claim_context():
    value = manifest()
    rows = inspect_result_manifest(value, [])['rows']
    assert len(rows) == 2
    for row in rows:
        assert row['statementScope'] == 'whole-claim-context'
        assert row['wholeClaimStatement'] == value['claims'][0]['statement']
        assert row['claimComponentCoverage']['mapped'] == 1
        assert row['claimComponentCoverage']['unmapped'] == 1
        assert row['componentScope']['status'] == 'unavailable'


def test_large_sibling_omission_reference_includes_unmapped_components():
    value = manifest()
    claim = value['claims'][0]
    claim['components'] = ['implication'] + [f'unmapped-{i}' for i in range(999)]
    claim['revision'] = content_revision('claim', claim)
    value['revision'] = content_revision('manifest', value)
    result = inspect_result_manifest(value, [], claim_id=claim['id'], component_id='implication')
    row = result['rows'][0]
    coverage = row['claimComponentCoverage']
    assert coverage['mapped'] == 1 and coverage['unmapped'] == 999
    omission = next(item for item in row['fieldOmissions']
                    if item['path'] == '/claimComponentCoverage/components')
    assert omission['omittedRows'] == 1000 - len(coverage['components'])
    assert omission['reference']['input'] == 'manifest'
    assert omission['reference']['pointer'] == '/claims/0/components'
    assert len(canonical_json(result)) + 1 <= 32768
    assert len(text_projection(result).encode()) + 1 <= 32768
