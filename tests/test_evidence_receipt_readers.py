from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from support.semantic_evidence import semantic_evidence
from support.semantic_execution import with_execution_context
from test_theorem_lineage_query import lineage_database
from test_theorem_lineage_store import sample_plan

from ladon.evidence_receipt import build_evidence_receipt, validate_evidence_receipt
from ladon.evidence_receipt_readers import stored_query_receipt
from ladon.proof_search_cli import _render_text
from ladon.proof_search_index import (
    build_proof_search_index,
    capture_repository_snapshot,
    inspect_proof_search_index,
)
from ladon.proofir_sqlite_v3 import project_envelopes
from ladon.proofir_v3 import detached_content_id
from ladon.proofir_v3_queries import query_v3_theorem_evidence
from ladon.theorem_lineage_cli import _identity
from ladon.theorem_lineage_cli import _render_text as render_lineage
from ladon.theorem_lineage_projection import ProjectionQuery, project_lineage
from ladon.theorem_lineage_query import LineageQuery, query_lineage
from ladon.theorem_lineage_store import LineageIdentity, ingest_theorem_lineage
from ladon.theorem_lineage_summary import summarize_lineage


@pytest.mark.parametrize('status', ['accepted', 'applicable-with-residuals', 'rejected'])
@pytest.mark.parametrize(('binding', 'mode'), [('explicit-pinned', 'explicit'), ('ambient-observed', 'ambient')])
def test_dossier_projects_check_receipts_without_mutating_canonical_evidence(status: str, binding: str, mode: str) -> None:
    artifacts, _, _ = semantic_evidence(status=status)
    artifacts, _ = with_execution_context(artifacts, mode)
    original = artifacts[1]['extensions']['ladon.process-observation/v1']['evidenceReceipt']
    values = {key: original[key] for key in ['subject', 'environmentRef', 'checkRunRef', 'limitations']}
    original = build_evidence_receipt(
        subject=values['subject'], environment_ref=values['environmentRef'], check_run_ref=values['checkRunRef'],
        limitations=values['limitations'], execution_binding=binding, observation_state='live',
        operation_outcome=original['operationOutcome'], authority_basis=original['authorityBasis'],
        analysis_completeness=original['analysisCompleteness'], source_freshness='stale', environment_match='exact',
    )
    artifacts[1]['extensions']['ladon.process-observation/v1']['evidenceReceipt'] = original
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    project_envelopes(connection, artifacts)
    before = connection.execute('SELECT canonical_json FROM proofir_v3_artifacts ORDER BY content_artifact_id').fetchall()
    dossier = query_v3_theorem_evidence(connection, 'Main.main', limit=10)
    assert dossier['checks']['rows']
    for row in dossier['checks']['rows']:
        receipt = row['evidenceReceipt']
        validate_evidence_receipt(receipt)
        assert receipt == {**original, 'observationState': 'stored', 'receiptIdentity': receipt['receiptIdentity']}
    assert connection.execute('SELECT canonical_json FROM proofir_v3_artifacts ORDER BY content_artifact_id').fetchall() == before
    assert artifacts[1]['extensions']['ladon.process-observation/v1']['evidenceReceipt']['observationState'] == 'live'
    assert 'sourceFreshness=stale' in _render_text(dossier)
    assert 'observationState=stored' in _render_text(dossier)
    assert dossier['evidenceReceipt']['operationOutcome'] == 'not-run'


@pytest.mark.parametrize('override', [
    {'execution_binding': 'explicit-pinned'}, {'operation_outcome': 'accepted'},
    {'authority_basis': 'kernel-check'}, {'analysis_completeness': 'complete'},
    {'environment_match': 'exact'}, {'check_run_ref': 'check:' + 'a' * 64},
])
def test_stored_query_subject_cannot_acquire_checker_authority(override: dict) -> None:
    args = {'subject': {'queryKind': 'theorem-lineage', 'theorem': 'Demo.target', 'sourceRef': None},
            'execution_binding': 'none', 'observation_state': 'stored', 'operation_outcome': 'not-run',
            'authority_basis': 'stored-observation', 'analysis_completeness': 'not-assessed', 'environment_match': 'not-assessed'}
    args.update(override)
    with pytest.raises(ValueError):
        build_evidence_receipt(**args)


def test_lineage_graph_and_summary_preserve_stored_nonchecker_binding() -> None:
    connection, identity = lineage_database()
    raw = query_lineage(connection, identity, LineageQuery(theorem='Demo.target'))
    graph = project_lineage(connection, identity, ProjectionQuery(LineageQuery(theorem='Demo.target'), view='graph'))
    summary = summarize_lineage(connection, identity, 'Demo.target')
    parent = raw['evidenceReceipt']
    assert parent['observationState'] == 'stored'
    assert parent['sourceFreshness'] == 'fresh'
    assert parent['subject']['sourceRef'] == 'lineage:' + raw['closureId']
    for result in [graph, summary]:
        receipt = result['evidenceReceipt']
        validate_evidence_receipt(receipt)
        assert receipt == {**parent, 'observationState': 'derived', 'receiptIdentity': receipt['receiptIdentity']}
        _assert_no_check(receipt)
        assert 'observationState=derived' in render_lineage(result)


def test_lineage_missing_and_stale_receipts_do_not_upgrade_source_or_environment() -> None:
    connection, identity = lineage_database()
    changed = LineageIdentity(**{**identity.__dict__, 'source_fingerprint': 'changed'})
    for reader in [lambda name, ident: query_lineage(connection, ident, LineageQuery(theorem=name)),
                   lambda name, ident: summarize_lineage(connection, ident, name)]:
        missing = reader('Demo.unknown', identity)['evidenceReceipt']
        assert missing['observationState'] == 'absent'
        assert missing['authorityBasis'] == 'not-assessed'
        stale = reader('Demo.target', changed)['evidenceReceipt']
        assert stale['sourceFreshness'] == 'stale'
        assert stale['environmentMatch'] == 'not-assessed'
        assert stale['operationOutcome'] == 'not-run'


def test_dossier_rejects_mismatched_owner_even_when_receipt_is_rehashed() -> None:
    artifacts, _, _ = semantic_evidence()
    extension = artifacts[1]['extensions']['ladon.process-observation/v1']
    extension['evidenceReceipt']['checkRunRef'] = 'check:' + 'e' * 64
    body = {key: value for key, value in extension['evidenceReceipt'].items() if key != 'receiptIdentity'}
    extension['evidenceReceipt']['receiptIdentity'] = 'sha256:' + hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(',', ':')).encode(),
    ).hexdigest()
    validate_evidence_receipt(extension['evidenceReceipt'])
    # The owner check is separate from canonical receipt identity validation.
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    connection = sqlite3.connect(':memory:')
    project_envelopes(connection, artifacts)
    with pytest.raises(ValueError, match='canonical check owner'):
        query_v3_theorem_evidence(connection, 'Main.main', limit=10)


def test_missing_dossier_does_not_claim_a_check_or_complete_analysis() -> None:
    dossier = query_v3_theorem_evidence(sqlite3.connect(':memory:'), 'Missing', limit=1)
    receipt = dossier['evidenceReceipt']
    assert receipt == stored_query_receipt('theorem-evidence', 'Missing', observed=False)
    assert receipt['operationOutcome'] == 'not-run'
    assert receipt['observationState'] == 'absent'


@pytest.mark.parametrize('view', ['summary', 'routes', 'graph'])
def test_installed_lineage_reader_preserves_receipt_in_json_and_text(tmp_path: Path, view: str) -> None:
    repo = tmp_path / 'repo'
    repo.mkdir()
    (repo / 'Demo.lean').write_text('namespace Demo\ntheorem target : True := by trivial\nend Demo\n')
    built = build_proof_search_index(repo)
    index = built.index_path
    status = inspect_proof_search_index(repo, index_path=index, verify_sources=True)
    identity = _identity(repo, capture_repository_snapshot(repo), status)
    with sqlite3.connect(index) as connection:
        ingest_theorem_lineage(connection, sample_plan(), identity)
    console = os.environ.get('LADON_CONSOLE', str(Path(sys.executable).with_name('ladon')))
    command = [console, 'theorem', 'lineage', 'Demo.target', '--repo-root', str(repo), '--index', str(index),
               '--refresh', 'never', '--view', view, '--from', 'trust', '--output', '-']
    outputs = [subprocess.run([*command, '--format', fmt], cwd=tmp_path, text=True, capture_output=True,
                              timeout=15, check=False) for fmt in ['json', 'text']]
    assert all(row.returncode == 0 for row in outputs), [row.stderr for row in outputs]
    payload = json.loads(outputs[0].stdout)
    receipt = payload['evidenceReceipt']
    assert receipt['operationOutcome'] == 'not-run'
    assert receipt['executionBinding'] == 'none'
    assert receipt['receiptIdentity'] in outputs[1].stdout
    for field in ['executionBinding', 'observationState', 'operationOutcome', 'sourceFreshness',
                  'environmentMatch', 'authorityBasis', 'analysisCompleteness']:
        assert f'{field}={receipt[field]}' in outputs[1].stdout
    assert payload['refresh']['performed'] is False


def _assert_no_check(receipt: dict) -> None:
    assert receipt['executionBinding'] == 'none'
    assert receipt['operationOutcome'] == 'not-run'
    assert receipt['analysisCompleteness'] == 'not-assessed'
    assert receipt['checkRunRef'] is None
    assert receipt['environmentRef'] is None
    assert receipt['environmentMatch'] == 'not-assessed'
