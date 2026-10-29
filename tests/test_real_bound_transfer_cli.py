"""CLI routing controls; actual native proof qualification is a separate live gate."""

import json

import pytest

from ladon.proof_contract_cli import contract_main


@pytest.mark.parametrize('operation', ['compose-real-bounds', 'compose-real-bounds-proofir', 'replay-real-transfer'])
def test_transfer_cli_preserves_unresolved_status(tmp_path, capsys, monkeypatch, operation):
    from ladon import real_bound_native_transfer as live
    from ladon import real_bound_native_transfer_bundle as bundles

    path = tmp_path / 'input.json'
    path.write_text('{}')
    calls = []

    def check(*args, timeout_seconds):
        calls.append((args, timeout_seconds))
        return {'schema': 'ladon-real-bound-transfer-analysis-v1', 'status': 'unresolved', 'authority': 'none'}

    monkeypatch.setattr(live, 'check_transfer_composition', check)
    monkeypatch.setattr(bundles, 'produce_transfer_bundle', check)
    monkeypatch.setattr(bundles, 'replay_transfer_bundle', check)
    flags = ['--input', str(path)] if operation == 'replay-real-transfer' else ['--left', str(path), '--right', str(path)]
    assert contract_main([operation, *flags, '--root', str(tmp_path), '--timeout-seconds', '37']) == 2
    assert calls[0][1] == 37
    assert json.loads(capsys.readouterr().out)['status'] == 'unresolved'
