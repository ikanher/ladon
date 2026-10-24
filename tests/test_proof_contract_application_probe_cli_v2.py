"""Ordinary CLI visibility, typed exits and immutable probe output."""
import json

from test_proof_contract_application_probe_boundaries import request

from ladon.proof_contract_cli import contract_main


def test_catalog_publication_is_immutable(tmp_path, capsys):
    output = tmp_path / 'profile.json'
    assert contract_main(['probe-profile', '--output', str(output)]) == 0
    frozen = output.read_bytes()
    assert json.loads(frozen)['regularity-boundary']['implemented'] is True
    witness = json.loads(frozen)['witness-dependence']
    assert witness == {'version': 'witness-dependence-v2', 'implemented': True}
    assert contract_main(['probe-profile', '--output', str(output)]) == 2
    assert output.read_bytes() == frozen
    capsys.readouterr()


def test_expired_probe_exits_two_and_preserves_typed_result(tmp_path, capsys):
    inputs = request()
    inputs['deadlineMonotonic'] = 0
    path = tmp_path / 'request.json'
    path.write_text(json.dumps(inputs))
    assert contract_main(['probe', '--input', str(path)]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'incomplete'
    assert result['diagnostic']['code'] == 'timeout'
    assert result['checkerAuthority'] == 'none'


def test_tiny_probe_capacity_publishes_neither_file_nor_json(tmp_path, capsys):
    inputs = request()
    inputs['limits'] = {'max_output_bytes': 1}
    path, output = tmp_path / 'request.json', tmp_path / 'result.json'
    path.write_text(json.dumps(inputs))
    assert contract_main(['probe', '--input', str(path), '--output', str(output)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ''
    assert 'no result published' in captured.err
    assert not output.exists()
