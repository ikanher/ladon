"""Actual bounded baseline commands and independent replay retain distinct outcomes."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ladon.evaluation_baselines import _replay_outcome, run_baseline, suggested_tactics
from ladon.evaluation_corpus import digest_bytes
from ladon.evaluation_ladon import run_ladon
from ladon.evaluation_metrics import summarize_method
from ladon.evaluation_process import captured_text, measure_command
from ladon.lean_toolchain import resolve_toolchain_context

FIXTURE = Path(__file__).parent / 'fixtures/lean_integration'
BOUNDS = {'timeoutSeconds': 20, 'maxRssBytes': 32 * 1024 ** 3, 'maxOutputBytes': 1024 ** 2, 'maxCandidates': 4}
CASE = {'module': 'LadonFixture', 'sourceFile': 'LadonFixture.lean', 'goal': 'value = value',
        'localContext': [{'name': 'value', 'type': 'Nat'}], 'pattern': '=',
        'candidatePool': ['LadonFixture.fixtureIdentity', 'LadonFixture.fixtureUsesCore']}


@pytest.mark.skipif(shutil.which('lake') is None, reason='pinned Lean fixture unavailable')
@pytest.mark.parametrize('method', ['exact?', 'apply?', '#check', 'rg', 'editor-search'])
def test_real_baseline_runs_the_registered_goal_and_replays_suggestions(tmp_path, method):
    lean = Path(subprocess.check_output(['elan', 'which', 'lean'], cwd=FIXTURE, text=True).strip())
    context = resolve_toolchain_context(FIXTURE, lean_path=lean, lake_path=lean.with_name('lake'))
    result = run_baseline(method, CASE, context, BOUNDS, tmp_path)
    metrics = summarize_method(result, ['LadonFixture.fixtureIdentity'])
    if method == 'editor-search':
        assert result['status'] == 'unavailable'
        assert metrics['runtimeSeconds'] is None
        return
    assert result['generation']['exitCode'] == 0, captured_text(result['generation'])
    assert result['assessments'], result
    assert any(row['status'] == 'closed' for row in result['assessments']), result
    assert metrics['timeToFirstAcceptedCandidateSeconds'] > 0
    assert metrics['outputBytes'] > 0
    assert metrics['scratchAttempts'] > 0


def test_resource_failures_and_changed_capture_bytes_remain_observed(tmp_path):
    record = measure_command([sys.executable, '-c', 'print("x" * 20000)'], cwd=tmp_path,
                             environment=None, bounds={**BOUNDS, 'maxOutputBytes': 256},
                             output=tmp_path, stem='bounded')
    assert record['status'] == 'failed'
    assert record['outputLimited'] is True
    Path(record['stdoutArtifact']['path']).write_text('changed captured evidence')
    with pytest.raises(ValueError, match='changed'):
        captured_text(record)


@pytest.mark.skipif(shutil.which('lake') is None, reason='pinned Lean fixture unavailable')
def test_ordinary_ladon_adapter_preserves_rejections_and_measures_closed_candidates(tmp_path):
    console = Path(os.environ.get('LADON_CONSOLE', str(Path(sys.executable).with_name('ladon'))))
    lean = Path(subprocess.check_output(['elan', 'which', 'lean'], cwd=FIXTURE, text=True).strip())
    context = resolve_toolchain_context(FIXTURE, lean_path=lean, lake_path=lean.with_name('lake'))
    index = tmp_path / 'index.sqlite'
    build = subprocess.run([str(console), 'proof-search', 'index', 'build', '--repo-root', str(FIXTURE),
                            '--index', str(index), '--format', 'json'], cwd=tmp_path,
                           capture_output=True, text=True, timeout=30, check=False)
    assert build.returncode == 0, build.stderr
    case = {**CASE, 'scope': 'module', 'roots': ['LadonFixture']}
    result = run_ladon(case, context, {**BOUNDS, 'batchSize': 4}, tmp_path,
                       console=console, index=index)
    assert result['status'] == 'passed', result
    metrics = summarize_method(result, ['LadonFixture.fixtureIdentity'])
    assert metrics['verifiedCandidateRecall'] == 1.0
    assert metrics['rejectedCandidates'] >= 1
    assert metrics['invalidSuggestions'] == 0
    assert metrics['scratchReplaySuccessRate'] == 1.0


def test_closed_alternatives_are_not_invalid_because_the_label_set_is_incomplete():
    generation = {'runtimeSeconds': 1.0, 'peakRssSampledBytes': None, 'outputBytes': 30}
    rows = [{'candidate': 'another-valid-proof', 'status': 'closed', 'availableAfterSeconds': 1,
             'scratch': None, 'measurement': None}]
    result = {'method': 'ladon', 'status': 'passed', 'generation': generation, 'assessments': rows}
    metrics = summarize_method(result, ['labeled-proof'])
    assert metrics['verifiedCandidateRecall'] == 0
    assert metrics['incorrectSuggestionRate'] == 0
    assert metrics['peakRssSampledBytes'] is None
    assert metrics['scratchReplaySuccessRate'] is None


def test_partial_and_unassessed_suggestions_are_separate_from_incorrect_proofs():
    generation = {'runtimeSeconds': 1.0, 'peakRssSampledBytes': 100, 'outputBytes': 30}
    rows = [{'candidate': name, 'status': status, 'availableAfterSeconds': 1, 'scratch': None, 'measurement': None}
            for name, status in [('partial', 'partial'), ('wrong', 'invalid'), ('omitted', 'unassessed')]]
    metrics = summarize_method({'method': 'ladon', 'status': 'failed', 'generation': generation,
                                'assessments': rows}, ['expected'])
    assert metrics['incorrectSuggestionRate'] == 0.5
    assert metrics['partialApplications'] == metrics['unassessedCandidates'] == 1
    assert metrics['timeToFirstAcceptedCandidateSeconds'] is None


def test_suggestion_parser_keeps_explicit_reflexivity_and_native_term_suggestions():
    text = 'info: Try this: rfl\nTry this:\n  [apply] exact Some.lemma h\n  unrelated text\n'
    assert suggested_tactics(text) == ['rfl', 'exact Some.lemma h']


def _failed_capture(tmp_path, text):
    path = tmp_path / 'failed.stdout'
    path.write_text(text)
    return {'status': 'failed', 'exitCode': 1, 'runtimeSeconds': 0.1,
            'peakRssSampledBytes': 100, 'outputBytes': len(text.encode()),
            'stdoutArtifact': {'path': str(path), 'digest': digest_bytes(path.read_bytes())}}


def test_missing_import_dependency_does_not_count_as_an_invalid_suggestion(tmp_path):
    record = _failed_capture(tmp_path, "Replay.lean:1:0: error: unknown module prefix 'Batteries'\n")
    assert _replay_outcome(record) == 'unassessed'


def test_nonzero_discovery_exit_preserves_terminal_unassessed_rows(tmp_path, monkeypatch):
    import ladon.evaluation_ladon as adapter

    case = {**CASE, 'scope': 'module', 'roots': ['LadonFixture']}
    request = {key: case[key] for key in ('module', 'goal', 'localContext', 'scope', 'roots')}
    payload = {'schema': 'ladon-verified-discovery-projection-v1', 'status': 'failed', 'request': request,
               'candidates': [{'name': CASE['candidatePool'][0], 'check': {
                   'status': 'unassessed', 'failure': {'stage': 'dependency-state-unavailable'}}}]}
    record = _failed_capture(tmp_path, json.dumps(payload))
    monkeypatch.setattr(adapter, 'measure_command', lambda *_a, **_k: record)
    context = type('Context', (), {'repo_root': FIXTURE, 'environment': {},
                                 'lean_path': tmp_path / 'lean', 'lake_path': tmp_path / 'lake'})()
    result = run_ladon(case, context, {**BOUNDS, 'batchSize': 4}, tmp_path,
                       console=tmp_path / 'ladon', index=tmp_path / 'index.sqlite')
    assert result['status'] == 'failed'
    assert [row['status'] for row in result['assessments']] == ['unassessed']
    assert result['assessments'][0]['failureStage'] == 'dependency-state-unavailable'


def test_partial_terminal_payload_cannot_promote_a_closed_prefix(tmp_path, monkeypatch):
    import ladon.evaluation_ladon as adapter

    case = {**CASE, 'scope': 'module', 'roots': ['LadonFixture']}
    request = {key: case[key] for key in ('module', 'goal', 'localContext', 'scope', 'roots')}
    payload = {'schema': 'ladon-verified-discovery-projection-v1', 'status': 'partial', 'request': request,
               'candidates': [{'name': CASE['candidatePool'][0], 'check': {
                   'status': 'accepted', 'residualPremises': []}}]}
    record = {**_failed_capture(tmp_path, json.dumps(payload)), 'status': 'passed', 'exitCode': 0}
    monkeypatch.setattr(adapter, 'measure_command', lambda *_a, **_k: record)
    monkeypatch.setattr(adapter, '_verify_offered_candidates', lambda *_: pytest.fail('partial prefix cannot promote'))
    context = type('Context', (), {'repo_root': FIXTURE, 'environment': {},
                                 'lean_path': tmp_path / 'lean', 'lake_path': tmp_path / 'lake'})()
    result = run_ladon(case, context, {**BOUNDS, 'batchSize': 4}, tmp_path,
                       console=tmp_path / 'ladon', index=tmp_path / 'index.sqlite')
    assert result['assessments'][0]['status'] == 'unassessed'
    assert summarize_method(result, CASE['candidatePool'])['closedCandidates'] == []
