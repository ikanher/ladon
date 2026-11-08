from __future__ import annotations

from types import SimpleNamespace

from ladon.process_supervisor import ProcessResult
from ladon.theorem_capsule_build import run_ordered_build


def _plan():
    return SimpleNamespace(target={'module': 'A'}, payload={
        'buildGraph': {'modules': [{'module': 'A'}], 'edges': []},
    })


def test_ordered_build_refuses_unbuilt_imports_after_preflight_failure(tmp_path):
    calls = []

    def run_stage(command, *_args, **_kwargs):
        calls.append(command)
        return {'status': 'Lean-rejected', 'result': ProcessResult(
            tuple(command), 3, 'dependency needs rebuild', '', 0.1), 'row': {'returncode': 3}}

    result = run_ordered_build(_plan(), tmp_path, 5, 1000, {}, run_stage)
    assert result['status'] == 'unsupported-facet'
    assert calls == [['lake', '--no-build', 'build', '+A:deps']]


def test_ordered_build_does_not_launch_module_after_shared_deadline(tmp_path, monkeypatch):
    times = iter((0.0, 0.1, 6.0))
    monkeypatch.setattr('ladon.theorem_capsule_build.monotonic', lambda: next(times))
    calls = []

    def run_stage(command, *_args, **_kwargs):
        calls.append(command)
        return {'status': None, 'result': ProcessResult(tuple(command), 0, '', '', 0.1), 'row': {}}

    result = run_ordered_build(_plan(), tmp_path, 5, 1000, {}, run_stage)
    assert result['status'] == 'resource-limit'
    assert len(calls) == 1
    assert result['row']['steps'][-1]['timeoutBeforeLaunch'] is True
