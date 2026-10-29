"""Additional adversarial cases for the exact local-owner constructor."""

import copy
import json

import pytest
from test_real_prose_exact_goal import (
    DECLARATIONS,
    goal,
    request,
    run,
    source,
)
from test_real_prose_exact_goal import project as _project

project = _project


@pytest.mark.parametrize('mutation', [
    'definition-as-formal', 'theorem-as-authored', 'non-prop-value', 'extra-owner-field',
    'extra-range-field', 'boolean-range', 'missing-premises', 'wrong-schema',
])
def test_actual_declaration_kinds_and_closed_nested_schemas(project, mutation):
    value = request()
    declarations = list(DECLARATIONS)
    if mutation == 'definition-as-formal':
        value['formal'] = copy.deepcopy(value['premises'][0])
        value['formal']['kind'] = 'theorem-type'
    elif mutation == 'theorem-as-authored':
        value['authored'] = copy.deepcopy(value['formal'])
        value['authored']['kind'] = 'proposition-value'
    elif mutation == 'non-prop-value':
        declarations[1] = 'def Reading : Nat := 0'
        value['authored']['range']['endColumn'] = len(declarations[1])
    elif mutation == 'extra-owner-field':
        value['authored']['admitted'] = True
    elif mutation == 'extra-range-field':
        value['authored']['range']['ignored'] = True
    elif mutation == 'boolean-range':
        value['authored']['range']['startLine'] = True
    elif mutation == 'missing-premises':
        del value['premises']
    else:
        value['schema'] = 'unknown'
    text = source(value).replace('\n'.join(DECLARATIONS), '\n'.join(declarations))
    (project / 'Case.lean').write_text(text)
    result = run(project, 'Case.lean')
    assert not result.succeeded, mutation
    assert 'error:' in result.stdout + result.stderr


def test_duplicate_json_keys_are_rejected_before_owner_lookup(project):
    encoded = json.dumps(request(), sort_keys=True, separators=(',', ':'))
    encoded = '{"module":"Untrusted",' + encoded[1:]
    text = source(request()).replace(goal(request()), 'ladon_prose_exact_goal% ' + json.dumps(encoded))
    (project / 'Case.lean').write_text(text)
    result = run(project, 'Case.lean')
    assert not result.succeeded
    assert 'canonical JSON' in result.stdout + result.stderr


def test_zero_premise_positive_retains_authored_binder_names(project):
    value = request()
    declarations = list(DECLARATIONS)
    declarations[1] = 'def Reading : Prop := ∀ (authoredIndex : Nat), True'
    value['authored']['range']['endColumn'] = len(declarations[1])
    value['authored']['expression'] = copy.deepcopy(value['formal']['expression'])
    value['premises'] = []
    text = 'import LadonProseExactGoal\n' + '\n'.join(declarations) + '\n'
    text += f'example : {goal(value)} := by\n  intro original\n  exact original\n'
    text += f'example : ({goal(value)}) = ((∀ n : Nat, True) → ∀ authoredIndex : Nat, True) := rfl\n'
    # Inspect the actual constructed Expr, rather than a pretty-printer's names.
    text += '''open Lean Elab Command Term
elab "#check_owner_binders " t:term : command => do
  liftTermElabM do
    let e ← elabTerm t none
    match e with
    | .forallE _ formal authored _ =>
      unless formal.bindingName! == `n do throwError "formal binder was rewritten"
      unless authored.bindingName! == `authoredIndex do throwError "authored binder was rewritten"
    | _ => throwError "missing exact target"
'''
    text += '#check_owner_binders (' + goal(value) + ')\n'
    (project / 'Case.lean').write_text(text)
    result = run(project, 'Case.lean')
    assert result.succeeded, result.stdout + result.stderr


def test_swapped_premises_change_the_target_instead_of_being_sorted(project):
    value = request()
    value['premises'].reverse()
    text = 'import LadonProseExactGoal\n' + '\n'.join(DECLARATIONS) + '\n'
    text += f'example : ({goal(value)}) = ((∀ n : Nat, True) → False → True → False) := rfl\n'
    text += f'example : {goal(value)} := by\n  intro original second first\n  exact second\n'
    (project / 'Case.lean').write_text(text)
    result = run(project, 'Case.lean')
    assert result.succeeded, result.stdout + result.stderr


def test_deep_owner_is_rejected_before_expression_comparison(project):
    value = request()
    declarations = list(DECLARATIONS)
    declarations[1] = 'def Reading : Prop := ' + 'True → ' * 150 + 'True'
    value['authored']['range']['endColumn'] = len(declarations[1])
    (project / 'Case.lean').write_text(source(value).replace('\n'.join(DECLARATIONS), '\n'.join(declarations)))
    result = run(project, 'Case.lean')
    assert not result.succeeded
    assert 'expression depth exceeds 128' in result.stdout + result.stderr
