"""Admission stops must remain honest across interruption and partial-run resume."""
import json

import pytest
from test_proof_contract_audit_boundaries import _version_only_runner
from test_proof_contract_audit_driver import _fixture_plan, _write_plan
from test_proof_contract_worker_scratch import _repo

from ladon.process_supervisor import ProcessResult


def _source_plan(tmp_path):
    root, _source, _other, _concurrent, lake, lean, _hash, _context = _repo(tmp_path / 'repo')
    (root / 'quote.txt').write_text('Selected source')
    plan = _fixture_plan()
    plan.update(repoRoot=str(root), sourceFiles=['quote.txt'])
    return _write_plan(tmp_path / 'plan.json', plan), _version_only_runner(lake, lean)


def _memory_worker(command, **_kwargs):
    return ProcessResult(tuple(command), -9, '', '', .01,
                         memory_limited=True, peak_rss_bytes=13 * 1024**3)


def test_unverified_admission_header_refuses_resume_without_final_report(tmp_path):
    from ladon.proof_contract_audit import run_contract_audit

    path, _runner = _source_plan(tmp_path)
    first = tmp_path / 'first'
    report = run_contract_audit(path, first, runner=_memory_worker)
    assert report['status'] == 'stopped'
    (first / 'run.json').unlink()

    def forbidden(*_args, **_kwargs):
        pytest.fail('unverified admission launched a retry after losing final report')

    with pytest.raises((ValueError, OSError)):
        run_contract_audit(path, tmp_path / 'retry', resume=first, runner=forbidden)
    assert not (tmp_path / 'retry').exists()


def test_resume_binding_stop_references_only_the_preserved_completed_prefix(tmp_path):
    from ladon.proof_contract_audit import run_contract_audit

    path, source_runner = _source_plan(tmp_path)

    def partial_inspect(command, **kwargs):
        job = json.loads(kwargs['input_bytes'])
        if job['analysisId'] == 'inspect':
            return ProcessResult(tuple(command), 0, json.dumps({
                'status': 'completed', 'result': {'status': 'incomplete',
                'code': 'review-needed', 'message': 'Retain the unresolved inspection'},
                'diagnostic': None}), '', .01)
        return source_runner(command, **kwargs)

    prior = tmp_path / 'prior'
    initial = run_contract_audit(path, prior, runner=partial_inspect)
    assert initial['status'] == 'partial'
    original = (prior / 'stages/propagate.json').read_bytes()
    stopped = tmp_path / 'stopped'
    report = run_contract_audit(path, stopped, resume=prior, runner=_memory_worker)
    assert report['status'] == 'stopped'
    assert report['code'] == 'memory-limit'
    assert [row['id'] for row in report['stages']] == ['propagate']
    assert (stopped / 'stages/propagate.json').read_bytes() == original
    assert not (stopped / 'stages/inspect.json').exists()
    assert (prior / 'stages/inspect.json').exists()
