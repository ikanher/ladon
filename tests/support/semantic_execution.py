"""Captured toolchain fixtures without touching the current host or toolchain."""
from __future__ import annotations

import hashlib
import json

from ladon.evidence_receipt import build_evidence_receipt
from ladon.proofir_v3 import canonical_bytes, detached_content_id


def with_execution_context(
    artifacts, mode='explicit', *, context=None, encoded_context=None, observed_identity=True,
):
    environment, check = artifacts
    digest = lambda text: 'sha256:' + hashlib.sha256(text.encode()).hexdigest()
    if context is None:
        context = {
            'repositoryRoot': '/historical/repository', 'lakePath': '/historical/bin/lake',
            'leanPath': '/historical/bin/lean', 'pinContent': 'leanprover/lean4:v4.fixture',
            'pinDigest': digest('leanprover/lean4:v4.fixture'), 'lakeIdentity': digest('lake'),
            'leanIdentity': check['payload']['checker']['executableDigest'],
            'sourceTreeIdentity': digest('source'), 'leanRelease': '4.fixture',
            'leanCommit': 'fixture', 'selectionMode': mode, 'environmentKeys': ['PATH'],
            'contextIdentity': digest('captured-redacted-context'),
        }
    environment['payload']['options']['toolchainContext'] = (
        json.dumps(context) if encoded_context is None else encoded_context
    )
    if observed_identity:
        environment['payload']['options']['observedLeanExecutableDigest'] = check['payload']['checker']['executableDigest']
    environment['environmentRef'] = 'sha256:' + hashlib.sha256(canonical_bytes(environment['payload'])).hexdigest()
    environment['artifactId'] = detached_content_id(environment)
    check['environmentRef'] = environment['environmentRef']
    check['payload']['inputs']['environmentRef'] = environment['environmentRef']
    check['payload']['inputs']['artifactRefs'] = [environment['artifactId']]
    receipt = check['extensions']['ladon.process-observation/v1']['evidenceReceipt']
    receipt = build_evidence_receipt(
        subject=receipt['subject'], execution_binding='explicit-pinned' if mode == 'explicit' else 'ambient-observed',
        observation_state=receipt['observationState'], operation_outcome=receipt['operationOutcome'],
        authority_basis=receipt['authorityBasis'], analysis_completeness=receipt['analysisCompleteness'],
        source_freshness=receipt['sourceFreshness'], environment_match=receipt['environmentMatch'],
        environment_ref=environment['environmentRef'], check_run_ref=receipt['checkRunRef'], limitations=receipt['limitations'],
    )
    check['extensions']['ladon.process-observation/v1']['evidenceReceipt'] = receipt
    check['artifactId'] = detached_content_id(check)
    return artifacts, receipt
