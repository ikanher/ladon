"""Inspection must put the exact interpreted claim beside its formal application."""

import json

import pytest

from ladon.proofir_v3_queries import query_v3_correspondence
from tests.test_correspondence_query_coverage import REF, database

INTERPRETATION_OWNER = 'sha256:' + 'b' * 64
RECORD = {'id': 'i', 'source': {'quote': '∀ état'}, 'formula': {'tag': 'opaque'}}


def context_database():
    db = database()
    for owner, record in [(INTERPRETATION_OWNER, RECORD), ('sha256:' + 'c' * 64, {'wrong': True})]:
        db.execute('INSERT INTO proofir_v3_interpretations VALUES(?,?,?,?,?,?,?,?,?)',
                   (owner, 'i', json.dumps(record, ensure_ascii=False), None,
                    'attributed-unreviewed', 'sha256:' + 'd' * 64, 'source-map', 's', '/'))
    db.execute('UPDATE proofir_v3_correspondences SET slice_json=?',
               (json.dumps({'selection': {'declaration': 'Original.theorem'}}),))
    return db


def test_exact_context_is_delivered_without_promoting_authority():
    result = query_v3_correspondence(context_database(), REF, limit=10)
    assert result['schema'] == 'ladon-native-correspondence-inspection-v2'
    assert result['context']['interpretation']['value']['record'] == RECORD
    assert result['context']['formalSlice']['value']['selection']['declaration'] == 'Original.theorem'
    assert result['context']['interpretation']['value']['loweredFormula'] is None
    assert result['coverage']['complete'] is True
    assert result['dimensions'] == {}
    assert result['authority'] == 'stored-evidence-only'
    assert {r['id'] for r in result['limitations']} >= {'attributed-source-mapping', 'historical-context'}


@pytest.mark.parametrize('missing', ['table', 'row', 'identity'])
def test_missing_exact_interpretation_is_explicit(missing):
    db = context_database()
    if missing == 'table':
        db.execute('DROP TABLE proofir_v3_interpretations')
    elif missing == 'row':
        db.execute('DELETE FROM proofir_v3_interpretations WHERE content_artifact_id=?',
                   (INTERPRETATION_OWNER,))
    else:
        db.execute('UPDATE proofir_v3_interpretations SET interpretation_id=? WHERE content_artifact_id=?',
                   ('other', INTERPRETATION_OWNER))
    result = query_v3_correspondence(db, REF, limit=10)
    assert result['context']['interpretation']['status'] == 'unavailable'
    assert result['coverage']['complete'] is False


def test_byte_bound_omits_whole_component_and_can_be_raised():
    db = context_database()
    full = query_v3_correspondence(db, REF, limit=10)
    size = full['context']['interpretation']['storedBytes']
    bounded = query_v3_correspondence(db, REF, limit=10, max_context_bytes=size - 1)
    component = bounded['context']['interpretation']
    assert component['status'] == 'omitted'
    assert component['reason'] == 'context-byte-limit'
    assert 'value' not in component
    assert bounded['coverage']['complete'] is False
    exact = query_v3_correspondence(db, REF, limit=10, max_context_bytes=size)
    assert exact['context']['interpretation']['value']['record'] == RECORD


@pytest.mark.parametrize('value', [0, -1, True, 8388609, 1.5, '65536'])
def test_invalid_context_allowance_is_rejected(value):
    with pytest.raises(ValueError, match='context'):
        query_v3_correspondence(database(), REF, limit=1, max_context_bytes=value)



def test_context_uses_utf8_bytes_before_loading_text():
    db = context_database()
    raw = json.dumps({'quote': 'é' * 1000}, ensure_ascii=False)
    db.execute('UPDATE proofir_v3_interpretations SET record_json=? WHERE content_artifact_id=?',
               (raw, INTERPRETATION_OWNER))
    # Enough characters, insufficient UTF-8 bytes, even before metadata is added.
    result = query_v3_correspondence(db, REF, limit=10, max_context_bytes=len(raw) + 200)
    component = result['context']['interpretation']
    assert component['status'] == 'omitted'
    assert component['storedBytes'] > len(raw.encode('utf-8'))
    assert 'value' not in component
