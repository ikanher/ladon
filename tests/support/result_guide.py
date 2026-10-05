"""Small, real manifest and companion fixtures for guide input contract tests."""
from __future__ import annotations

import copy
import hashlib
import json

from test_result_resolution import inputs
from test_result_resolution import seal as seal_manifest

from ladon.result_manifest_io import content_revision


def revision(kind: str, row: dict) -> str:
    content = {key: value for key, value in row.items() if key != 'revision'}
    encoded = json.dumps(content, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return 'sha256:' + hashlib.sha256(f'ladon-result-guide-v1/{kind}\0'.encode() + encoded).hexdigest()


def reseal(guide: dict) -> dict:
    known = {}
    for step in guide['steps']:
        for dependency in step['prerequisites']:
            if dependency['stepId'] in known:
                dependency['revision'] = known[dependency['stepId']]
        step['revision'] = revision('step', step)
        known[step['id']] = step['revision']
    for citation in guide['citations']:
        if citation['stepId'] in known:
            citation['stepRevision'] = known[citation['stepId']]
        citation['revision'] = revision('citation', citation)
    for review in guide['reviews']:
        if review['stepId'] in known:
            review['stepRevision'] = known[review['stepId']]
    return guide


def guide_inputs() -> tuple[dict, list, dict]:
    manifest, artifacts = inputs()
    claim = manifest['claims'][0]
    target = manifest['targets'][0]
    supporting_claim = copy.deepcopy(claim)
    supporting_claim.update(id='paper-lemma-2', statement='A supporting lemma with an independently authored explanation.')
    supporting_claim['document'] = {'locator': 'example-paper#lemma-2', 'digest': 'sha256:' + '4' * 64}
    supporting_claim['revision'] = content_revision('claim', supporting_claim)
    supporting_target = copy.deepcopy(target)
    supporting_target.update(id='supporting-lemma', name='Example.supporting_lemma')
    supporting_target['revision'] = content_revision('target', supporting_target)
    manifest['claims'].append(supporting_claim)
    manifest['targets'].append(supporting_target)
    seal_manifest(manifest)
    first = {
        'id': 'condition', 'revision': '', 'claimId': claim['id'], 'claimRevision': claim['revision'],
        'targetRevisions': [{'targetId': target['id'], 'revision': target['revision']}],
        'purpose': 'state the sufficient condition',
        'explanation': 'The finite-domain hypothesis supplies the condition used below.',
        'sources': [{'locator': 'example-paper#theorem-1', 'digest': claim['document']['digest']}],
        'author': {'identity': 'fixture-author', 'kind': 'human'}, 'prerequisites': [],
    }
    second = {
        'id': 'argument', 'revision': '', 'claimId': supporting_claim['id'], 'claimRevision': supporting_claim['revision'],
        'targetRevisions': [{'targetId': supporting_target['id'], 'revision': supporting_target['revision']}],
        'purpose': 'explain the argument', 'explanation': 'The supporting argument uses the stated condition.',
        'sources': [{'locator': 'Example.lean:1', 'digest': target['source']['digest']}],
        'author': {'identity': 'fixture-model', 'kind': 'model'},
        'prerequisites': [{'stepId': 'condition', 'revision': ''}],
    }
    first['revision'] = revision('step', first)
    second['prerequisites'][0]['revision'] = first['revision']
    second['revision'] = revision('step', second)
    guide = {
        'schema': 'ladon-result-guide-v1', 'resultId': manifest['resultId'],
        'manifestRevision': manifest['revision'], 'steps': [first, second],
        'citations': [{
            'id': 'paper-citation', 'revision': '', 'stepId': 'condition', 'stepRevision': first['revision'],
            'work': {'id': 'example-paper', 'title': 'An illustrative paper', 'authors': ['A. Author']},
            'locator': 'Theorem 1', 'relationship': 'uses-result',
            'assertion': 'This theorem is used as background.', 'submitter': 'fixture-author',
        }],
        'reviews': [{
            'id': 'review-condition', 'scope': 'explanation', 'stepId': 'condition',
            'stepRevision': first['revision'],
            'targetRevisions': [{'targetId': target['id'], 'revision': target['revision']}],
            'reviewer': {'identity': 'reviewer-1', 'kind': 'human'}, 'status': 'approved',
            'rationale': 'The supplied explanation matches its stated scope.', 'timestamp': '2026-09-29T10:00:00Z',
        }],
    }
    reseal(guide)
    return manifest, artifacts, guide


def clone(value: dict) -> dict:
    return copy.deepcopy(value)
