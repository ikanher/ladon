"""Exact expression origins and source-prefix closures for alias certificates."""

from copy import deepcopy

from ladon.proof_contract_payloads import closed
from ladon.real_bound_binding import _alpha_expression


def alpha_equal(left, right):
    return _alpha_expression(left) == _alpha_expression(right)


def selected_expression(proposition, pointer):
    if not isinstance(pointer, str) or not pointer.startswith('/propositionExpr/'):
        raise ValueError('normalization origin must name the exact proposition expression')
    parts = pointer.split('/')[2:]
    if len(parts) > 256:
        raise ValueError('normalization origin exceeds path bound')
    node, prefix = proposition, []
    for index, part in enumerate(parts):
        if isinstance(node, list):
            if part not in {'0', '1'}:
                raise ValueError('invalid expression array selector')
            node = node[int(part)]
        else:
            if part == 'body' and index and parts[index - 1] in {'forallE', 'lam'}:
                prefix.append(deepcopy(node))
            if not isinstance(node, dict) or part not in node:
                raise ValueError('normalization origin is outside the proposition')
            node = node[part]
    return deepcopy(node), prefix


def close_prefix(prefix, body, kind='lam'):
    result = deepcopy(body)
    for row in reversed(prefix):
        result = {kind: {key: deepcopy(value) for key, value in row.items() if key != 'body'} | {'body': result}}
    return result


def binder_reference(prefix, index):
    if type(index) is not int or not 0 <= index < len(prefix):
        raise ValueError('normalization role escapes its exact source prefix')
    return {'bvar': len(prefix) - index - 1}


def alias_request(shape):
    candidate = shape['candidate']
    if candidate is None:
        raise ValueError('alias normalization requires a complete bound skeleton')
    roles = {key: int(candidate['roles'][key][1:]) for key in ('order', 'constant', 'bound')}
    return {'schema': 'ladon-prose-alias-request-v1', 'targets': [
        {**row, 'roles': roles} for row in shape['normalizationTargets']]}


def validate_alias_request(value, shape):
    closed(value, {'schema', 'targets'}, 'prose alias request')
    if value != alias_request(shape):
        raise ValueError('alias request differs from exact observed roles and origins')
