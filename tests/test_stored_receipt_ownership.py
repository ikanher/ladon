from __future__ import annotations

import copy
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from support.semantic_evidence import semantic_evidence

from ladon.evidence_receipt import build_evidence_receipt, validate_evidence_receipt
from ladon.evidence_receipt_readers import stored_check_receipt
from ladon.proofir_sqlite_v3 import project_envelopes
from ladon.proofir_v3 import detached_content_id
from ladon.proofir_v3_queries import query_v3_theorem_evidence
from ladon.semantic_evidence_registry import SemanticEvidenceRegistry


def rebind_receipt(artifacts, **changes):
    check = artifacts[1]
    original = check['extensions']['ladon.process-observation/v1']['evidenceReceipt']
    keys = {
        'execution_binding': 'executionBinding', 'observation_state': 'observationState',
        'operation_outcome': 'operationOutcome', 'authority_basis': 'authorityBasis',
        'analysis_completeness': 'analysisCompleteness', 'source_freshness': 'sourceFreshness',
        'environment_match': 'environmentMatch', 'environment_ref': 'environmentRef',
        'check_run_ref': 'checkRunRef', 'subject': 'subject', 'limitations': 'limitations',
    }
    receipt = build_evidence_receipt(**{**{key: original[field] for key, field in keys.items()}, **changes})
    validate_evidence_receipt(receipt)
    check['extensions']['ladon.process-observation/v1']['evidenceReceipt'] = receipt
    check['artifactId'] = detached_content_id(check)
    return artifacts


@pytest.mark.parametrize('status', ['accepted', 'applicable-with-residuals', 'rejected'])
@pytest.mark.parametrize('field', ['module', 'candidate', 'goal'])
def test_rehashed_stored_receipt_must_match_exact_canonical_subject(status, field):
    artifacts, _, receipt = semantic_evidence(status=status)
    subject = {**copy.deepcopy(receipt['subject']), field: 'Different'}
    rebind_receipt(artifacts, subject=subject)
    with pytest.raises(ValueError):
        stored_check_receipt(artifacts[1])


@pytest.mark.parametrize('changes', [
    {'operation_outcome': 'rejected'},
    {'analysis_completeness': 'partial'},
    {'subject': {'module': 'Main', 'candidate': 'Main.main', 'goal': 'True', 'localContext': [{'name': 'h', 'type': 'False'}]}},
])
def test_rehashed_stored_receipt_cannot_change_check_outcome_or_application_context(changes):
    artifacts, _, _ = semantic_evidence()
    rebind_receipt(artifacts, **changes)
    with pytest.raises(ValueError):
        stored_check_receipt(artifacts[1])


def test_residual_check_cannot_be_relabelled_complete_after_rehash():
    artifacts, _, _ = semantic_evidence(status='applicable-with-residuals')
    rebind_receipt(artifacts, analysis_completeness='complete')
    with pytest.raises(ValueError):
        stored_check_receipt(artifacts[1])


@pytest.mark.parametrize('status', ['compiled', 'failed', 'timeout', 'output-limited', 'memory-limited', 'process-failed'])
def test_scratch_roundtrip_preserves_process_authority(status):
    artifacts, _, original = semantic_evidence(status=status, scratch=True)
    receipt = stored_check_receipt(artifacts[1])
    assert receipt['authorityBasis'] == 'process-observation'
    assert receipt['operationOutcome'] == original['operationOutcome']
    assert receipt['analysisCompleteness'] == 'partial'


@pytest.mark.parametrize('field', ['module', 'goal', 'localContext'])
def test_scratch_receipt_cannot_change_canonical_replay_subject(field):
    artifacts, _, original = semantic_evidence(status='compiled', scratch=True, local_context=({'name': 'h', 'type': 'True'},))
    value = [{'name': 'h', 'type': 'False'}] if field == 'localContext' else 'Different'
    rebind_receipt(artifacts, subject={**original['subject'], field: value})
    with pytest.raises(ValueError):
        stored_check_receipt(artifacts[1])


def test_dossier_rejects_rehashed_accepted_receipt_for_rejected_canonical_check():
    artifacts, _, _ = semantic_evidence(status='rejected')
    rebind_receipt(artifacts, operation_outcome='accepted')
    connection = sqlite3.connect(':memory:')
    project_envelopes(connection, artifacts)
    with pytest.raises(ValueError):
        query_v3_theorem_evidence(connection, 'Main.main', limit=10)


def test_installed_console_rejects_rehashed_receipt_for_another_goal(tmp_path: Path):
    artifacts, _, receipt = semantic_evidence()
    rebind_receipt(artifacts, subject={**receipt['subject'], 'goal': 'False'})
    store = tmp_path / 'evidence.sqlite'
    SemanticEvidenceRegistry(store).register_bundle(artifacts)
    console = os.environ.get('LADON_CONSOLE', str(Path(sys.executable).with_name('ladon')))
    command = [console, 'proof-search', 'evidence', 'semantic-artifact', artifacts[1]['artifactId'],
               '--repo-root', str(tmp_path), '--evidence-store', str(store), '--format', 'json']
    completed = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=10, check=False)
    assert completed.returncode == 1
    assert completed.stdout == ''
    assert json.loads(completed.stderr)['diagnostic']['code'] == 'invalid-stored-evidence-receipt'


def test_provisional_candidate_remains_partial_process_observation():
    artifacts, _, original = semantic_evidence(authority_basis='process-observation', completeness='partial')
    application = next(row for row in artifacts[1]['subjectRefs'] if row['kind'] == 'candidate-application')
    application['searchShape']['processOutcome'] = 'timeout'
    artifacts[1]['payload']['results'][0]['diagnostics'] = [{
        'stage': 'batch-process', 'code': 'timeout', 'pointer': '/process',
        'message': 'partial batch', 'order': 0,
    }]
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    receipt = stored_check_receipt(artifacts[1])
    assert receipt['authorityBasis'] == 'process-observation'
    assert receipt['analysisCompleteness'] == 'partial'
    assert receipt['operationOutcome'] == original['operationOutcome']


def test_missing_receipt_does_not_require_a_semantic_adapter():
    artifacts, _, _ = semantic_evidence()
    artifacts[1]['extensions'] = {}
    artifacts[1]['payload']['operation'] = 'legacy-check'
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    assert stored_check_receipt(artifacts[1]) is None


def test_contradictory_canonical_results_do_not_acquire_accepted_receipt():
    artifacts, _, _ = semantic_evidence()
    artifacts[1]['payload']['results'][1]['result'] = 'rejected'
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    with pytest.raises(ValueError, match='terminal results'):
        stored_check_receipt(artifacts[1])


def test_application_descriptor_must_be_a_declared_check_input():
    artifacts, _, _ = semantic_evidence()
    inputs = artifacts[1]['payload']['inputs']['subjectRefs']
    artifacts[1]['payload']['inputs']['subjectRefs'] = [row for row in inputs if row['kind'] != 'candidate-application']
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    with pytest.raises(ValueError):
        stored_check_receipt(artifacts[1])


def test_receipt_for_an_unregistered_operation_is_rejected():
    artifacts, _, _ = semantic_evidence()
    artifacts[1]['payload']['operation'] = 'different-check'
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    with pytest.raises(ValueError, match='unsupported semantic operation'):
        stored_check_receipt(artifacts[1])
