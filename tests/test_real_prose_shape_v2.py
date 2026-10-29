"""V2 skeletons preserve exact scope and require checked arithmetic normalization."""

import importlib
from copy import deepcopy

import pytest
from test_real_bound_shape import app, bind, const, nonnegative, plus, resolve, var


def reader():
    return importlib.import_module('ladon.real_prose_shape')


def estimate(*, global_scope=True, late_constant=False, guard_k=True,
             guard_c=True, aliases=False, predicate='J', operator='A'):
    order = app('shift', var('n')) if aliases else plus(var('n'), {'nat': 7})
    product = app('product', var('K'), var('C')) if aliases else app(
        'HMul.hMul', const('Real'), const('Real'), const('Real'), const('mulInstance'),
        var('K'), var('C'))
    pred = app(predicate, var('T'))
    middle = [] if global_scope else [var('S')]
    source = app(pred, var('f'), *middle, order, var('C'))
    target = app(pred, app(operator, var('f')), *middle, var('n'), product)
    body = bind('h', source, target)
    if guard_c:
        body = bind('hC', nonnegative('C'), body)
    body = bind('smooth', app('Smooth', var('f')), body)
    if not late_constant:
        body = data_binders(body, global_scope)
    if guard_k:
        body = app('And', nonnegative('K'), body)
    body = app('Exists', const('Real'), bind('K', const('Real'), body, 'lam'))
    if late_constant:
        body = data_binders(body, global_scope)
    return resolve(bind('T', {'sort': '1'}, bind('n', const('Nat'), body)))


def data_binders(body, global_scope):
    rows = [('f', const('Function'))]
    if not global_scope:
        rows.append(('S', app('Set', const('Domain'))))
    rows.append(('C', const('Real')))
    for name, type_ in reversed(rows):
        body = bind(name, type_, body)
    return body


@pytest.mark.parametrize('global_scope,kind', [(True, 'global'), (False, 'set-indexed')])
@pytest.mark.parametrize('predicate,operator', [('J', 'A'), ('Unrelated.Bound', 'Other.Transform')])
def test_exact_global_and_set_skeletons_need_normalization(global_scope, kind, predicate, operator):
    result = reader().recognize_shape(estimate(global_scope=global_scope,
                                              predicate=predicate, operator=operator))
    shape = result['candidate']
    assert result['profileId'] == 'real-bound-prose-shape-v2'
    assert result['admission'] == 'unresolved'
    assert shape['scope']['kind'] == kind
    assert ('set' in shape['input']) is (not global_scope)
    assert shape['loss'] is None
    assert [t['kind'] for t in result['normalizationTargets']] == ['input-order', 'output-bound']
    assert shape['input']['predicate']['app'][0] == const(predicate)
    assert shape['operator'] == const(operator)


def test_aliases_are_retained_not_inferred_from_names():
    result = reader().recognize_shape(estimate(aliases=True))
    assert result['candidate']['loss'] is None
    assert result['candidate']['input']['order']['app'][0] == const('shift')
    assert result['candidate']['output']['bound']['app'][0]['app'][0] == const('product')
    assert all(t['originPath'].startswith('/propositionExpr/') for t in result['normalizationTargets'])


def test_late_coefficient_keeps_all_previous_permissions():
    early = reader().recognize_shape(estimate())['candidate']
    late = reader().recognize_shape(estimate(late_constant=True))['candidate']
    assert len(early['constant']['permittedBinderIds']) == 2
    assert len(late['constant']['permittedBinderIds']) == 4
    assert [r['quantifier'] for r in late['telescope']].count('exists') == 1
    assert len(early['telescope']) == len(late['telescope'])


@pytest.mark.parametrize('guard', ['guard_k', 'guard_c'])
def test_missing_guard_is_not_a_normalizable_estimate(guard):
    result = reader().recognize_shape(estimate(**{guard: False}))
    assert result['candidate'] is None and result['normalizationTargets'] == []
    assert result['residuals']


def test_set_parameter_is_not_synthesized_for_global_bound():
    shape = reader().recognize_shape(estimate())['candidate']
    assert 'set' not in shape['roles']
    assert all(row['type'] != app('Set', const('Domain')) for row in shape['telescope'])


def test_changing_input_does_not_mutate_frozen_expression():
    expression = estimate(aliases=True)
    original = deepcopy(expression)
    reader().recognize_shape(expression)
    assert expression == original


def test_wrong_or_unrelated_proposition_stays_unresolved():
    result = reader().recognize_shape(const('True'))
    assert result['candidate'] is None
    assert result['admission'] == 'unresolved' and result['residuals']
