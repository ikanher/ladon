"""Freeze exact owner references, request grammar and byte-copy association."""

import copy
import json
from pathlib import Path

import pytest

from ladon.real_prose_connection_inputs import (
    REQUEST_SCHEMA,
    authored_owner,
    bound_inputs,
    connection_request,
    copy_relation,
    formal_owner,
    input_reference,
)

BASE = Path(__file__).parents[1] / 'openspec/changes'
FORMAL = BASE / 'ladon-real-bound-contracts/evidence/qualification-20261027/native/inverse_finiteJets-production.json'
AUTHORED = BASE / 'ladon-real-prose-contracts/evidence/authored-real-native-20261027/live/navier-produced.json'


def request():
    return {'schema': REQUEST_SCHEMA, 'term': 'by intro h; exact h', 'premises': []}


@pytest.fixture(scope='module')
def histories():
    return json.loads(FORMAL.read_text()), json.loads(AUTHORED.read_text())


def test_closed_request_retains_order_and_term():
    value = request()
    value['premises'] = ['Other.second', 'Other.first']
    assert connection_request(value) == value
    assert connection_request(value) is not value


@pytest.mark.parametrize('field,value', [('schema', 'unknown'), ('term', ''), ('term', True),
                                        ('term', 'x'*(1024**2+1)), ('premises', ['a', 'a']),
                                        ('premises', ['a']*17), ('premises', ['a; command']),
                                        ('premises', [False]), ('premises', None)])
def test_invalid_requests_reject(field, value):
    changed = request()
    changed[field] = value
    with pytest.raises((ValueError, TypeError)):
        connection_request(changed)


def test_unknown_request_authority_and_missing_fields_reject():
    value = request()
    value['admission'] = 'checked'
    with pytest.raises(ValueError):
        connection_request(value)
    del value['admission'], value['term']
    with pytest.raises(ValueError):
        connection_request(value)


def test_copy_relation_preserves_utf8_and_rejects_normalization():
    prefix = 'α\r\n'.encode()
    relation = copy_relation(prefix, prefix + 'β\n'.encode())
    assert relation['formalBytes'] == len(prefix)
    assert relation['helperImportLineOffset'] == 1
    with pytest.raises(ValueError):
        copy_relation(prefix, 'α\nβ\n'.encode())
    with pytest.raises(TypeError):
        copy_relation('α', prefix)


def test_full_input_digest_binds_more_than_claimed_snapshot_id():
    left = {'snapshotId': 'saved', 'extra': 1}
    right = {**left, 'extra': 2}
    assert input_reference(left)['snapshotId'] == input_reference(right)['snapshotId']
    assert input_reference(left)['digest'] != input_reference(right)['digest']


def test_recorded_pair_has_full_semantic_owners_and_exact_copy(histories):
    formal, authored = histories
    result = bound_inputs(formal, authored, request())
    assert result['inputs']['formal'] == input_reference(formal)
    assert result['inputs']['authored'] == input_reference(authored)
    assert result['owners']['authored']['request'] == authored['request']
    assert result['owners']['authored']['propositionExpr']
    assert result['association']['formalBytes'] == len(formal['sourceText'].encode())
    assert result['owners']['authored']['record']['admission'] == 'unresolved'


def test_owner_projections_reject_altered_productions(histories):
    formal, authored = histories
    bad_formal, bad_authored = copy.deepcopy(formal), copy.deepcopy(authored)
    bad_formal['sourceText'] += '\n'
    bad_authored['request']['alternativeId'] = 'another:identity'
    with pytest.raises(ValueError):
        formal_owner(bad_formal)
    with pytest.raises(ValueError):
        authored_owner(bad_authored)
