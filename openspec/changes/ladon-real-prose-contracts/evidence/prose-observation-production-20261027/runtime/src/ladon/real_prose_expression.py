"""Bounded proposition JSON decoding and exact Lean expression tree structure."""

import json

from ladon.proof_contract_payloads import closed
from ladon.proof_contract_worker import _ensure_json_depth, _unique_json_object
from ladon.real_prose_inputs import MAX_BYTES


def parse_worker(encoded):
    if not isinstance(encoded, str) or len(encoded.encode()) > MAX_BYTES:
        raise ValueError('prose helper output exceeds its byte bound')
    _ensure_json_depth(encoded, 272)
    result = json.loads(encoded, object_pairs_hook=_unique_json_object)
    if not isinstance(result, dict):
        raise TypeError('prose helper output must be an object')
    return result


def validate_expression(expression):
    stack, count = [(expression, 0, 0)], 0
    while stack:
        node, depth, scope = stack.pop()
        count += 1
        if count > 100_000 or depth > 128:
            raise ValueError('prose expression exceeds its node/depth bound')
        children = _children(node, scope)
        stack.extend((child, depth + 1, child_scope) for child, child_scope in children)


def _children(node, scope):
    if not isinstance(node, dict):
        raise TypeError('prose expression node must be an object')
    if set(node) == {'const', 'levels'}:
        return _constant_children(node)
    if len(node) != 1:
        raise ValueError('prose expression requires one constructor')
    tag, value = next(iter(node.items()))
    if tag in {'lam', 'forallE', 'letE'}:
        return _binder_children(tag, value, scope)
    if tag == 'app':
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError('prose application requires ordered function and argument')
        return [(child, scope) for child in value]
    return _leaf_children(tag, value, scope)


def _binder_children(tag, value, scope):
    keys = {'name', 'type', 'body', 'value', 'nondep'} if tag == 'letE' else {
        'name', 'type', 'body', 'binderInfo'}
    closed(value, keys, 'prose expression binder')
    if not isinstance(value['name'], str):
        raise TypeError('prose binder name must be a string')
    children = [(value['type'], scope), (value['body'], scope + 1)]
    if tag == 'letE':
        if type(value['nondep']) is not bool:
            raise ValueError('prose let dependency marker must be Boolean')
        children.append((value['value'], scope))
    elif value['binderInfo'] not in {'explicit', 'implicit', 'strict-implicit', 'instance-implicit'}:
        raise ValueError('invalid prose binder information')
    return children


def _constant_children(node):
    if not isinstance(node['const'], str) or not isinstance(node['levels'], list):
        raise TypeError('prose constant must preserve name and levels')
    if not all(isinstance(level, str) for level in node['levels']):
        raise ValueError('prose constant levels must be strings')
    return []


def _projection(value, scope):
    closed(value, {'typeName', 'index', 'structure'}, 'prose projection')
    if not isinstance(value['typeName'], str) or type(value['index']) is not int or value['index'] < 0:
        raise ValueError('invalid prose projection identity')
    return [(value['structure'], scope)]


def _leaf_children(tag, value, scope):
    if tag == 'proj':
        return _projection(value, scope)
    if tag == 'bvar':
        valid = type(value) is int and 0 <= value < scope
    elif tag == 'nat':
        valid = type(value) is int and value >= 0
    elif tag in {'sort', 'string'}:
        valid = isinstance(value, str)
    else:
        valid = False
    if not valid:
        raise ValueError('invalid or unclosed prose expression constructor')
    return []
