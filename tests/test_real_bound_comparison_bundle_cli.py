"""Public consumers preserve historical authority and explicit fresh replay."""

import json

import pytest
from test_real_bound_comparison_persistence import recorded

from ladon.proof_contract_cli import contract_main


@pytest.mark.parametrize('operation', ['inspect-real-comparison', 'inspect'])
def test_bundle_offline_cli_inspection(tmp_path, capsys, operation):
    path = tmp_path / 'bundle.json'
    path.write_text(json.dumps(recorded()))
    assert contract_main([operation, '--input', str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'validated-historical'
    assert result['freshCheck'] is False
    assert result['authority'] == 'none'


@pytest.mark.parametrize('operation', ['compare-real-bounds-proofir', 'replay-real-comparison'])
def test_bundle_fresh_cli_dispatch_and_unresolved_exit(tmp_path, monkeypatch, capsys, operation):
    from ladon import real_bound_native_analysis_bundle as bundles

    path = tmp_path / 'value.json'
    path.write_text('{}')
    calls = []

    def fresh(*args, timeout_seconds):
        calls.append((args, timeout_seconds))
        return {'schema': 'ladon-real-bound-analysis-v1', 'status': 'unresolved', 'relation': None}

    monkeypatch.setattr(bundles, 'produce_comparison_bundle', fresh)
    monkeypatch.setattr(bundles, 'replay_comparison_bundle', fresh)
    arguments = (['--left', str(path), '--right', str(path)]
                 if operation == 'compare-real-bounds-proofir' else ['--input', str(path)])
    assert contract_main([operation, *arguments, '--root', str(tmp_path),
                          '--timeout-seconds', '23']) == 2
    assert calls[0][0][-1] == tmp_path
    assert calls[0][1] == 23
    assert json.loads(capsys.readouterr().out)['relation'] is None
