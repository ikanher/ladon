"""Real diagnostic branches with simulated I/O; no Lean acceptance is fabricated."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from ladon import correspondence_check as checker
from ladon.correspondence_evidence import completion_artifacts
from ladon.lean_toolchain import LeanToolchainContext
from ladon.process_supervisor import ProcessResult
from ladon.proofir_correspondence import _as_exact_decimal_strings
from ladon.proofir_v3 import ProofIRV3Error, canonical_bytes, validate_envelope_batch


@pytest.fixture
def diagnostic_run(tmp_path, monkeypatch):
    typed = ProcessResult((sys.executable,), 0, 'LADON_TYPED_SUBJECT ' + json.dumps(
        {'subject': {'structural': 'original'}}), '', 0.0)
    toolchain = LeanToolchainContext(tmp_path, Path(sys.executable), Path(sys.executable),
        'fixture', 'pin', 'lake', 'lean', 'source', 'fixture', None, 'explicit', (), {})
    execution = SimpleNamespace(command=[sys.executable], environment={})
    monkeypatch.setattr(checker, '_verify_prepared_inputs', lambda *args: None)
    monkeypatch.setattr(checker, '_generated_prelude', lambda *args: 'import Lean\n')
    monkeypatch.setattr(checker, 'prepare_direct_lean_execution', lambda *_args, **_kwargs: execution)
    monkeypatch.setattr(checker, 'run_bounded_target_process', lambda *_args, **_kwargs: typed)
    monkeypatch.setattr(checker, 'pinned_toolchain', lambda *args: toolchain)
    monkeypatch.setattr(checker, 'complete_source_goal', lambda *_args, **_kwargs: pytest.fail(
        'diagnostics must stop before completion'))

    def run(code, count):
        capture = {'schema': 'ladon-source-goal-capture-result-v1',
                   'operation': 'capture-source-goal',
                   'status': 'captured' if code != 'capture-failure' else 'failed',
                   'capture': {'environment': {'compiledInventory': {
                       'modules': [{'module': f'M{i}'} for i in range(count)]}},
                       'goal': {'typeStructural': 'different', 'localContext': [
                           {'implementationDetail': False}]}}}
        monkeypatch.setattr(checker, 'capture_source_goal', lambda *_args, **_kwargs: capture)
        prepared = object() if code == 'prepared-goal-subject-mismatch' else None
        result = checker._check_goal('True', 'True.intro', tmp_path, b'import Lean\n',
                                     {}, toolchain, prepared=prepared)
        return {'obligation': 'interpretation', 'mode': 'prove', 'goal': 'True', **result}
    return run


def artifacts(row):
    plan = {'planId': 'control', 'slice': {'environment': 'sha256:' + '1' * 64,
                                        'selection': {'declaration': 'selected'}}}
    return completion_artifacts(plan, {'checks': [row],
                                      'implementationDigest': 'sha256:' + '2' * 64})[0]


@pytest.mark.parametrize('code', ['prepared-goal-subject-mismatch',
                                  'unexpected-generated-goal-context', 'capture-failure'])
@pytest.mark.parametrize('count', [10001, 32768])
def test_large_diagnostic_retains_unresolved_evidence(diagnostic_run, code, count):
    row = diagnostic_run(code, count)
    assert row['status'] == 'unresolved'
    assert row['goalOrigin'] == 'generated-correspondence-obligation'
    assert 'completion' not in row
    produced = artifacts(row)
    validate_envelope_batch(produced)
    check = produced[0]['payload']
    assert check['results'][0]['result'] == 'unknown'
    assert check['guarantee']['scope'] == 'none'
    if code != 'capture-failure':
        assert check['results'][0]['diagnostics'][0]['code'] == code


@pytest.mark.parametrize('code', ['prepared-goal-subject-mismatch',
                                  'unexpected-generated-goal-context', 'capture-failure'])
def test_large_diagnostic_still_obeys_inventory_cap(diagnostic_run, code):
    with pytest.raises(ProofIRV3Error, match='32768'):
        artifacts(diagnostic_run(code, 32769))


def test_diagnostic_exception_does_not_relax_other_bounds(diagnostic_run):
    row = _as_exact_decimal_strings(diagnostic_run('unexpected-generated-goal-context', 10001))
    with pytest.raises(ProofIRV3Error, match='byte'):
        canonical_bytes(row, max_bytes=100)
    row['unrelated'] = [None] * 10001
    with pytest.raises(ProofIRV3Error, match='10000'):
        canonical_bytes(row)
