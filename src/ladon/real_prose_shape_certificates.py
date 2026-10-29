"""Validate saved alias-certificate owners without authenticating saved execution."""

from copy import deepcopy

from ladon.proof_contract_expressions import _app_parts, _const_name
from ladon.proof_contract_payloads import closed
from ladon.real_prose_expression import validate_expression
from ladon.real_prose_shape_paths import (
    alpha_equal,
    binder_reference,
    close_prefix,
    selected_expression,
)


def apply_certificates(shape, proposition, rows):
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError('normalization requires both ordered target results')
    candidate, residuals, complete = deepcopy(shape['candidate']), [], True
    for target, certificate in zip(shape['normalizationTargets'], rows, strict=True):
        if any(certificate.get(key) != target[key] for key in ('kind', 'originPath')):
            raise ValueError('normalization certificate has the wrong expression owner')
        if certificate['state'] == 'unresolved':
            closed(certificate, {'kind', 'originPath', 'state', 'code', 'message'}, 'unresolved normalization')
            residuals.append({'code': certificate['code'], 'message': certificate['message']})
            complete = False
            continue
        literal = _checked_certificate(certificate, proposition, candidate['roles'])
        if target['kind'] == 'input-order':
            candidate['loss'] = literal
    return {'profileId': shape['profileId'], 'candidate': candidate,
            'admission': 'unresolved', 'normalizationState': 'checked' if complete else 'partial',
            'residuals': residuals + [{'code': 'predicate-admission-unchecked',
                'message': 'Checked arithmetic does not admit the bound predicate or certify prose meaning.'}]}


def _checked_certificate(row, proposition, roles):
    closed(row, {'kind', 'originPath', 'state', 'lossLiteral', 'original', 'canonical',
                 'goal', 'proof', 'kernelCheck', 'scopeCount', 'levelParams'}, 'alias certificate')
    if row['state'] != 'checked' or row['kernelCheck'] != 'synchronous':
        raise ValueError('alias certificate must record its synchronous kernel check')
    original, prefix, canonical = _source_closure(row, proposition)
    type_ = _canonical(row, canonical, prefix, roles)
    _equation(row['goal'], prefix, type_, original, canonical)
    _reflexivity(row['proof'], prefix, type_, original)
    if not isinstance(row['levelParams'], list) or not all(isinstance(x, str) for x in row['levelParams']):
        raise ValueError('alias certificate must retain universe parameters')
    return row['lossLiteral']


def _source_closure(row, proposition):
    original, prefix = selected_expression(proposition, row['originPath'])
    if row['scopeCount'] != len(prefix):
        raise ValueError('alias certificate dropped or inserted source binders')
    for key in ('original', 'canonical', 'goal', 'proof'):
        validate_expression(row[key])
    if not alpha_equal(row['original'], close_prefix(prefix, original)):
        raise ValueError('alias certificate original differs from exact source expression')
    return original, prefix, _body(row['canonical'], prefix, 'lam')


def _equation(goal, prefix, type_, original, canonical):
    head, args = _app_parts(_body(goal, prefix, 'forallE'))
    if _const_name(head) != 'Eq' or len(args) != 3:
        raise ValueError('alias certificate must own its exact equality goal')
    if not all(alpha_equal(a, b) for a, b in zip(args, [type_, original, canonical], strict=True)):
        raise ValueError('alias equality has different operands or carrier')


def _reflexivity(proof, prefix, type_, original):
    head, args = _app_parts(_body(proof, prefix, 'lam'))
    if (_const_name(head) != 'Eq.refl' or len(args) != 2
            or not alpha_equal(args[0], type_) or not alpha_equal(args[1], original)):
        raise ValueError('alias proof differs from the source reflexivity certificate')


def _body(expression, prefix, kind):
    current = expression
    for source in prefix:
        if not isinstance(current, dict) or set(current) != {kind}:
            raise ValueError('alias certificate has an incomplete source closure')
        row = current[kind]
        expected = {key: value for key, value in source.items() if key not in {'body', 'name'}}
        actual = {key: value for key, value in row.items() if key not in {'body', 'name'}}
        if not alpha_equal(actual, expected):
            raise ValueError('alias certificate binder type or information differs from source')
        current = row['body']
    return current


def _canonical(row, body, prefix, roles):
    head, args = _app_parts(body)
    refs = {key: binder_reference(prefix, int(roles[key][1:])) for key in ('order', 'constant', 'bound')}
    if row['kind'] == 'input-order':
        return _canonical_order(row, head, args, refs['order'])
    return _canonical_product(row, head, args, refs)


def _canonical_order(row, head, args, order):
    literal = row['lossLiteral']
    if type(literal) is not int or not 0 <= literal <= 2**53 - 1:
        raise ValueError('alias loss must be a bounded Nat literal')
    if _const_name(head) != 'Nat.add' or args != [order, {'nat': literal}]:
        raise ValueError('alias canonical order must be the exact builtin Nat shift')
    return {'const': 'Nat', 'levels': []}


def _canonical_product(row, head, args, refs):
    real = {'const': 'Real', 'levels': []}
    if (_const_name(head) != 'HMul.hMul' or len(args) != 6 or args[:3] != [real] * 3
            or args[-2:] != [refs['constant'], refs['bound']] or row['lossLiteral'] is not None):
        raise ValueError('alias canonical product must retain its carrier, instance and exact K/C')
    return real
