"""Actual-Mathlib input production for the public connection acceptance tests."""

import os
from pathlib import Path

import pytest
from test_real_prose_recognition import app, quantified, var

from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_binding import plan_bound_prefix
from ladon.real_bound_native_plan import plan_real_bound
from ladon.real_bound_native_production import produce_real_bound
from ladon.real_bound_observation import observe_bound_snapshot
from ladon.real_prose_native_production import produce_real_prose_bound

TERMS = {'predicate-admission': 'by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl',
         'scalar-semantics': 'by intros; exact ⟨rfl, rfl, rfl⟩'}


def project(tmp_path_factory):
    selected = os.environ.get('LADON_MATHLIB_TEST_ROOT')
    if selected is None:
        pytest.skip('set LADON_MATHLIB_TEST_ROOT for actual connection acceptance')
    chosen = Path(selected).resolve(strict=True)
    root = tmp_path_factory.mktemp('connection-live')
    (root/'lean-toolchain').write_bytes((chosen/'lean-toolchain').read_bytes())
    (root/'.lake/build/lib/lean').mkdir(parents=True)
    for i, library in enumerate(pinned_toolchain(chosen).library_roots):
        target = root/f'.lake/packages/import{i}/.lake/build/lib/lean'
        target.parent.mkdir(parents=True)
        target.symlink_to(library, target_is_directory=True)
    source = (Path(__file__).parent/'fixtures/real_bound_native/TransferExamples.lean').read_text()
    source += '\ndef ConnectionShift (n : Nat) := n+4\ndef ConnectionProduct (k c : Real) := k*c\n'
    source += 'def ConnectionGlobal (f : Real) (n : Nat) (C : Real) : Prop := TransferExamples.bound f Set.univ n C\n'
    (root/'Context.lean').write_text(source)
    (root/'claim.txt').write_text('An attributed generic transfer estimate, without fidelity certification.')
    return root


def formal_input(root):
    snapshot = produce_formal_snapshot(root, 'Context.lean', 'Context', 'TransferExamples.first')
    observation = observe_bound_snapshot(snapshot, root)
    plan = plan_real_bound(plan_bound_prefix(observation, {'declaration':'TransferExamples.measure','arguments':[]}))
    result = produce_real_bound(root, plan, TERMS, timeout_seconds=300)
    assert result['status'] == 'admitted', result
    return result


def interpretation(root, *, global_scope):
    import hashlib

    quote = (root/'claim.txt').read_text()
    symbols = {'J': {'leanName': 'ConnectionGlobal' if global_scope else 'TransferExamples.bound',
                     'leanType': 'Real → Nat → Real → Prop' if global_scope else 'Real → Set Nat → Nat → Real → Prop'},
               'A': {'leanName':'TransferExamples.twice','leanType':'Real → Real'},
               'shift': {'leanName':'ConnectionShift','leanType':'Nat → Nat'},
               'product': {'leanName':'ConnectionProduct','leanType':'Real → Real → Real'}}
    middle = [] if global_scope else [var('S')]
    source = app('J', var('f'), *middle, app('shift', var('n')), var('C'))
    target = app('J', app('A',var('f')), *middle, var('n'),app('product',var('K'),var('C')))
    def nonnegative(name):
        return {'tag':'le','left':{'tag':'const','name':'0'},'right':var(name)}
    body = {'tag':'implies','premise':nonnegative('C'),
            'conclusion':{'tag':'implies','premise':source,'conclusion':target}}
    body = quantified('forall','C','Real',body)
    if not global_scope:
        body = quantified('forall','S','Set Nat',body)
    body = quantified('forall','f','Real',body)
    body = quantified('exists','K','Real',{'tag':'and','items':[nonnegative('K'),body]})
    body = quantified('forall','n','Nat',body)
    return {'id':'generic:connection-reading','source':{'path':'claim.txt','startLine':1,'endLine':1,
             'quote':quote,'sha256':hashlib.sha256(quote.encode()).hexdigest()},'formula':body,'symbols':symbols}


def authored_input(root, *, global_scope):
    context = {'schema':'ladon-prose-bound-context-v1','file':'Context.lean','module':'Context','scope':'file-end'}
    result = produce_real_prose_bound(root, interpretation(root,global_scope=global_scope), context,
                                      alternative_id='generic:global' if global_scope else 'generic:set',
                                      author='acceptance',timeout_seconds=120)
    assert result['status'] == 'authored', result
    return result
