"""Shared fixtures that model trusted prior Ladon checker output.

These synthetic receipts test reuse predicates, not receipt-origin
authentication; the repository-local evidence store is a declared trust input.
"""
from __future__ import annotations

import copy
import hashlib
import time

from test_proof_contract_application_probe_contract import TEMPLATE, fixture

from ladon._proof_contract_context_preparation import _digest
from ladon.proof_contract_probe_artifacts import application_probe_artifact


def request(tmp_path):
    data = fixture()
    return {
        'repoRoot': str(tmp_path), 'context': data['context'],
        'left': data['sides'][0], 'right': data['sides'][1],
        'template': TEMPLATE, 'deadlineMonotonic': time.monotonic() + 60,
        'limits': {},
    }


def prepared(request_value):
    artifact = application_probe_artifact(request_value['context'], request_value['left'],
        request_value['right'], request_value['template'], analysis_id='analysis:reuse-test')
    return {
        'status': 'prepared', 'planId': _digest({
            'artifact': artifact['artifactId'], 'root': request_value['repoRoot'],
            'template': request_value['template'],
            'deadline': request_value['deadlineMonotonic'],
            'limits': request_value['limits'],
        }),
        'artifact': artifact, 'goals': copy.deepcopy(artifact['payload']['result']['goals']),
        'binding': {}, 'adapter': {}, 'symbols': {}, 'construction': {},
        'residuals': [],
    }


def cache(tmp_path, request_value, plan_id='sha256:' + 'a' * 64):
    from ladon._proof_contract_route_context_evidence import store_goal_evidence

    data = prepared(request_value)
    plan_id = data['planId'] if plan_id is None else plan_id
    result = {'schema': 'ladon-application-probe-v1',
        'status': 'checked-local-implication', 'planId': plan_id,
        'checkerAuthority': 'checked-local-goals',
        'goals': copy.deepcopy(data['goals']), 'residuals': [],
        'sourceFidelity': 'attributed-unreviewed', 'wholeMethodAuthority': 'none',
        'mathematicalFalsity': 'not-established', 'memoryReportBackRequired': False}
    for goal in result['goals']:
        term = 'by assumption'
        goal.update(status='checked-support', term=term)
        term_digest = 'sha256:' + hashlib.sha256(term.encode()).hexdigest()
        raw = {'status': 'supported', 'completion': {
            'status': 'completed', 'termDigest': term_digest,
            'replay': {'status': 'accepted'}, 'trust': {'accepted': True},
        }, 'ladonApplicationProbeBinding': {
            'planId': plan_id, 'goalId': goal['goalId'],
            'goalDigest': goal['goalDigest'], 'goal': goal['goal'],
            'termDigest': term_digest,
        }}
        goal['result'] = store_goal_evidence(tmp_path, raw)
    return result
