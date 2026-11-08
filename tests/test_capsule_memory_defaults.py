from __future__ import annotations

import pytest

from ladon.theorem_capsule_replay import replay_theorem_capsule
from ladon.theorem_cli import build_theorem_parser, theorem_main


@pytest.mark.parametrize('arguments', [
    ['plan', 'A.chosen'], ['replay', 'capsule'],
    ['extract', 'A.chosen', '--output', 'capsule', '--verify'],
])
def test_capsule_commands_default_to_twelve_gib(arguments):
    args = build_theorem_parser().parse_args(arguments)
    assert args.max_rss_mib == 12288


def test_replay_service_default_is_twelve_gib(tmp_path, monkeypatch):
    limits = []

    def replay(_capsule, _timeout, max_rss_bytes, _network, _policy):
        limits.append(max_rss_bytes)
        return {'status': 'resource-limit', 'stages': [{'stage': 'lean_build'}]}

    monkeypatch.setattr('ladon.theorem_capsule_replay._replay_validated', replay)
    receipt = replay_theorem_capsule(tmp_path, build_policy='ordered')
    assert limits == [12 * 1024**3]
    assert receipt['resourceLimits']['maxProcessTreeRssBytes'] == 12 * 1024**3


def test_cli_forwards_default_twelve_gib_for_ordered_replay(tmp_path, monkeypatch, capsys):
    limits = []

    def replay(*_args, **kwargs):
        limits.append(kwargs['max_rss_bytes'])
        return {'status': 'resource-limit', 'stages': []}

    monkeypatch.setattr('ladon.theorem_capsule_replay.replay_theorem_capsule', replay)
    assert theorem_main(['replay', str(tmp_path), '--build-policy', 'ordered', '--format', 'json']) == 1
    capsys.readouterr()
    assert limits == [12 * 1024**3]
