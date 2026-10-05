from __future__ import annotations

import copy
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from support.semantic_evidence import digest, semantic_evidence
from test_proofir_derivation_queries import derivation
from test_semantic_result_projection import _discovery_payload

from ladon.evidence_receipt import (
    build_evidence_receipt,
    validate_evidence_receipt,
)
from ladon.evidence_receipt_readers import stored_check_receipt
from ladon.proof_search_cli import _render_text
from ladon.proof_search_evidence_cli import _dispatch_stored_derivation
from ladon.proof_search_index import ProofSearchIndexError
from ladon.proofir_sqlite_v3 import project_envelopes
from ladon.semantic_projection_fit import _minimal_projection
from ladon.semantic_result_projection import project_semantic_result


@pytest.mark.parametrize('projection', ['llm', 'review'])
def test_discovery_projects_individual_receipts_without_promoting_partial_population(projection: str) -> None:
    payload, registry = _discovery_payload()
    original = copy.deepcopy(payload)
    projected = project_semantic_result(payload, projection=projection, registered_artifacts=registry)
    source = payload['candidates'][0]['check']['evidenceReceipt']
    artifacts = payload['candidates'][0]['check']['artifacts']
    expected = stored_check_receipt(artifacts[1], projection_kind='aggregate', environment_artifacts=artifacts[:1])
    check = projected['candidates'][0]['check']
    assert check['authority'] == {key: expected[key] for key in check['authority']}
    assert check['receiptIdentity'] == expected['receiptIdentity']
    assert check['sourceReceiptIdentity'] == source['receiptIdentity']
    assert projected['status'] == 'partial'
    assert projected['candidates'][1]['check']['receiptIdentity'] is None
    assert payload == original
    text = _render_text(projected)
    assert expected['receiptIdentity'] in text
    assert source['receiptIdentity'] in text
    assert_text_axes(text, check['authority'])


def assert_text_axes(text, authority):
    for field, value in authority.items():
        assert f'{field}={value}' in text


@pytest.mark.parametrize('projection', ['llm', 'review'])
def test_scratch_keeps_separate_authority_and_receipt_in_aggregate_and_minimal_views(projection: str) -> None:
    payload, registry = _discovery_payload()
    artifacts, scratch_registry, receipt = semantic_evidence('scratch', candidate='Main.main', status='compiled', scratch=True)
    registry.update(scratch_registry)
    payload['candidates'][0]['check']['scratch'] = {
        'status': 'compiled', 'evidenceReceipt': receipt, 'artifacts': artifacts,
        'environmentRef': receipt['environmentRef'], 'checkRunRef': receipt['checkRunRef'],
        'sourceDigest': digest('scratch-source:scratch'), 'applicationTerm': 'Main.main',
        'parentCheckRunRef': payload['candidates'][0]['check']['evidenceReceipt']['checkRunRef'],
    }
    payload['coverage']['scratchAttempted'] = 1
    payload['coverage']['scratchCompiled'] = 1
    projected = project_semantic_result(payload, projection=projection, registered_artifacts=registry)
    expected = stored_check_receipt(artifacts[1], projection_kind='aggregate', environment_artifacts=artifacts[:1])
    for view in [projected, _minimal_projection(projected)]:
        scratch = view['candidates'][0]['check']['scratch']
        assert scratch['receiptIdentity'] == expected['receiptIdentity']
        assert scratch['sourceReceiptIdentity'] == receipt['receiptIdentity']
        assert scratch['authority']['observationState'] == 'derived'
        assert scratch['authority']['authorityBasis'] == receipt['authorityBasis']
        text = _render_text(view)
        assert expected['receiptIdentity'] in text
        assert 'authorityBasis=' + receipt['authorityBasis'] in text


def stored_derivation():
    artifact = derivation([('step', ['a', 'b'], 'target')])
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    project_envelopes(connection, [artifact.to_dict()])
    return connection, artifact


def args(artifact, **overrides):
    return SimpleNamespace(**{'kind': 'slice', 'name': artifact.content_id, 'start': 'statement:a', 'end': 'statement:target', 'limit': 100, **overrides})


@pytest.mark.parametrize('kind', ['route', 'slice', 'alternatives'])
@pytest.mark.parametrize('limit', [1, 100])
def test_stored_derivation_receipt_separates_structural_completion_from_checking(kind: str, limit: int) -> None:
    connection, artifact = stored_derivation()
    before = connection.execute('SELECT canonical_json FROM proofir_v3_artifacts').fetchall()
    result = _dispatch_stored_derivation(connection, args(artifact, kind=kind, limit=limit))
    receipt = result['evidenceReceipt']
    validate_evidence_receipt(receipt)
    assert receipt['subject']['artifactRef'] == artifact.content_id
    assert receipt['observationState'] == 'derived'
    assert_no_checker_authority(receipt)
    assert len(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()) <= limit * 4096
    assert result['checkerAcceptance'] == 'not-evaluated'
    if limit == 100:
        assert result['complete']
    assert connection.execute('SELECT canonical_json FROM proofir_v3_artifacts').fetchall() == before
    assert receipt['receiptIdentity'] in _render_text(result)


def assert_no_checker_authority(receipt):
    assert receipt['executionBinding'] == 'none'
    assert receipt['operationOutcome'] == 'not-run'
    assert receipt['authorityBasis'] == 'stored-observation'
    assert receipt['analysisCompleteness'] == 'not-assessed'
    assert receipt['environmentRef'] is None and receipt['checkRunRef'] is None
    assert receipt['sourceFreshness'] == receipt['environmentMatch'] == 'not-assessed'


def test_derivation_receipt_query_identity_binds_start_target_operation_and_bounds() -> None:
    connection, artifact = stored_derivation()
    variants = [{}, {'start': 'statement:b'}, {'end': 'statement:b'}, {'kind': 'slice'}, {'limit': 50}]
    identities = {
        _dispatch_stored_derivation(connection, args(artifact, **{'kind': 'route', **variant}))['evidenceReceipt']['receiptIdentity']
        for variant in variants
    }
    assert len(identities) == len(variants)


def test_invalid_target_has_failed_receipt_without_checker_acceptance() -> None:
    connection, artifact = stored_derivation()
    result = _dispatch_stored_derivation(connection, args(artifact, end='statement:missing'))
    assert result['status'] == 'invalid'
    receipt = result['evidenceReceipt']
    validate_evidence_receipt(receipt)
    assert receipt['observationState'] == 'failed'
    assert receipt['authorityBasis'] == 'not-assessed'
    assert receipt['operationOutcome'] == 'not-run'


def test_derivation_lookup_owner_mismatch_is_rejected() -> None:
    connection, artifact = stored_derivation()
    other = derivation([('other', ['a'], 'target')])
    connection.execute('UPDATE proofir_v3_artifacts SET canonical_json=? WHERE content_artifact_id=?', (json.dumps(other.to_dict()), artifact.content_id))
    with pytest.raises(ProofSearchIndexError, match='content owner'):
        _dispatch_stored_derivation(connection, args(artifact))


@pytest.mark.parametrize('override', [
    {'execution_binding': 'ambient-observed'}, {'operation_outcome': 'accepted'},
    {'environment_match': 'exact'}, {'authority_basis': 'kernel-check'},
])
def test_derivation_query_receipt_rejects_checker_promotions(override: dict) -> None:
    values = {
        'subject': {'queryKind': 'derivation', 'artifactRef': 'sha256:' + 'a' * 64, 'queryIdentity': 'sha256:' + 'b' * 64},
        'execution_binding': 'none', 'observation_state': 'derived', 'operation_outcome': 'not-run',
        'authority_basis': 'stored-observation', 'analysis_completeness': 'not-assessed',
        'environment_match': 'not-assessed',
    }
    with pytest.raises(ValueError):
        build_evidence_receipt(**{**values, **override})


@pytest.mark.parametrize('kind', ['route', 'slice', 'alternatives'])
def test_installed_derivation_console_json_text_receipt_parity(tmp_path: Path, kind: str) -> None:
    artifact = derivation([('step', ['a', 'b'], 'target')])
    path = tmp_path / 'index.sqlite'
    with sqlite3.connect(path) as connection:
        project_envelopes(connection, [artifact.to_dict()])
    console = os.environ.get('LADON_CONSOLE', str(Path(sys.executable).with_name('ladon')))
    command = [console, 'proof-search', 'evidence', kind, artifact.content_id,
               '--repo-root', str(tmp_path), '--index', str(path), '--end', 'statement:target']
    if kind == 'route':
        command.extend(['--start', 'statement:a'])
    outputs = [subprocess.run([*command, '--format', fmt], cwd=tmp_path, capture_output=True,
                             text=True, timeout=10, check=False) for fmt in ['json', 'text']]
    assert [row.returncode for row in outputs] == [0, 0], [row.stderr for row in outputs]
    receipt = json.loads(outputs[0].stdout)['evidenceReceipt']
    validate_evidence_receipt(receipt)
    assert_no_checker_authority(receipt)
    assert receipt['receiptIdentity'] in outputs[1].stdout
    assert 'observationState=derived' in outputs[1].stdout
