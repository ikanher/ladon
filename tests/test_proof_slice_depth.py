"""Explicit depth limits govern native extraction and saved evidence."""
import json
from pathlib import Path

import pytest

from ladon.correspondence_cli import proof_slice_main
from ladon.proof_slice import extract_proof_slice
from ladon.proof_slice_limits import DEFAULT_MAX_DEPTH
from ladon.proof_slice_validation import validate_slice_shape

ROOT = Path(__file__).parent / 'fixtures/correspondence_m1'


@pytest.mark.parametrize('value', [0, -1, True, 1.5, '128', 4097])
def test_invalid_depth_is_rejected_before_repository_access(value):
    with pytest.raises(ValueError, match='depth budget'):
        extract_proof_slice('/nonexistent', 'Proof.lean', 'Proof', 'Example', 'provider',
                            max_depth=value)


@pytest.mark.parametrize('scoped', [False, True])
def test_native_depth_failure_and_cli_override(scoped, tmp_path):
    args = ['--repo', str(ROOT), '--source', 'Proof.lean', '--module', 'Proof',
            '--declaration', 'Correspondence.term', '--application', 'bridge']
    if scoped:
        args += ['--scoped']
    for depth, expected in [(1, 2 if scoped else 0), (256, 0)]:
        output = tmp_path / f'{depth}.json'
        assert proof_slice_main(args + ['--max-depth', str(depth), '--output', str(output)]) == expected
        result = json.loads(output.read_text())
        assert result['limits']['depth'] == depth
        if expected:
            assert 'expression depth exceeds 1' in result['processReceipts'][-1]['stdout']
        else:
            validate_slice_shape(result)
    assert DEFAULT_MAX_DEPTH == 128


def test_contract_expand_cli_forwards_explicit_depth(monkeypatch, capsys):
    from ladon import proof_contract_cli as cli

    observed = []

    def expand(args):
        observed.append(args.max_depth)
        return {'status': 'unavailable'}

    monkeypatch.setattr(cli, '_expand', expand)
    cli.contract_main(['expand', '--root', '.', '--input', 'saved.json',
                       '--application', 'Example.provider', '--obligation-id', 'premise:1',
                       '--max-depth', '1024'])
    capsys.readouterr()
    assert observed == [1024]
