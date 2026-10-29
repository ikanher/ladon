"""Native Real chains retain individually checked edges and exact shared owners."""

import json
import sqlite3

import pytest
from test_real_bound_comparison_persistence import analysis, rehash_artifact
from test_real_bound_prefix_persistence import recorded as prefix_bundle

from ladon.proof_contract_cli import contract_main
from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.proofir_v3 import validate_envelope_batch


def recorded():
    from ladon.real_bound_native_chain_artifacts import recorded_chain

    return recorded_chain([prefix_bundle()])


def test_prefix_edge_survives_chain_storage():
    bundle = recorded()
    p = analysis(bundle)['payload']
    assert bundle['schema'] == 'ladon-real-bound-chain-bundle-v1'
    assert bundle['authority'] == 'none'
    assert p['stage'] == 'propagation'
    assert p['analysisKind'] == 'real-bound-chain-v1'
    assert p['rules'] == ['order-prefix-v1']
    assert p['result']['authority'] == 'none'
    assert p['result']['endpointTheorem'] == 'not-checked'
    assert len(p['edgeAnalysisRefs']) == len(p['checkRunRefs']) == 1
    validate_envelope_batch(bundle['artifacts'])


def test_chain_sqlite_keeps_contract_positions_without_inventing_derivation():
    bundle = recorded()
    row = analysis(bundle)
    db = sqlite3.connect(':memory:')
    project_envelopes(db, bundle['artifacts'])
    validate_v3_database(db)
    inputs = db.execute('SELECT contract_owner,contract_local_id FROM proofir_v3_contract_analysis_inputs '
                        'WHERE owner_artifact_id=? ORDER BY ordinal', (row['artifactId'],)).fetchall()
    assert inputs == [(r['artifactRef'], r['localId']) for r in row['payload']['contractRefs']]
    assert db.execute('SELECT * FROM proofir_v3_contract_analysis_derivations WHERE owner_artifact_id=?',
                      (row['artifactId'],)).fetchall() == []
    assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def test_disconnected_edges_cannot_form_a_chain():
    from ladon.real_bound_native_chain_artifacts import recorded_chain

    edge = prefix_bundle()
    with pytest.raises(ValueError, match='adjacent|middle|chain'):
        recorded_chain([edge, edge])


@pytest.mark.parametrize('mutation', ['middle', 'rule', 'edge-kind', 'missing-edge', 'fresh', 'endpoint'])
def test_rehashed_chain_cannot_invent_proof(mutation):
    bundle = recorded()
    target = analysis(bundle)
    p = target['payload']
    if mutation == 'middle':
        p['contractRefs'].reverse()
    elif mutation == 'rule':
        p['rules'][0] = 'identity-v1'
    elif mutation == 'edge-kind':
        p['edgeAnalysisRefs'][0] = p['contractRefs'][0]
    elif mutation == 'missing-edge':
        owner = p['edgeAnalysisRefs'][0]['artifactRef']
        bundle['artifacts'] = [r for r in bundle['artifacts'] if r['artifactId'] != owner]
    elif mutation == 'fresh':
        p['result']['authority'] = 'fresh-lean-check'
    else:
        p['result']['endpointTheorem'] = 'checked'
    rehash_artifact(target)
    with pytest.raises(ValueError):
        validate_envelope_batch(bundle['artifacts'])


@pytest.mark.parametrize('operation', ['inspect-real-chain', 'inspect'])
def test_cli_inspection_remains_historical(tmp_path, capsys, operation):
    path = tmp_path / 'chain.json'
    path.write_text(json.dumps(recorded()))
    assert contract_main([operation, '--input', str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['authority'] == 'none'
    assert result['freshCheck'] is False
    assert result['evidenceAuthentication'] == 'not-established'


@pytest.mark.parametrize('count', [0, 128])
def test_edge_count_rejected_before_reconstruction(count):
    from ladon.real_bound_native_chain_artifacts import recorded_chain

    with pytest.raises(ValueError):
        recorded_chain([{}] * count)
