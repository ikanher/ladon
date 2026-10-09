"""Validate complete opaque Lean expression DAGs without interpreting terms."""
from __future__ import annotations

from ladon.source_association_io import _strict_json

PREFIX = 'ladon-expr-dag-v1:'
_MAX_NODES = 1_000_000
_LAYOUTS = {
    'bvar': 'n', 'fvar': 's', 'mvar': 's', 'sort': 's', 'const': 'ss',
    'app': 'rr', 'lam': 'ssrr', 'forallE': 'ssrr', 'letE': 'sbrrr',
    'lit': 's', 'mdata': 'sr', 'proj': 'snr',
}


def validate_structural_text(text: str) -> None:
    if not text.startswith('ladon-expr-dag-'):
        return  # Historical opaque repr fingerprints remain readable.
    if not text.startswith(PREFIX):
        raise ValueError('unsupported structural expression codec')
    value = _strict_json(text[len(PREFIX):])
    if not isinstance(value, dict) or set(value) != {'root', 'nodes'}:
        raise ValueError('expression graph fields are not closed')
    nodes = value['nodes']
    if not isinstance(nodes, list) or not 0 < len(nodes) <= _MAX_NODES:
        raise ValueError('expression graph node population is invalid')
    if type(value['root']) is not int or value['root'] != len(nodes) - 1:
        raise ValueError('expression graph root is not the final node')
    for index, node in enumerate(nodes):
        _validate_node(node, index)


def _validate_node(node, index: int) -> None:
    if not isinstance(node, list) or not node or not isinstance(node[0], str):
        raise ValueError('expression node is malformed')
    layout = _LAYOUTS.get(node[0])
    if layout is None or len(node) != len(layout) + 1:
        raise ValueError('expression constructor fields are invalid')
    for kind, value in zip(layout, node[1:], strict=True):
        _validate_field(kind, value, index)


def _validate_field(kind: str, value, index: int) -> None:
    if kind == 's':
        valid = isinstance(value, str) and bool(value)
    elif kind == 'b':
        valid = type(value) is bool
    else:
        valid = type(value) is int and value >= 0
        if kind == 'r':
            valid = valid and value < index
    if not valid:
        raise ValueError('expression node field or backward reference is invalid')
