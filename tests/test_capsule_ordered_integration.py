from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ladon.process_supervisor import run_bounded_target_process
from ladon.theorem_capsule_materialization import materialize_theorem_capsule
from ladon.theorem_capsule_planning import plan_theorem_capsule
from ladon.theorem_capsule_replay import replay_theorem_capsule


@pytest.fixture(scope='module')
def ordered_capsule(tmp_path_factory):
    base = tmp_path_factory.mktemp('capsule-ordered-integration')
    repo = base / 'original'
    shutil.copytree(Path(__file__).parent / 'fixtures' / 'capsule_ordered', repo)
    build = run_bounded_target_process(
        ['lake', 'build', '+Budget:leanArts'], cwd=repo,
        timeout_seconds=60, max_rss_bytes=6 * 1024**3, max_output_bytes=1024**2,
    )
    assert build.succeeded, build.stdout + build.stderr
    plan = plan_theorem_capsule(repo, 'Budget.chosen', max_rss_bytes=6 * 1024**3)
    capsule = base / 'capsule'
    materialize_theorem_capsule(plan, capsule)
    repo.rename(base / 'original-unavailable')
    return capsule


def test_ordered_replay_verifies_diamond_after_original_is_unavailable(ordered_capsule):
    receipt = replay_theorem_capsule(
        ordered_capsule, build_policy='ordered', timeout_seconds=60,
        max_rss_bytes=6 * 1024**3,
    )
    assert receipt['status'] == 'verified', receipt
    assert all(receipt['comparisons']['checks'].values())
    assert receipt['buildPolicy']['effective'] == 'ordered'
    build = next(row for row in receipt['stages'] if row['stage'] == 'lean_build')
    assert build['resourceObservations']['maxLeanProcesses'] == 1
    assert len(build['steps']) == 8


def test_ordered_replay_rejects_mutation_before_build(ordered_capsule, tmp_path):
    capsule = tmp_path / 'capsule'
    shutil.copytree(ordered_capsule, capsule)
    with (capsule / 'Budget.lean').open('a') as stream:
        stream.write('\n-- mutation\n')
    receipt = replay_theorem_capsule(capsule, build_policy='ordered')
    assert receipt['status'] == 'content-invalid'
    assert receipt['buildPolicy']['effective'] == 'not-started'


def test_ordered_build_success_still_rejects_theorem_identity_mismatch(ordered_capsule, monkeypatch):
    def changed_helper(plan, *_args, **_kwargs):
        nodes = [dict(row) for row in plan.payload['semanticGraph']['nodes']]
        target = next(row for row in nodes if row['name'] == plan.target['name'])
        target['typeFingerprint'] = 'changed'
        return {
            'status': None, 'row': {'stage': 'theorem_query', 'returncode': 0},
            'payload': {'target': plan.target['name'],
                        'leanVersion': plan.payload['toolchain']['leanVersion'], 'nodes': nodes},
        }

    monkeypatch.setattr('ladon.theorem_capsule_replay._run_replay_helper', changed_helper)
    receipt = replay_theorem_capsule(
        ordered_capsule, build_policy='ordered', timeout_seconds=60,
        max_rss_bytes=6 * 1024**3,
    )
    assert receipt['status'] == 'identity-mismatch'
    assert not all(receipt['comparisons']['checks'].values())
