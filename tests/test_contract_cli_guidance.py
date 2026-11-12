"""CLI guidance distinguishes recognition from original proof inspection."""
import json

from ladon import proof_contract_cli as cli


def test_unsupported_observation_retains_json_and_prints_next_command(tmp_path, monkeypatch, capsys):
    output = tmp_path / 'saved observation.json'
    result = {'status': 'unsupported', 'channel': 'formal', 'observation': {'typeExpr': {}},
              'snapshotId': 'frozen', 'residuals': [{'message': 'telescope-limit'}]}
    monkeypatch.setattr(cli, '_produce', lambda args: result)
    cli.contract_main(['produce', '--channel', 'formal', '--root', str(tmp_path),
                       '--output', str(output)])
    captured = capsys.readouterr()
    assert json.loads(output.read_text()) == result
    assert captured.out == ''
    assert 'Typed Lean statement retained' in captured.err
    assert 'norm-scale-v1' in captured.err
    assert 'contract expand' in captured.err
    assert str(output) in captured.err
    assert 'telescope-limit' in captured.err


def test_missing_observation_does_not_offer_expansion(monkeypatch, capsys):
    result = {'status': 'unavailable', 'channel': 'formal', 'observation': None}
    monkeypatch.setattr(cli, '_produce', lambda args: result)
    cli.contract_main(['produce', '--channel', 'formal', '--root', '.'])
    captured = capsys.readouterr()
    assert json.loads(captured.out) == result
    assert 'contract expand' not in captured.err


def test_expansion_exposes_bounded_native_failure_without_changing_receipt(monkeypatch, capsys):
    result = {'schema': 'ladon-contract-expansion-v1', 'slice': {
        'complete': False, 'status': 'unavailable', 'processReceipts': [
            {'returncode': 1, 'stdout': 'x' * 5000 + '\nerror: expression depth exceeds 64\n',
             'stderr': '', 'memory_limited': False}]}}
    monkeypatch.setattr(cli, '_expand', lambda args: result)
    cli.contract_main(['expand', '--root', '.', '--input', 'observation.json',
                       '--application', 'Example.provider', '--obligation-id', 'premise:1'])
    captured = capsys.readouterr()
    assert json.loads(captured.out) == result
    assert 'expression depth exceeds 64' in captured.err
    assert len(captured.err) < 1800
    assert 'No application route was established' in captured.err


def test_stdout_observation_guidance_requires_saving_before_expansion(monkeypatch, capsys):
    result = {'status': 'unsupported', 'channel': 'formal', 'observation': {'typeExpr': {}},
              'residuals': [{'code': 'telescope-limit', 'message': 'unsupported telescope'}]}
    monkeypatch.setattr(cli, '_produce', lambda args: result)
    cli.contract_main(['produce', '--channel', 'formal', '--root', '.'])
    captured = capsys.readouterr()
    assert json.loads(captured.out) == result
    assert 'Save the JSON observation' in captured.err
    assert 'at most 8 binders' in captured.err


def test_first_failure_is_reported_with_terminal_controls_escaped(monkeypatch, capsys):
    result = {'schema': 'ladon-contract-expansion-v1', 'slice': {
        'complete': False, 'status': 'unavailable', 'processReceipts': [
            {'returncode': 1, 'stdout': '\x1b[31mfirst failure', 'stderr': ''},
            {'returncode': 1, 'stdout': 'later failure', 'stderr': ''}]}}
    monkeypatch.setattr(cli, '_expand', lambda args: result)
    cli.contract_main(['expand', '--root', '.', '--input', 'observation.json',
                       '--application', 'Example.provider', '--obligation-id', 'premise:1'])
    captured = capsys.readouterr()
    assert json.loads(captured.out) == result
    assert 'first failure' in captured.err and 'later failure' not in captured.err
    assert '\x1b' not in captured.err


def test_partial_slice_does_not_claim_no_route(monkeypatch, capsys):
    result = {'schema': 'ladon-contract-expansion-v1', 'slice': {
        'complete': False, 'status': 'partial', 'nodes': [{'id': 'observed'}]}}
    monkeypatch.setattr(cli, '_expand', lambda args: result)
    cli.contract_main(['expand', '--root', '.', '--input', 'observation.json',
                       '--application', 'Example.provider', '--obligation-id', 'premise:1'])
    captured = capsys.readouterr()
    assert json.loads(captured.out) == result
    assert captured.err == ''
