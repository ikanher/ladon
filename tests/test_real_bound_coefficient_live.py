"""Public coefficient checking with actual source admission and kernel evidence."""

import copy
import json
import os
import time

import pytest
from test_real_bound_coefficient_lean import FIXTURE
from test_real_bound_prefix_lean import clean_root

from ladon.proof_contract_cli import contract_main
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.real_bound_binding import plan_bound_prefix
from ladon.real_bound_native_plan import plan_real_bound
from ladon.real_bound_native_production import produce_real_bound
from ladon.real_bound_observation import observe_bound_snapshot


def admit(root, name, measure, arguments):
    snapshot = produce_formal_snapshot(root, 'CoefficientExamples.lean', 'CoefficientExamples', name)
    observation = observe_bound_snapshot(snapshot, root)
    plan = plan_real_bound(plan_bound_prefix(observation, {'declaration': measure, 'arguments': arguments}))
    terms = {'predicate-admission': 'by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl',
             'scalar-semantics': 'by intros; exact ⟨rfl, rfl, rfl⟩'}
    production = produce_real_bound(root, plan, terms, timeout_seconds=180)
    assert production['status'] == 'admitted', production.get('check')
    return production


def mutate(run, kind):
    changed = copy.deepcopy(run)
    if kind == 'owner':
        changed['result']['request']['planId'] = 'different'
    elif kind in ('term', 'scalar'):
        field = 'term' if kind == 'term' else 'scalarTerm'
        changed['result']['request'][field] = 'by trivial'
    elif kind == 'goal':
        changed['result']['request']['goal']['proposition'] = 'True'
    elif kind == 'memory':
        changed['processReceipt']['memoryLimited'] = True
    elif kind == 'checker':
        changed['result']['checkerIdentity'] = 'sha256:' + 'f' * 64
    else:
        changed['result']['check']['capture']['capture']['source']['digest'] = 'sha256:' + 'e' * 64
    return changed


def _assert_scope(result):
    assert result['status'] == 'resolved'
    assert result['rule'] == 'coefficient-mono-v1'
    assert result['scope'] == 'pointwise-fixed-output-context'
    assert result['sourceTheoremProof'] == 'not-checked'
    assert result['coefficientUniformity'] == 'not-inferred'
    assert result['paperNormBridge'] == 'unresolved'


def assert_checked(result, production):
    from ladon.real_bound_native_coefficient import accepted_coefficient_run

    _assert_scope(result)
    run = result['relationCheckRun']
    assert run['result']['status'] == 'checked'
    assert accepted_coefficient_run(run, production)
    for kind in ('owner', 'term', 'scalar', 'goal', 'memory', 'checker', 'source'):
        assert not accepted_coefficient_run(mutate(run, kind), production), kind


@pytest.mark.skipif(os.environ.get('LADON_REAL_BOUND_LIVE_COEFFICIENT') != '1',
                    reason='opt-in actual admission and coefficient CLI qualification')
def test_live_coefficient_rule_preserves_pointwise_and_parameterized_contexts(tmp_path, capsys):
    clean_root(tmp_path)
    source = tmp_path / 'CoefficientExamples.lean'
    source.write_text(FIXTURE.read_text())
    cases = []
    for name, measure, arguments in (
        ('pointwise', 'measure', []),
        ('Parameterized.estimate', 'Parameterized.measure', ['b1']),
    ):
        started = time.monotonic()
        production = admit(tmp_path, 'CoefficientExamples.' + name, 'CoefficientExamples.' + measure, arguments)
        path = tmp_path / (name + '.json')
        path.write_text(json.dumps(production))
        output = tmp_path / (name + '-result.json')
        assert contract_main(['check-real-bound-coefficient', '--input', str(path), '--root', str(tmp_path),
                              '--output', str(output), '--timeout-seconds', '600']) == 0
        result = json.loads(output.read_text())
        assert_checked(result, production)
        cases.append({'name': name, 'status': result['status'], 'elapsedSeconds': time.monotonic() - started})
        capsys.readouterr()
    source.write_text(FIXTURE.read_text() + '\n-- changed source\n')
    assert contract_main(['check-real-bound-coefficient', '--input', str(path), '--root', str(tmp_path)]) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'invalid'
    with capsys.disabled():
        print(json.dumps({'cases': cases, 'runDirectory': str(tmp_path)}))
