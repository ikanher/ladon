"""Audit identities must hold across dispatch, not only at resume entry."""
import json

import pytest
from test_proof_contract_audit_boundaries import _run, _version_only_runner
from test_proof_contract_audit_driver import _fixture_plan, _write_plan
from test_proof_contract_worker_scratch import _repo


def test_saved_manifest_is_exact_and_normalization_does_not_hide_input_drift(tmp_path):
    original = _fixture_plan()
    path = _write_plan(tmp_path / 'plan.json', original)
    first = _run(path, tmp_path / 'first', max_stages=1)
    assert (tmp_path / 'first/plan.json').read_bytes() == path.read_bytes()
    changed = _fixture_plan()
    changed['limits'] = first['bounds']
    changed_path = _write_plan(tmp_path / 'changed.json', changed)

    def forbidden(*_args, **_kwargs):
        pytest.fail('a changed input manifest launched work')

    with pytest.raises((ValueError, OSError)):
        _run(changed_path, tmp_path / 'changed', resume=tmp_path / 'first', runner=forbidden)


def test_source_change_after_initial_binding_cannot_be_accepted_as_a_new_baseline(tmp_path):
    root, _source, _other, _concurrent, lake, lean, _hash, _context = _repo(tmp_path / 'repo')
    quote = root / 'quote.txt'
    quote.write_text('original quote')
    plan = _fixture_plan(stages=[_fixture_plan()['stages'][0]])
    plan.update(repoRoot=str(root), sourceFiles=['quote.txt'])
    path = _write_plan(tmp_path / 'plan.json', plan)
    base_runner = _version_only_runner(lake, lean)

    def mutate_before_stage(command, **kwargs):
        if json.loads(kwargs['input_bytes'])['operation'] == 'audit-stage':
            quote.write_text('changed between initial binding and dispatch')
        return base_runner(command, **kwargs)

    try:
        report = _run(path, tmp_path / 'run', runner=mutate_before_stage)
    except (ValueError, OSError):
        return
    assert report['status'] != 'completed', report


def test_runtime_change_during_dispatch_cannot_produce_a_completed_run(tmp_path, monkeypatch):
    import ladon.proof_contract_audit as audit

    identity = audit._runtime_identity()
    observations = []

    def runtime():
        observations.append(True)
        return identity if len(observations) <= 2 else 'sha256:' + '0' * 64

    monkeypatch.setattr(audit, '_runtime_identity', runtime)
    plan = _fixture_plan(stages=[_fixture_plan()['stages'][0]])
    try:
        report = _run(_write_plan(tmp_path / 'plan.json', plan), tmp_path / 'run')
    except (ValueError, OSError):
        return
    assert report['status'] != 'completed', report


def test_oversized_prior_stage_is_rejected_before_unbounded_read(tmp_path, monkeypatch):
    from pathlib import Path

    path = _write_plan(tmp_path / 'plan.json', _fixture_plan())
    _run(path, tmp_path / 'first', max_stages=1)
    stage = tmp_path / 'first/stages/propagate.json'
    with stage.open('r+b') as stream:
        stream.truncate(8 * 1024**2 + 1)
    original_read = Path.read_bytes

    def guarded_read(file):
        if file == stage:
            pytest.fail('oversized prior stage was read without a byte bound')
        return original_read(file)

    monkeypatch.setattr(Path, 'read_bytes', guarded_read)
    with pytest.raises((ValueError, OSError)):
        _run(path, tmp_path / 'resume', resume=tmp_path / 'first')
