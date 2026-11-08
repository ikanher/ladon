from __future__ import annotations

from types import SimpleNamespace

import pytest

from ladon.theorem_capsule_models import CapsuleInvocationError
from ladon.theorem_capsule_replay import replay_theorem_capsule
from ladon.theorem_cli import build_theorem_parser, theorem_main


@pytest.mark.parametrize('timeout', [float('nan'), float('inf'), -float('inf')])
def test_replay_rejects_nonfinite_timeouts_before_content_access(tmp_path, timeout):
    with pytest.raises(CapsuleInvocationError, match='finite'):
        replay_theorem_capsule(tmp_path / 'absent', timeout_seconds=timeout)


def test_cli_rejects_nonfinite_timeout():
    with pytest.raises(SystemExit) as caught:
        build_theorem_parser().parse_args(['replay', 'absent', '--timeout', 'nan'])
    assert caught.value.code == 2


def test_ordered_graph_edges_have_a_finite_population_bound():
    from ladon.theorem_capsule_build import ordered_modules

    plan = SimpleNamespace(target={'module': 'A'}, payload={'buildGraph': {
        'modules': [{'module': 'A'}], 'edges': [{}] * 262145,
    }})
    with pytest.raises(ValueError, match='edge count'):
        ordered_modules(plan)


def test_unsupported_policy_is_not_reported_as_effectively_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr('ladon.theorem_capsule_replay._replay_validated', lambda *_args: {
        'status': 'unsupported-facet', 'stages': [{'stage': 'lean_build'}],
    })
    receipt = replay_theorem_capsule(tmp_path, build_policy='ordered')
    assert receipt['buildPolicy']['requested'] == 'ordered'
    assert receipt['buildPolicy']['effective'] == 'not-enforced'


def test_extract_ordered_policy_requires_verification(tmp_path, monkeypatch):
    def unexpected(*_args, **_kwargs):
        pytest.fail('planning must not start for an ignored build policy')

    monkeypatch.setattr('ladon.theorem_cli.plan_theorem_capsule', unexpected)
    assert theorem_main([
        'extract', 'A.chosen', '--repo-root', str(tmp_path),
        '--output', str(tmp_path / 'capsule'), '--build-policy', 'ordered',
    ]) == 2
