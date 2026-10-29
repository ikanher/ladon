"""Finish stale-source checks against the preserved public qualification artifacts."""

import json
import os
from pathlib import Path

import pytest

from ladon.proof_contract_cli import contract_main


@pytest.mark.skipif(not os.environ.get('LADON_TASK32_EXISTING_ROOT'),
                    reason='requires the preserved Task 3.2 public run after explicit source drift')
@pytest.mark.parametrize('name', ['transfer', 'coefficient'])
def test_saved_public_rule_remains_historical_but_stale_replay_is_invalid(name, capsys):
    root = Path(os.environ['LADON_TASK32_EXISTING_ROOT']).resolve()
    assert (root / 'TaskExamples.lean').read_text().endswith('-- qualification source drift\n')
    path = root / (name + '.json')
    before = path.read_bytes()
    assert contract_main(['inspect', '--input', str(path)]) == 0
    history = json.loads(capsys.readouterr().out)
    assert history['authority'] == 'none' and history['freshCheck'] is False
    assert history['evidenceAuthentication'] == 'not-established'
    assert contract_main(['replay-real-' + name, '--input', str(path), '--root', str(root)]) == 2
    rejection = json.loads(capsys.readouterr().out)
    assert rejection['status'] == 'invalid'
    assert path.read_bytes() == before
