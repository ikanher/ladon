"""Public source admission and prefix-rule qualification without checker mocks."""

import copy
import json
import os
import time

import pytest
from test_real_bound_prefix_lean import FIXTURE, clean_root

from ladon.proof_contract_cli import contract_main
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.real_bound_binding import plan_bound_prefix
from ladon.real_bound_native_plan import plan_real_bound
from ladon.real_bound_native_prefix import accepted_prefix_run
from ladon.real_bound_native_production import produce_real_bound
from ladon.real_bound_observation import observe_bound_snapshot


def admit(root, declaration, measure, arguments):
    snapshot = produce_formal_snapshot(root, 'PrefixExamples.lean', 'PrefixExamples', declaration)
    observation = observe_bound_snapshot(snapshot, root)
    plan = plan_real_bound(plan_bound_prefix(observation, {'declaration': measure, 'arguments': arguments}))
    terms = {'predicate-admission': 'by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl',
             'scalar-semantics': 'by intros; exact ⟨rfl, rfl, rfl⟩'}
    production = produce_real_bound(root, plan, terms, timeout_seconds=180)
    assert production['status'] == 'admitted', production.get('check')
    return production


def rejection_mutations(run, strong, weak):
    for kind in ('owner', 'goal', 'proof', 'memory', 'source'):
        changed = copy.deepcopy(run)
        if kind == 'owner':
            changed['result']['request']['strongerPlanId'] = weak['request']['plan']['planId']
        elif kind == 'goal':
            changed['result']['request']['goal']['proposition'] = 'True'
        elif kind == 'proof':
            changed['result']['request']['term'] = 'by trivial'
        elif kind == 'memory':
            changed['processReceipt']['memoryLimited'] = True
        else:
            changed['result']['check']['capture']['capture']['source']['digest'] = 'sha256:' + 'e' * 64
        assert accepted_prefix_run(changed, strong, weak) is False


@pytest.mark.skipif(os.environ.get('LADON_REAL_BOUND_LIVE_PREFIX') != '1',
                    reason='opt-in fresh admission and rule CLI qualification')
def test_live_public_prefix_rule_across_two_families(tmp_path, capsys):
    started = time.monotonic()
    clean_root(tmp_path)
    source = tmp_path / 'PrefixExamples.lean'
    source.write_text(FIXTURE.read_text())
    peaks, cases = [], []
    for label, strong_name, weak_name, measure, args in (
        ('scalar', 'PrefixExamples.wide', 'PrefixExamples.narrow', 'PrefixExamples.measure', []),
        ('parameterized-function', 'PrefixExamples.Alternative.higher', 'PrefixExamples.Alternative.lower',
         'PrefixExamples.Alternative.measure', ['b0']),
    ):
        strong, weak = [admit(tmp_path, name, measure, args) for name in (strong_name, weak_name)]
        strong_path, weak_path = tmp_path / (label + '-strong.json'), tmp_path / (label + '-weak.json')
        for path, value in ((strong_path, strong), (weak_path, weak)):
            path.write_text(json.dumps(value))
            peaks.append(value['check']['processReceipt']['peakRssBytes'])
        target = tmp_path / (label + '-result.json')
        assert contract_main(['check-real-bound-prefix', '--stronger', str(strong_path),
                              '--weaker', str(weak_path), '--root', str(tmp_path), '--output', str(target)]) == 0
        result = json.loads(target.read_text())
        assert result['relation'] == 'input-prefix-implies'
        assert result['rule'] == 'order-prefix-v1'
        assert result['sourceTheoremProof'] == 'not-checked'
        assert result['paperNormBridge'] == 'unresolved'
        assert result['strongerInputContractRef'] != result['weakerInputContractRef']
        assert result['relationCheckRun']['result']['status'] == 'checked'
        peaks.append(result['relationCheckRun']['processReceipt']['peakRssBytes'])
        rejection_mutations(result['relationCheckRun'], strong, weak)
        capsys.readouterr()
        assert contract_main(['check-real-bound-prefix', '--stronger', str(weak_path),
                              '--weaker', str(strong_path), '--root', str(tmp_path)]) == 2
        reverse = json.loads(capsys.readouterr().out)
        assert reverse['status'] == 'unresolved' and reverse['rule'] is None
        assert reverse['relationCheckRun'] is None
        assert reverse['residuals'] == [{'code': 'real-prefix-direction-unproved'}]
        cases.append({'family': label, 'status': result['status'], 'reverseStatus': reverse['status']})
    source.write_text(FIXTURE.read_text() + '\n-- current source drift\n')
    assert contract_main(['check-real-bound-prefix', '--stronger', str(strong_path),
                          '--weaker', str(weak_path), '--root', str(tmp_path)]) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'invalid'
    with capsys.disabled():
        print(json.dumps({'cases': cases, 'elapsedSeconds': time.monotonic() - started,
                          'maximumMeasuredWorkerRssBytes': max(peaks), 'runDirectory': str(tmp_path)}))
