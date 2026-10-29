"""Independent threshold and generation controls for bounded job transport."""

import json
import random

import pytest
from test_bounded_json_transport import canonical, forbidden_expansion

from ladon import bounded_json_transport as api
from ladon.proofir_v3 import canonical_bytes, validate_envelope_batch


def test_all_small_structural_limits_accept_their_exact_ceiling():
    value = {'x': [None, None]}
    encoded = api.pack_json(value)
    limits = api.TransportLimits(max_depth=2, max_nodes=3, max_edges=3,
                                 max_expanded_nodes=4, max_string_bytes=1,
                                 max_expanded_bytes=len(canonical(value)), max_wire_bytes=len(encoded))
    assert api.unpack_json(api.pack_json(value, limits=limits), limits=limits) == value


@pytest.mark.parametrize('value', [{'x': 'é'}, {'é': True}])
def test_decoder_checks_utf8_bounds_for_values_and_object_keys(value):
    encoded = api.pack_json(value)
    with pytest.raises(ValueError):
        api.unpack_json(encoded, limits=api.TransportLimits(max_string_bytes=1))


def test_default_depth_ceiling_and_one_beyond_it():
    value = True
    for _ in range(271):
        value = [value]
    original = {'x': value}
    assert canonical(api.unpack_json(api.pack_json(original))) == canonical(original)
    with pytest.raises(ValueError):
        api.pack_json({'x': [value]})


def test_default_utf8_string_ceiling_and_one_beyond_it():
    text = 'é' * (1024**2 // 2)
    encoded = api.pack_json({'x': text})
    assert api.unpack_json(encoded)['x'] == text
    with pytest.raises(ValueError):
        api.pack_json({'x': text + 'x'})


def test_escaped_bytes_match_dp_footprint():
    value = {'quote"\\\n': '"\\\n\r\t\x00é雪'}
    encoded = api.pack_json(value)
    assert json.loads(encoded)['expandedBytes'] == len(canonical(value))
    assert canonical(api.unpack_json(encoded)) == canonical(value)


def _random_value(rng, depth):
    leaves = [None, False, True, 2**80, -0.0, 1.0, -17, 1.25e-18, 'é雪"\\\n', '']
    if depth == 0 or rng.randrange(3) == 0:
        return rng.choice(leaves)
    if rng.randrange(2):
        return [_random_value(rng, depth-1) for _ in range(rng.randrange(5))]
    return {f'k{i}': _random_value(rng, depth-1) for i in range(rng.randrange(5))}


def test_seeded_generic_values_roundtrip_with_deterministic_key_order():
    rng = random.Random(90210)
    for _ in range(500):
        value = {'z': _random_value(rng, 5), 'a': _random_value(rng, 4)}
        encoded = api.pack_json(value)
        assert canonical(api.unpack_json(encoded)) == canonical(value)
        assert api.pack_json(dict(reversed(list(value.items())))) == encoded


def test_wire_bound_precedes_json_parsing(monkeypatch):
    monkeypatch.setattr(api.json, 'loads', forbidden_expansion)
    with pytest.raises(ValueError):
        api.unpack_json(b'x'*129, limits=api.TransportLimits(max_wire_bytes=128))


def test_transport_does_not_relax_native_artifact_validation():
    value = {'artifact': {'value': 1.5}, 'claimed': {'admission': 'admitted'}}
    restored = api.unpack_json(api.pack_json(value))
    assert canonical(restored) == canonical(value)
    with pytest.raises(ValueError):
        canonical_bytes(restored['artifact'])
    with pytest.raises(ValueError):
        validate_envelope_batch([restored['claimed']])
