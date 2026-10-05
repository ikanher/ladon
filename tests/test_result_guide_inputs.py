from __future__ import annotations

import copy
import hashlib
import json
from importlib.resources import files

import pytest
from support.result_guide import guide_inputs, reseal, revision


def _api():
    from ladon.result_guide_inputs import guide_revision, validate_result_guide
    return guide_revision, validate_result_guide


def test_valid_companion_uses_domain_separated_revisions_and_returns_detached_data():
    manifest, _, guide = guide_inputs()
    guide_revision, validate = _api()
    assert guide_revision('step', guide['steps'][0]) == guide['steps'][0]['revision']
    assert guide_revision('citation', guide['citations'][0]) == guide['citations'][0]['revision']
    assert guide_revision('step', guide['steps'][0]) != guide_revision('citation', guide['steps'][0])
    checked = validate(guide, manifest)
    checked['steps'][0]['explanation'] = 'caller mutation'
    assert guide['steps'][0]['explanation'] != 'caller mutation'


@pytest.mark.parametrize('mutation', [
    lambda g: g['steps'][1]['prerequisites'][0].update(stepId='missing'),
    lambda g: g['steps'][0]['targetRevisions'][0].update(targetId='missing'),
    lambda g: g['citations'][0].update(stepId='missing'),
    lambda g: g['reviews'][0].update(scope='attribution'),
    lambda g: g['steps'][1]['prerequisites'][0].update(stepId='argument'),
])
def test_dangling_wrong_scope_self_and_duplicate_rows_are_rejected(mutation):
    manifest, _, guide = guide_inputs()
    broken = copy.deepcopy(guide)
    mutation(broken)
    reseal(broken)
    with pytest.raises((ValueError, TypeError)):
        _api()[1](broken, manifest)


@pytest.mark.parametrize('mutation', [
    lambda g: g['steps'][1]['targetRevisions'].append(copy.deepcopy(g['steps'][1]['targetRevisions'][0])),
    lambda g: g['citations'].append(copy.deepcopy(g['citations'][0])),
    lambda g: g['steps'][1].update(id='condition'),
    lambda g: g['steps'][0].update(explanation='x' * 65537),
    lambda g: g['steps'][0]['sources'].clear(),
])
def test_duplicate_identities_and_contract_boundaries_fail_closed(mutation):
    manifest, _, guide = guide_inputs()
    broken = copy.deepcopy(guide)
    mutation(broken)
    reseal(broken)
    with pytest.raises((ValueError, TypeError)):
        _api()[1](broken, manifest)


def test_revision_tampering_and_closed_schema_shape_are_rejected():
    manifest, _, guide = guide_inputs()
    broken = copy.deepcopy(guide)
    broken['steps'][0]['revision'] = 'sha256:' + '0' * 64
    with pytest.raises((ValueError, TypeError)):
        _api()[1](broken, manifest)
    broken = copy.deepcopy(guide)
    broken['steps'][0]['unrecognized'] = True
    with pytest.raises((ValueError, TypeError)):
        _api()[1](broken, manifest)


def test_schema_is_packaged_and_declares_closed_companion_objects():
    schema_path = files('ladon.schemas').joinpath('ladon-result-guide-v1.schema.json')
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    assert schema['additionalProperties'] is False
    assert {'schema', 'resultId', 'manifestRevision', 'steps', 'citations', 'reviews'} <= set(schema['required'])
    assert schema['properties']['steps']['maxItems'] == 10000
    assert schema['properties']['citations']['maxItems'] == 10000


def test_domain_hash_uses_utf8_and_the_actual_nul_separator():
    row = {'id': 'é', 'explanation': 'π', 'revision': 'ignored'}
    expected = 'sha256:' + hashlib.sha256(b'ladon-result-guide-v1/step\0' +
        json.dumps({'id': 'é', 'explanation': 'π'}, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()
    assert revision('step', row) == expected
    assert _api()[0]('step', row) == expected
