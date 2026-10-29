"""Bounded exact JSON job transport; decoding confers no semantic authority."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ladon._bounded_json_graph import (
    build_graph,
    canonical,
    expanded_digest,
    preflight,
)
from ladon._bounded_json_graph import materialize as _materialize
from ladon.proof_contract_worker import _ensure_json_depth, _unique_json_object

_CAPS = {'max_wire_bytes': 8 * 1024**2, 'max_expanded_bytes': 32 * 1024**2,
         'max_depth': 272, 'max_string_bytes': 1024**2, 'max_nodes': 100_000,
         'max_edges': 500_000, 'max_expanded_nodes': 1_000_000}
_SCHEMA = 'ladon-bounded-json-dag-v1'
_KEYS = {'schema', 'root', 'nodes', 'expandedBytes', 'digest'}
_DIGEST = re.compile(r'^sha256:[0-9a-f]{64}$')


@dataclass(frozen=True)
class TransportLimits:
    """Lowerable limits for aggregate jobs, independent of native artifact limits."""

    max_wire_bytes: int = 8 * 1024**2
    max_expanded_bytes: int = 32 * 1024**2
    max_depth: int = 272
    max_string_bytes: int = 1024**2
    max_nodes: int = 100_000
    max_edges: int = 500_000
    max_expanded_nodes: int = 1_000_000

    def __post_init__(self):
        for name, maximum in _CAPS.items():
            value = getattr(self, name)
            if type(value) is not int or not 0 < value <= maximum:
                raise ValueError(f'invalid transport limit: {name}')


_DEFAULT_LIMITS = TransportLimits()


def _limits(value):
    if type(value) is not TransportLimits:
        raise TypeError('transport requires explicit TransportLimits')
    value.__post_init__()


def pack_json(value, *, limits=_DEFAULT_LIMITS):
    """Preflight an exact object, then serialize its canonical interned graph."""
    _limits(limits)
    if type(value) is not dict:
        raise TypeError('transport root must be an object')
    nodes, root, metric = build_graph(value, limits)
    wire = canonical({'schema': _SCHEMA, 'root': root, 'nodes': nodes,
                      'expandedBytes': metric.size, 'digest': expanded_digest(nodes, root)})
    if len(wire) > limits.max_wire_bytes:
        raise ValueError('transport wire exceeds byte limit')
    return wire


def _nonfinite(_value):
    raise ValueError('transport numbers must be finite')


def _parse(raw, limits):
    if type(raw) is not bytes:
        raise TypeError('transport wire must be bytes')
    if not raw or len(raw) > limits.max_wire_bytes:
        raise ValueError('transport wire exceeds byte limit')
    try:
        text = raw.decode('ascii')
        _ensure_json_depth(text, 8)
        value = json.loads(text, object_pairs_hook=_unique_json_object, parse_constant=_nonfinite)
    except (UnicodeError, ValueError, RecursionError) as error:
        raise ValueError('transport wire is not unambiguous bounded ASCII JSON') from error
    if type(value) is not dict or set(value) != _KEYS or value['schema'] != _SCHEMA:
        raise ValueError('invalid transport header')
    if canonical(value) != raw:
        raise ValueError('transport wire is not canonical')
    return value


def _header(value, metric):
    size = value['expandedBytes']
    if type(size) is not int or size != metric.size:
        raise ValueError('transport expanded byte length mismatch')
    digest = value['digest']
    if type(digest) is not str or not _DIGEST.fullmatch(digest):
        raise ValueError('transport digest shape invalid')


def unpack_json(raw, *, limits=_DEFAULT_LIMITS):
    """Validate the complete graph and expansion budget before allocating a tree."""
    _limits(limits)
    value = _parse(raw, limits)
    nodes, root = value['nodes'], value['root']
    metric = preflight(nodes, root, limits)
    _header(value, metric)
    if expanded_digest(nodes, root) != value['digest']:
        raise ValueError('transport expanded digest mismatch')
    return _materialize(nodes, root)
