"""A clipped formal type advertises the required input and target arguments."""
from ladon.result_inspection_page import compact_row


def test_type_excerpt_route_is_a_complete_explicit_template():
    row = {'supportingStatements': [{'targetId': 'fixture-target', 'typeText': 'α' * 20000}],
           'references': {'/supportingStatements/0/typeText': {
               'input': 'manifest', 'pointer': '/targets/0/typeText', 'revision': 'fixture'}}}
    value = compact_row(row, profile='exposition')
    text = value['supportingStatements'][0]['typeText']
    assert 'EXCERPT' in text
    assert 'ladon result inspect INPUT --section targets --target TARGET_ID --format json' in text
    assert 'Replace INPUT' in text and 'shown targetId' in text
    omission = next(r for r in value['fieldOmissions'] if r['path'].endswith('/typeText'))
    assert omission['reference']['pointer'] == '/targets/0/typeText'
