"""Exact JSON graph transport and rejection before untrusted expansion."""

import hashlib
import json
from dataclasses import fields

import pytest

from ladon import bounded_json_transport as api


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def graph(nodes, *, value=None, root=None):
    value = {'x': True} if value is None else value
    payload = canonical(value)
    return {'schema': 'ladon-bounded-json-dag-v1', 'root': len(nodes)-1 if root is None else root,
            'nodes': nodes, 'expandedBytes': len(payload),
            'digest': 'sha256:' + hashlib.sha256(payload).hexdigest()}


def basic():
    return graph([['scalar', True], ['object', ['x'], [0]]])


def test_lossless_roundtrip_preserves_types_unicode_large_integers_and_negative_zero():
    value = {'x': [None, True, False, 1, 1.0, -0.0, 2**80, 'λ雪', {'a': []}],
             'nested-json': '{"opaque": true}'}
    encoded = api.pack_json(value)
    restored = api.unpack_json(encoded)
    assert canonical(restored) == canonical(value)
    assert type(restored['x'][3]) is int and type(restored['x'][4]) is float
    assert restored['nested-json'] == value['nested-json']
    assert api.pack_json(restored) == encoded


def test_interned_mutable_owners_are_independent_after_decode():
    shared = {'claims': [1, 2]}
    value = {'authored': shared, 'formal': shared}
    encoded = api.pack_json(value)
    restored = api.unpack_json(encoded)
    assert restored == value
    assert restored['authored'] is not restored['formal']
    restored['authored']['claims'].append(3)
    assert restored['formal']['claims'] == [1, 2]
    nodes = json.loads(encoded)['nodes']
    assert len(nodes) < 10


@pytest.mark.parametrize('reference', [True, False, -1, 1, 2, 0.0, '0', None])
def test_refs_are_strict_backward_integers(reference):
    value = basic()
    value['nodes'][-1][2] = [reference]
    with pytest.raises((ValueError, TypeError)):
        api.unpack_json(canonical(value))


@pytest.mark.parametrize('node', [
    ['unknown', True], ['scalar', []], ['scalar', {}], ['scalar', True, False],
    ['array', '0'], ['object', ['x', 'x'], [0, 0]], ['object', ['z', 'a'], [0, 0]],
    ['object', ['x'], []], ['object', [False], [0]], ['object', ['x'], [0], 'extra'],
])
def test_malformed_nodes_are_rejected(node):
    value = basic()
    value['nodes'][-1] = node
    with pytest.raises((ValueError, TypeError)):
        api.unpack_json(canonical(value))


@pytest.mark.parametrize('key,bad', [('schema', 'unknown'), ('root', True), ('root', 0),
                                   ('expandedBytes', True), ('expandedBytes', 1),
                                   ('digest', 'sha256:' + '0'*64)])
def test_forged_headers_are_rejected(key, bad):
    value = basic()
    value[key] = bad
    with pytest.raises((ValueError, TypeError)):
        api.unpack_json(canonical(value))


def test_unknown_header_and_duplicate_json_keys_are_rejected():
    value = basic()
    value['authority'] = 'admitted'
    with pytest.raises(ValueError):
        api.unpack_json(canonical(value))
    encoded = canonical(basic())
    with pytest.raises(ValueError):
        api.unpack_json(b'{"root":999,' + encoded[1:])
    with pytest.raises(ValueError):
        api.unpack_json(encoded + b' ')


@pytest.mark.parametrize('nodes,value', [
    ([['scalar', False], ['scalar', True], ['object', ['x'], [1]]], {'x': True}),
    ([['scalar', True], ['scalar', True], ['object', ['x', 'y'], [0, 1]]], {'x': True, 'y': True}),
    ([['scalar', False], ['scalar', True], ['object', ['x', 'y'], [1, 0]]], {'x': True, 'y': False}),
    ([['scalar', True], ['array', [0]]], {'x': True}),
])
def test_orphans_duplicates_noncanonical_order_and_nonobject_root_reject(nodes, value):
    with pytest.raises(ValueError):
        api.unpack_json(canonical(graph(nodes, value=value)))


def forbidden_expansion(*_args):
    raise AssertionError('tree materialization occurred before preflight rejection')


def test_exponential_wire_graph_is_rejected_before_materialization(monkeypatch):
    nodes = [['scalar', None]]
    for index in range(60):
        nodes.append(['array', [index, index]])
    nodes.append(['object', ['x'], [60]])
    monkeypatch.setattr(api, '_materialize', forbidden_expansion)
    with pytest.raises(ValueError):
        api.unpack_json(canonical(graph(nodes)))


def test_encoder_preflights_exponential_shared_python_graph():
    value = None
    for _ in range(60):
        value = [value, value]
    with pytest.raises(ValueError):
        api.pack_json({'x': value})


@pytest.mark.parametrize('kind', ['list', 'object'])
def test_python_cycles_are_rejected(kind):
    value = [] if kind == 'list' else {}
    if kind == 'list':
        value.append(value)
    else:
        value['self'] = value
    with pytest.raises(ValueError):
        api.pack_json({'x': value})


@pytest.mark.parametrize('scalar', [float('nan'), float('inf'), float('-inf'), {1, 2}, b'bytes'])
def test_non_json_and_nonfinite_python_values_reject(scalar):
    with pytest.raises((ValueError, TypeError)):
        api.pack_json({'x': scalar})


def test_nonfinite_wire_scalar_rejects():
    encoded = canonical(basic()).replace(b'["scalar",true]', b'["scalar",1e999]')
    with pytest.raises(ValueError):
        api.unpack_json(encoded)


@pytest.mark.parametrize('name', [field.name for field in fields(api.TransportLimits)])
def test_limits_only_narrow_fixed_profile(name):
    default = getattr(api.TransportLimits(), name)
    for bad in [0, -1, True, 1.0, default + 1]:
        with pytest.raises((ValueError, TypeError)):
            api.TransportLimits(**{name: bad})


def test_expanded_and_wire_exact_byte_ceilings():
    value = {'x': [1, 2, 3]}
    encoded = api.pack_json(value)
    limits = api.TransportLimits(max_expanded_bytes=len(canonical(value)), max_wire_bytes=len(encoded))
    assert canonical(api.unpack_json(api.pack_json(value, limits=limits), limits=limits)) == canonical(value)
    with pytest.raises(ValueError):
        api.pack_json(value, limits=api.TransportLimits(max_expanded_bytes=len(canonical(value))-1))
    with pytest.raises(ValueError):
        api.unpack_json(encoded, limits=api.TransportLimits(max_expanded_bytes=len(canonical(value))-1))
    with pytest.raises(ValueError):
        api.unpack_json(encoded, limits=api.TransportLimits(max_wire_bytes=len(encoded)-1))


def test_depth_edges_nodes_and_occurrences_are_counted_before_expansion(monkeypatch):
    value = {'x': [[True], [True]]}
    encoded = api.pack_json(value)
    monkeypatch.setattr(api, '_materialize', forbidden_expansion)
    limits = [api.TransportLimits(max_depth=2), api.TransportLimits(max_edges=1),
              api.TransportLimits(max_nodes=2), api.TransportLimits(max_expanded_nodes=3)]
    for limit in limits:
        with pytest.raises(ValueError):
            api.unpack_json(encoded, limits=limit)


def test_utf8_string_bound_is_separate_from_escaped_expansion():
    value = {'x': 'é'}
    encoded = api.pack_json(value, limits=api.TransportLimits(max_string_bytes=2))
    assert api.unpack_json(encoded)['x'] == 'é'
    with pytest.raises(ValueError):
        api.pack_json(value, limits=api.TransportLimits(max_string_bytes=1))


def test_input_types_and_object_key_types_are_closed():
    for value in [[], None, {'x': (1, 2)}, {1: True}, {'x': '\ud800'}]:
        with pytest.raises((ValueError, TypeError)):
            api.pack_json(value)
    with pytest.raises((ValueError, TypeError)):
        api.unpack_json('{}')
