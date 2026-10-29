"""Receipt transport is reversible and cannot carry noncanonical float tags."""

import copy
import json

import pytest

from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_native_analysis_codec import decode_replay, encode_replay


def test_receipt_timings_survive_native_json_without_rounding():
    productions = [{'authority': 'none', 'snapshotId': '', 'elapsed': 0.1},
                   {'authority': 'none', 'snapshotId': '', 'elapsed': -0.0}]
    for production in productions:
        production['snapshotId'] = snapshot_identity(production)
    run = {'budget': 599.9999999999999}
    encoded = encode_replay(productions, run)
    assert decode_replay(json.loads(json.dumps(encoded))) == (productions, run)
    assert encoded['productions'][1]['elapsed'] == {'$realBoundFloat': '-0x0.0p+0'}


@pytest.mark.parametrize('tag', ['nan', 'inf', '0x1.0p+9999999', '0x1.00p+0', 1])
def test_invalid_receipt_scalar_fails_closed(tag):
    original = [{'authority': 'none'}, {'authority': 'none'}]
    for production in original:
        production['snapshotId'] = snapshot_identity(production)
    encoded = encode_replay(original, {})
    encoded['relationRun'] = {'timing': {'$realBoundFloat': tag}}
    with pytest.raises(ValueError):
        decode_replay(encoded)


def test_reserved_tag_cannot_be_injected_from_an_ordinary_receipt():
    with pytest.raises(ValueError):
        encode_replay([], {'$realBoundFloat': '0x1.0p+0'})


def test_encoded_owner_identity_is_checked_before_decoding():
    productions = [{'authority': 'none'}, {'authority': 'none'}]
    encoded = encode_replay(productions, {})
    changed = copy.deepcopy(encoded)
    changed['productions'][0]['unexpected'] = True
    with pytest.raises(ValueError):
        decode_replay(changed)
