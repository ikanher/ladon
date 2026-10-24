"""Public orchestration boundaries, including source binding without Lean compilation."""
import json
import subprocess
import sys
import time

import pytest
from test_proof_contract_audit_driver import _fixture_plan, _write_plan
from test_proof_contract_worker_scratch import _repo

from ladon.process_supervisor import ProcessResult, run_bounded_target_process
from ladon.resource_limits import memory_limit_message


def _run(*args, **kwargs):
    from ladon.proof_contract_audit import run_contract_audit
    return run_contract_audit(*args, **kwargs)


def test_cli_runs_real_fixture_and_returns_nonzero_for_partial(tmp_path):
    plan = _fixture_plan()
    path = _write_plan(tmp_path / 'plan.json', plan)
    command = [sys.executable, '-m', 'ladon.entrypoint', 'investigation', 'contract',
               'audit', '--input', str(path), '--output-dir', str(tmp_path / 'complete')]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)['status'] == 'completed'
    plan['stages'].append({'id': 'future', 'operation': 'refine', 'request': {}})
    _write_plan(path, plan)
    command[-1] = str(tmp_path / 'partial')
    partial = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    assert partial.returncode == 2, partial.stdout + partial.stderr
    assert json.loads(partial.stdout)['code'] == 'refinement-unavailable'


def test_expired_resume_and_existing_output_do_not_launch(tmp_path, monkeypatch):
    path = _write_plan(tmp_path / 'plan.json', _fixture_plan())
    first = _run(path, tmp_path / 'first', max_stages=1)

    def forbidden(*_args, **_kwargs):
        pytest.fail('expired/colliding work launched')

    with pytest.raises((ValueError, OSError)):
        _run(path, tmp_path / 'first', runner=forbidden)
    monkeypatch.setattr(time, 'monotonic', lambda: first['clock']['deadlineMonotonic'] + 1)
    with pytest.raises((ValueError, OSError)):
        _run(path, tmp_path / 'expired', resume=tmp_path / 'first', runner=forbidden)
    assert not (tmp_path / 'expired').exists()


def test_resume_recovers_published_prefix_when_final_receipt_was_not_written(tmp_path):
    path = _write_plan(tmp_path / 'plan.json', _fixture_plan())
    previous = tmp_path / 'first'
    _run(path, previous, max_stages=1)
    original = (previous / 'stages/propagate.json').read_bytes()
    (previous / 'run.json').unlink()
    result = _run(path, tmp_path / 'recovered', resume=previous)
    assert result['status'] == 'completed'
    assert (previous / 'stages/propagate.json').read_bytes() == original
    assert not (previous / 'run.json').exists()


def test_nested_memory_stop_retains_the_child_cap_and_guidance(tmp_path):
    path = _write_plan(tmp_path / 'plan.json', _fixture_plan())
    calls = []
    message = memory_limit_message(1024**2, 2 * 1024**2)
    body = {'status': 'incomplete', 'diagnostic': {'code': 'memory-limit', 'message': message},
            'processReceipt': {'memoryLimited': True, 'requestedMaxRssBytes': 1024**2,
                               'peakRssBytes': 2 * 1024**2}}

    def memory_worker(command, **_kwargs):
        calls.append(command)
        return ProcessResult(tuple(command), 0, json.dumps({
            'status': 'completed', 'result': body, 'diagnostic': None}), '', .01)

    report = _run(path, tmp_path / 'memory', runner=memory_worker)
    assert report['status'] == 'stopped'
    assert report['code'] == 'memory-limit'
    assert message in report['message']
    assert len(calls) == 1


def _version_only_runner(lake, lean):
    bootstrap = '''import os
from pathlib import Path
from ladon.lean_toolchain import resolve_toolchain_context
import ladon.proof_slice as slices
slices.pinned_toolchain = lambda root: resolve_toolchain_context(
    Path(root), lake_path=Path(os.environ['LADON_TEST_LAKE']),
    lean_path=Path(os.environ['LADON_TEST_LEAN']), environment=os.environ)
from ladon.proof_contract_audit_worker import main
raise SystemExit(main())
'''

    def runner(command, **kwargs):
        assert command[-1] == 'ladon.proof_contract_audit_worker'
        environment = {**kwargs['env'], 'LADON_TEST_LAKE': str(lake),
                       'LADON_TEST_LEAN': str(lean)}
        return run_bounded_target_process([sys.executable, '-c', bootstrap],
            **{**kwargs, 'env': environment})

    return runner


def test_source_binding_resume_rejects_quote_and_lean_mutations(tmp_path):
    root, source, _unrelated, _concurrent, lake, lean, _digest, _context = _repo(tmp_path / 'repo')
    quote = root / 'quote.txt'
    quote.write_bytes(b'original prose')
    plan = _fixture_plan()
    plan.update(repoRoot=str(root), sourceFiles=['quote.txt'])
    path = _write_plan(tmp_path / 'plan.json', plan)
    runner = _version_only_runner(lake, lean)
    first = _run(path, tmp_path / 'first', max_stages=1, runner=runner)
    assert first['status'] == 'partial', first
    quote.write_bytes(b'changed prose')
    with pytest.raises((ValueError, OSError)):
        _run(path, tmp_path / 'changed-quote', resume=tmp_path / 'first', runner=runner)
    quote.write_bytes(b'original prose')
    source.write_bytes(source.read_bytes() + b'\n-- actual source change\n')
    with pytest.raises((ValueError, OSError)):
        _run(path, tmp_path / 'changed-lean', resume=tmp_path / 'first', runner=runner)


def test_source_selection_and_prose_order_are_validated_before_work(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    outside = tmp_path / 'outside.txt'
    outside.write_text('foreign source')
    (root / 'quote.txt').symlink_to(outside)
    plan = _fixture_plan()
    plan.update(repoRoot=str(root), sourceFiles=['quote.txt'])

    def forbidden(*_args, **_kwargs):
        pytest.fail('invalid source plan launched')

    with pytest.raises((ValueError, OSError)):
        _run(_write_plan(tmp_path / 'symlink.json', plan), tmp_path / 'symlink', runner=forbidden)
    assert not (tmp_path / 'symlink').exists()
    ordered = _fixture_plan()
    ordered['stages'].append({'id': 'late-reading', 'operation': 'produce-prose', 'request': {}})
    with pytest.raises((ValueError, TypeError)):
        _run(_write_plan(tmp_path / 'order.json', ordered), tmp_path / 'order', runner=forbidden)
    assert not (tmp_path / 'order').exists()
