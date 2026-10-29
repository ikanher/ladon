"""Opt-in Task 3.2 public matrix and actual native coefficient/transfer replay."""

import json
import os

import pytest
from real_bound_task32_helpers import (
    FIXTURES,
    admit,
    assert_mutations_rejected,
    assert_not_chain_edge,
    assert_stored,
    check_replay,
    cli,
    compare,
    stale_checks,
)
from test_real_bound_comparison_persistence import analysis
from test_real_bound_prefix_lean import clean_root


def _native_checks(root, first, second, capsys):
    transfer = cli(root, 'transfer', ['compose-real-bounds-proofir', '--left', str(first), '--right', str(second),
                                    '--root', str(root), '--timeout-seconds', '600'])
    assert transfer['authority'] == 'fresh-source-predicate-scalar-and-transfer-checks'
    assert analysis(transfer)['payload']['result']['transferPremises'] == 'assumed'
    assert_stored(transfer, 2)
    assert_mutations_rejected(transfer)
    assert_not_chain_edge(transfer)
    check_replay(root, 'transfer', transfer, 2, capsys)
    coefficient = cli(root, 'coefficient', ['check-real-bound-coefficient-proofir', '--input', str(first),
                                          '--root', str(root), '--timeout-seconds', '600'])
    assert coefficient['authority'] == 'fresh-source-predicate-scalar-and-coefficient-checks'
    assert_stored(coefficient, 1)
    assert_not_chain_edge(coefficient)
    check_replay(root, 'coefficient', coefficient, 1, capsys)


def _matrix(root, first):
    endpoint = admit(root, 'MatrixExamples.endpoint')
    compare(root, 'same-context', first, first, True)
    compare(root, 'equal-loss-distinct-endpoint', first, endpoint, False)
    set_left = admit(root, 'MatrixExamples.setLeft')
    set_right = admit(root, 'MatrixExamples.setRight')
    compare(root, 'set', set_left, set_right, False)
    measure = 'TransferExamples.Functions.measure'
    param_left = admit(root, 'MatrixExamples.paramLeft', measure, ['b0'])
    param_right = admit(root, 'MatrixExamples.paramRight', measure, ['b1'])
    compare(root, 'parameter', param_left, param_right, False)
    pointwise = admit(root, 'MatrixExamples.pointwise')
    compare(root, 'constant-scope', first, pointwise, False)
    result = cli(root, 'incompatible-middle', ['compose-real-bounds-proofir', '--left', str(param_left),
                                              '--right', str(param_right), '--root', str(root),
                                              '--timeout-seconds', '600'], 2)
    assert result['status'] == 'unresolved'
    assert result['authority'] == 'none'
    assert result['relationCheckRun'] is not None
    assert 'artifacts' not in result


@pytest.mark.skipif(os.environ.get('LADON_REAL_BOUND_LIVE_TASK32') != '1',
                    reason='opt-in actual public Task 3.2 qualification')
def test_task32_native_rules_and_public_comparison_matrix(tmp_path, capsys):
    clean_root(tmp_path)
    source = tmp_path / 'TaskExamples.lean'
    source.write_text((FIXTURES / 'TransferExamples.lean').read_text() + '\n' +
                      (FIXTURES / 'MatrixExamples.lean').read_text())
    first = admit(tmp_path, 'TransferExamples.first')
    second = admit(tmp_path, 'TransferExamples.second')
    _native_checks(tmp_path, first, second, capsys)
    _matrix(tmp_path, first)
    stale_checks(tmp_path, source, capsys)
    with capsys.disabled():
        print(json.dumps({'runDirectory': str(tmp_path), 'qualification': 'passed'}))
