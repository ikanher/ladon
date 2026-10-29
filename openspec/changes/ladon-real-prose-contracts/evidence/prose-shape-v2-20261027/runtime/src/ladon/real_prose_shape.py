"""Versioned global/set estimate skeletons; arithmetic still needs checked evidence."""

from copy import deepcopy

from ladon._real_bound_terms import application, direct_binder, is_nonnegative, scoped, unsupported
from ladon.proof_contract_expressions import (
    _app_argument_path,
    _app_parts,
    _const_name,
    _Unsupported,
)
from ladon.real_prose_expression import validate_expression

PROFILE_ID = 'real-bound-prose-shape-v2'
MAX_BINDERS = 64


def recognize_shape(expression):
    try:
        validate_expression(expression)
        shape, targets = _recognize(expression)
    except (_Unsupported, ValueError, TypeError, KeyError, IndexError) as error:
        code = error.code if isinstance(error, _Unsupported) else 'invalid-bound-expression'
        return _result(None, [], [{'code': code, 'message': str(error)}])
    return _result(shape, targets, [{'code': 'arithmetic-normalization-required',
                                    'message': 'Exact arithmetic expressions require source-context kernel checks.'}])


def _result(candidate, targets, residuals):
    return {'profileId': PROFILE_ID, 'candidate': candidate, 'normalizationTargets': targets,
            'admission': 'unresolved', 'residuals': residuals}


def _binder(row, quantifier, scope, telescope, path):
    if len(telescope) >= MAX_BINDERS:
        unsupported('Telescope exceeds 64 binders', code='telescope-limit')
    identity = f'b{len(telescope)}'
    telescope.append({'binderId': identity, 'quantifier': quantifier,
                      'type': scoped(row['type'], scope), 'binderInfo': row['binderInfo'],
                      'originPath': path})
    scope.append(identity)


def _peel(expression):
    telescope, scope, conjunctions = [], [], []
    path, last = '/propositionExpr', None
    while isinstance(expression, dict):
        if 'forallE' in expression:
            row = expression['forallE']
            last = (row['type'], list(scope), path + '/forallE/type')
            _binder(row, 'forall', scope, telescope, path)
            expression, path = row['body'], path + '/forallE/body'
            continue
        head, args = _app_parts(expression)
        if _const_name(head) == 'Exists' and len(args) == 2 and 'lam' in args[-1]:
            row = args[-1]['lam']
            if _const_name(args[0]) != 'Real' or _const_name(row['type']) != 'Real':
                unsupported('Coefficient existential must have observed type Real')
            path = _app_argument_path(expression, 1, path) + '/lam'
            _binder(row, 'exists', scope, telescope, path)
            expression, path = row['body'], path + '/body'
            continue
        if _const_name(head) == 'And' and len(args) == 2:
            conjunctions.append({'expression': scoped(args[0], scope),
                                 'originPath': _app_argument_path(expression, 0, path)})
            expression, path = args[1], _app_argument_path(expression, 1, path)
            continue
        break
    return telescope, scope, conjunctions, last, expression, path


def _recognize(expression):
    telescope, scope, conjunctions, last, body, path = _peel(expression)
    anchor = _coefficient_anchor(telescope, conjunctions, last)
    choices = []
    for arity in (3, 4):
        try:
            choices.append(_candidate(telescope, scope, conjunctions[0], last, body, path, anchor, arity))
        except _Unsupported:
            continue
    if len(choices) != 1:
        unsupported('Expected exactly one complete global or set-indexed interpretation',
                    code='ambiguous-bound-scope' if choices else 'unsupported-bound-shape')
    return choices[0]


def _coefficient_anchor(telescope, conjunctions, last):
    constants = [row for row in telescope if row['quantifier'] == 'exists']
    if len(constants) != 1 or len(conjunctions) != 1 or last is None:
        unsupported('Expected one coefficient existential and its nonnegative conjunction')
    anchor = constants[0]['binderId']
    if not is_nonnegative(conjunctions[0]['expression'], anchor):
        unsupported('Missing explicit nonnegative coefficient guard', 'constant.guard')
    return anchor


def _application(expression, arity):
    predicate, args = application(expression, arity, 'bound-predicate')
    head, _ = _app_parts(predicate)
    if _const_name(head) in {None, 'Not', 'Or', 'And', 'Exists', 'Eq', 'LE.le'}:
        unsupported('Bound predicate must retain a named exact prefix')
    names = ('function', 'order', 'bound') if arity == 3 else ('function', 'set', 'order', 'bound')
    return {'predicate': predicate, **dict(zip(names, args, strict=True))}


def _roles(source, target, telescope, anchor, arity):
    roles = {'function': direct_binder(source['function'], telescope),
             'order': direct_binder(target['order'], telescope, type_name='Nat'),
             'bound': direct_binder(source['bound'], telescope, type_name='Real'), 'constant': anchor}
    if arity == 4:
        identity = direct_binder(source['set'], telescope)
        type_ = next(row['type'] for row in telescope if row['binderId'] == identity)
        head, args = _app_parts(type_)
        if _const_name(head) != 'Set' or len(args) != 1:
            unsupported('Set-indexed bound must retain an explicit Set-typed binder')
        roles['set'] = identity
    universals = {row['binderId'] for row in telescope if row['quantifier'] == 'forall'}
    if len(set(roles.values())) != len(roles) or not set(roles.values()) - {anchor} <= universals:
        unsupported('Bound roles require distinct actual universal binders')
    return roles


def _candidate(telescope, scope, guard, last, body, path, anchor, arity):
    source, target = _application(scoped(last[0], last[1]), arity), _application(scoped(body, scope), arity)
    roles = _roles(source, target, telescope, anchor, arity)
    _match_endpoints(source, target, arity)
    operator, operands = application(target['function'], 1, 'operator')
    if operands[0] != source['function']:
        unsupported('Output operator must apply to the exact input object')
    guards = _bound_guards(telescope, roles['bound'])
    before = [row['binderId'] for row in telescope[:int(anchor[1:])] if row['quantifier'] == 'forall']
    shape = {'schema': 'ladon-typed-prose-bound-shape-v2', 'telescope': deepcopy(telescope),
             'roles': roles, 'scope': {'kind': 'global' if arity == 3 else 'set-indexed'},
             'input': {**source, 'originPath': last[2]}, 'output': {**target, 'originPath': path},
             'operator': operator, 'loss': None,
             'constant': {'binderId': anchor, 'permittedBinderIds': before},
             'guards': {'constantNonnegative': guard, 'boundNonnegativeBinderIds': guards}}
    _, source_args = _app_parts(last[0])
    _, target_args = _app_parts(body)
    targets = [{'kind': 'input-order',
                'originPath': _app_argument_path(last[0], len(source_args) - 2, last[2])},
               {'kind': 'output-bound',
                'originPath': _app_argument_path(body, len(target_args) - 1, path)}]
    return shape, targets


def _match_endpoints(source, target, arity):
    if source['predicate'] != target['predicate']:
        unsupported('Predicate prefix or fixed parameters differ')
    if arity == 4 and source['set'] != target['set']:
        unsupported('Input/output sets differ')


def _bound_guards(telescope, bound):
    guards = [row['binderId'] for row in telescope if row['quantifier'] == 'forall'
              and is_nonnegative(row['type'], bound)]
    if not guards:
        unsupported('Missing explicit nonnegative input-bound guard')
    return guards
