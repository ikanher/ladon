"""Source-context equality checks authorize syntax features, never Real admission."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest
from test_proof_contract_cli import invoke

ROOT = Path(__file__).parent / 'fixtures/real_prose_recognition'


def api():
    return importlib.import_module('ladon.real_prose_recognition')


def var(identity):
    return {'tag': 'var', 'id': identity}


def app(symbol, *args):
    return {'tag': 'app', 'symbol': symbol, 'args': list(args)}


def quantified(tag, name, domain, body):
    return {'tag': tag, 'binder': {'id': name, 'name': name, 'domain': domain}, 'body': body}


def reading(root, *, set_indexed=False, product='product', shift='bump'):
    quote = 'An authored indexed estimate; interpretation and Real meaning remain unreviewed.'
    (root / 'claim.txt').write_text(quote)
    symbols = {'J': {'leanName': 'BoundSet' if set_indexed else 'BoundGlobal',
                     'leanType': 'Fn → Set Nat → Nat → Real → Prop' if set_indexed else 'Fn → Nat → Real → Prop'},
               'A': {'leanName': 'Transform', 'leanType': 'Fn → Fn'},
               'shift': {'leanName': shift, 'leanType': 'Nat → Nat'},
               'product': {'leanName': product, 'leanType': 'Real → Real → Real'}}
    middle = [var('S')] if set_indexed else []
    source = app('J', var('f'), *middle, app('shift', var('n')), var('C'))
    target = app('J', app('A', var('f')), *middle, var('n'), app('product', var('K'), var('C')))
    def nonnegative(x):
        return {'tag': 'le', 'left': {'tag': 'const', 'name': '0'}, 'right': var(x)}
    body = {'tag': 'implies', 'premise': nonnegative('C'),
            'conclusion': {'tag': 'implies', 'premise': source, 'conclusion': target}}
    body = quantified('forall', 'C', 'Real', body)
    if set_indexed:
        body = quantified('forall', 'S', 'Set Nat', body)
    body = quantified('forall', 'f', 'Fn', body)
    body = {'tag': 'and', 'items': [nonnegative('K'), body]}
    body = quantified('exists', 'K', 'Real', body)
    body = quantified('forall', 'n', 'Nat', body)
    return {'id': 'reading:bound', 'source': {'path': 'claim.txt', 'startLine': 1, 'endLine': 1,
            'quote': quote, 'sha256': hashlib.sha256(quote.encode()).hexdigest()},
            'formula': body, 'symbols': symbols}


@pytest.fixture
def project(tmp_path):
    for name in ['Context.lean', 'lean-toolchain']:
        (tmp_path / name).write_bytes((ROOT / name).read_bytes())
    return tmp_path


def context():
    return {'schema': 'ladon-prose-bound-context-v1', 'file': 'Context.lean',
            'module': 'Context', 'scope': 'file-end'}


@pytest.mark.parametrize('set_indexed', [False, True])
def test_actual_alias_equalities_recognize_both_scopes_without_admission(project, set_indexed):
    result = api().recognize_prose_bound(project, reading(project, set_indexed=set_indexed), context(),
                                        timeout_seconds=60)
    assert result['status'] == 'recognized', result
    assert result['profileId'] == 'real-bound-prose-shape-v2'
    assert result['admission'] == 'unresolved' and result['contract'] is None
    final = result['check']['result']
    assert final['features']['candidate']['loss'] == 5
    assert final['features']['candidate']['scope']['kind'] == ('set-indexed' if set_indexed else 'global')
    checks = final['normalization']['worker']['results']
    assert [r['state'] for r in checks] == ['checked', 'checked']
    assert all(r['kernelCheck'] == 'synchronous' for r in checks)
    assert all(r['scopeCount'] > 0 for r in checks)
    inspected = api().inspect_recognition(result, project)
    assert inspected['authority'] == 'none' and inspected['freshCheck'] is False


@pytest.mark.parametrize('change', [{'product': 'wrongProduct'}, {'shift': 'nonlinearShift'}])
def test_incorrect_alias_is_retained_as_unresolved(project, change):
    result = api().recognize_prose_bound(project, reading(project, **change), context(), timeout_seconds=60)
    assert result['status'] == 'unresolved'
    checks = result['check']['result']['normalization']['worker']['results']
    assert any(r['state'] == 'unresolved' for r in checks)
    assert result['contract'] is None


def test_rehashed_loss_tampering_is_rejected(project):
    from ladon.real_prose_inputs import observation_identity

    result = api().recognize_prose_bound(project, reading(project), context(), timeout_seconds=60)
    result['check']['result']['features']['candidate']['loss'] = 4
    result['snapshotId'] = observation_identity(result)
    with pytest.raises(ValueError):
        api().inspect_recognition(result)


def test_public_recognition_preserves_historical_authority(project):
    for name, value in [('reading', reading(project)), ('context', context())]:
        (project / (name + '.json')).write_text(json.dumps(value))
    output = project / 'recognized.json'
    result = invoke('recognize-prose-bound', '--root', project, '--interpretation', project / 'reading.json',
                    '--context', project / 'context.json', '--output', output, '--timeout-seconds', '60')
    assert result.returncode == 0, result.stdout + result.stderr
    inspected = invoke('inspect', '--input', output, '--root', project)
    assert inspected.returncode == 0, inspected.stdout + inspected.stderr
    assert json.loads(inspected.stdout)['authority'] == 'none'
    before = output.read_bytes()
    assert invoke('recognize-prose-bound', '--root', project, '--interpretation', project / 'reading.json',
                  '--context', project / 'context.json', '--output', output).returncode == 2
    assert output.read_bytes() == before
