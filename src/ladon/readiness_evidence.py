"""Resolve readiness claims against independently selected acceptance contracts.

This adapter verifies recorded execution bytes and coverage through the child
acceptance owner. It does not authenticate producers or infer public release
authority. External studies and owner decisions need separate validators.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from ladon.child_acceptance import _json_object, _read_evidence, validate_child_bundle

SCOPE = ('candidateIdentity', 'sourceTreeIdentity', 'wheelDigest', 'producerIdentity',
         'environmentRef', 'workingDirectory')
CONTRACT_KINDS = frozenset(('installedSmoke', 'adversarialContract', 'resourceGate',
                          'platformPosture'))


def verify_readiness_evidence(name, row, root, inventories, requirements) -> None:
    """Require exact receipt scope, both runtimes and independently named test nodes."""
    if name not in CONTRACT_KINDS:
        raise ValueError('this evidence class has no qualified external-study or owner-decision validator')
    if root is None or inventories is None or requirements is None:
        raise ValueError('readiness requires evidence bytes and independently selected contracts')
    inventory = inventories[name]
    receipt = _object(root, row['receiptArtifactRef'])
    validate_child_bundle(receipt, bundle_root=Path(root), inventory=inventory)
    evidence = _read_evidence(receipt['evidenceFiles'], Path(root))
    _verify_scope(row, receipt, evidence)
    nodes = requirements[name]
    if not nodes or any(_help_only(node) for node in nodes):
        raise ValueError('readiness requires semantic test nodes rather than help-only coverage')
    results = [_json_object(evidence[ref]) for ref in row['resultArtifactRefs']]
    _verify_named_executions(row, results, nodes)
    _verify_execution_times(row, results)


def _verify_scope(row, receipt, evidence) -> None:
    if any(row[field] != receipt[field] for field in SCOPE):
        raise ValueError('readiness claim crosses receipt execution scope')
    candidate = _json_object(evidence[receipt['candidateArtifactRef']])
    if row['candidateCommit'] != candidate.get('candidateCommit'):
        raise ValueError('readiness claim names a different candidate revision')
    if row['resultArtifactRefs'] != receipt['resultArtifactRefs'] or row['logArtifactRefs'] != receipt['logArtifactRefs']:
        raise ValueError('readiness claim names different execution results or logs')


def _help_only(node) -> bool:
    name = node.rsplit('::', 1)[-1].split('[', 1)[0]
    return '--help' in node or re.search(r'(^|_)help($|_)', name) is not None


def _verify_execution_times(row, results) -> None:
    finished = []
    for result in results:
        start = datetime.fromisoformat(result['startedAt'])
        end = datetime.fromisoformat(result['completedAt'])
        if start.utcoffset() is None or end.utcoffset() is None or start > end:
            raise ValueError('readiness execution timestamps are invalid')
        finished.append(end)
    if datetime.fromisoformat(row['timestamp']) != max(finished):
        raise ValueError('readiness freshness timestamp differs from recorded execution')


def _object(root, reference):
    objects = _read_evidence([{'digest': reference, 'path': 'objects/' + reference.removeprefix('sha256:')}], Path(root))
    return _json_object(objects[reference])


def _verify_named_executions(row, results, nodes) -> None:
    first = results[0]
    if row['commandVector'] != first['commandVector'] or row['command'] != first['command']:
        raise ValueError('readiness claim command differs from recorded execution')
    for result in results:
        for node in nodes:
            if not any(found == node or found.startswith(node + '[') for found in result['passed']):
                raise ValueError('readiness named test was not passed on every supported runtime: ' + node)
