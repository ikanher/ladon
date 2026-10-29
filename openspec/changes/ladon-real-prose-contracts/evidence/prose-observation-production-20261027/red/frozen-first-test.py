"""Authored propositions are observed with source custody and no proof authority."""

import hashlib
import importlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from test_proof_contract_cli import invoke


def module():
    return importlib.import_module('ladon.real_prose_observation')


@pytest.fixture
def inputs(tmp_path):
    toolchain = Path(__file__).parent / 'fixtures/real_bound_observation/lean-toolchain'
    (tmp_path / 'lean-toolchain').write_bytes(toolchain.read_bytes())
    (tmp_path / 'Context.lean').write_text('import Lean\n')
    quote = 'Every natural number is strictly smaller than itself.'
    (tmp_path / 'claim.txt').write_text(quote)
    reading = {
        'id': 'reading:unproved', 'source': {
            'path': 'claim.txt', 'startLine': 1, 'endLine': 1, 'quote': quote,
            'sha256': hashlib.sha256(quote.encode()).hexdigest()},
        'formula': {'tag': 'forall', 'binder': {'id': 'n', 'name': 'n', 'domain': 'Nat'},
                    'body': {'tag': 'lt', 'left': {'tag': 'var', 'id': 'n'},
                             'right': {'tag': 'var', 'id': 'n'}}},
        'symbols': {},
    }
    context = {'schema': 'ladon-prose-bound-context-v1', 'file': 'Context.lean',
               'module': 'Context', 'scope': 'file-end'}
    return reading, context


def observe(root, inputs):
    return module().observe_prose_bound(root, *inputs, timeout_seconds=60)


def test_false_proposition_is_observed_without_proof_or_admission(tmp_path, inputs):
    result = observe(tmp_path, inputs)
    assert result['schema'] == 'ladon-real-prose-observation-v1'
    assert result['status'] == 'observed'
    assert result['authority'] == 'syntax-only'
    assert result['fidelity'] == 'attributed-unreviewed'
    assert result['admission'] == 'unresolved' and result['contract'] is None
    worker = result['check']['result']['observation']
    assert 'forallE' in worker['propositionExpr']
    assert worker['sourceModuleOwned'] is True
    assert [a['artifactKind'] for a in result['check']['result']['artifacts']] == [
        'proofir.source-map', 'proofir.interpretation']
    assert (tmp_path / 'Context.lean').read_text() == 'import Lean\n'
    inspected = module().inspect_prose_observation(result, tmp_path)
    assert inspected['status'] == 'validated-historical'
    assert inspected['authority'] == 'none' and inspected['freshCheck'] is False


def test_ill_typed_application_cannot_be_observed(tmp_path, inputs):
    reading, context = inputs
    reading['formula'] = {'tag': 'app', 'symbol': 's', 'args': [{'tag': 'const', 'name': '0'}]}
    reading['symbols'] = {'s': {'leanName': 'Nat.succ', 'leanType': 'Nat → Prop'}}
    result = observe(tmp_path, (reading, context))
    assert result['status'] == 'unavailable'
    assert result['contract'] is None
    assert result['check']['result']['observation']['status'] == 'elaboration-failed'


def test_opaque_interpretation_remains_unsupported(tmp_path, inputs):
    reading, context = inputs
    reading['formula'] = {'tag': 'opaque', 'text': 'some estimate', 'reason': 'unspecified norm'}
    result = observe(tmp_path, (reading, context))
    assert result['status'] == 'unsupported'
    assert result['check']['result']['observation'] is None
    assert result['check']['result']['processReceipts'] == []


@pytest.mark.parametrize('change', ['quote', 'context', 'authority', 'expression', 'extra'])
def test_rehashed_snapshot_tampering_or_staleness_is_rejected(tmp_path, inputs, change):
    result = observe(tmp_path, inputs)
    from ladon.proof_contract_source import snapshot_identity

    if change == 'quote':
        (tmp_path / 'claim.txt').write_text('changed')
    elif change == 'context':
        (tmp_path / 'Context.lean').write_text('import Lean\n-- changed\n')
    elif change == 'expression':
        result['check']['result']['observation']['propositionExpr'] = {'const': 'True', 'levels': []}
    elif change == 'authority':
        result['authority'] = 'fresh-lean-check'
    else:
        result['meaning'] = 'admitted'
    result['snapshotId'] = snapshot_identity(result)
    with pytest.raises(ValueError):
        module().inspect_prose_observation(result, tmp_path)


@pytest.mark.parametrize('key,value', [('scope', 'local-goal'), ('declaration', 'Nat.zero_lt_succ')])
def test_context_cannot_select_a_theorem_or_unbound_scope(tmp_path, inputs, key, value):
    reading, context = deepcopy(inputs)
    context[key] = value
    with pytest.raises(ValueError):
        observe(tmp_path, (reading, context))


def test_memory_stop_is_explicit_and_prevents_progress(tmp_path, inputs, monkeypatch):
    from ladon.process_supervisor import ProcessResult

    calls = []

    def limited(*args, **kwargs):
        calls.append((args, kwargs))
        return ProcessResult((), -1, '', '', 0.01, memory_limited=True,
                             peak_rss_bytes=1024 * 1024)

    monkeypatch.setattr('ladon.proof_contract_obligation_supervision._run', limited)
    result = observe(tmp_path, inputs)
    assert result['status'] == 'unavailable'
    assert result['check']['diagnostic']['code'] == 'memory-limit'
    assert 'Stop progress and report back to the user' in result['check']['diagnostic']['message']
    assert result['check']['result'] is None and len(calls) == 1


def test_public_cli_observe_inspect_and_collision(tmp_path, inputs):
    reading, context = inputs
    for name, value in [('reading', reading), ('context', context)]:
        (tmp_path / (name + '.json')).write_text(json.dumps(value))
    output = tmp_path / 'observed.json'
    args = ['observe-prose-bound', '--root', tmp_path, '--interpretation',
            tmp_path / 'reading.json', '--context', tmp_path / 'context.json',
            '--timeout-seconds', '60', '--output', output]
    produced = invoke(*args)
    assert produced.returncode == 0, produced.stdout + produced.stderr
    frozen = output.read_bytes()
    inspected = invoke('inspect', '--input', output, '--root', tmp_path)
    assert inspected.returncode == 0, inspected.stdout + inspected.stderr
    assert json.loads(inspected.stdout)['authority'] == 'none'
    collision = invoke(*args)
    assert collision.returncode == 2 and output.read_bytes() == frozen
