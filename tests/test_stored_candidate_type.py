"""Stored explanation must consume one attributed rendered declaration type."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from ladon.stored_candidate_type import candidate_type_evidence


def _artifact():
    structural = 'Lean.Expr.const `True []'
    identity = 'sha256:' + hashlib.sha256(json.dumps({'qualifiedName': 'Demo.proof', 'type': structural}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'subjectRefs': [{'kind': 'declaration', 'display': 'Demo.proof',
                            'localId': 'declaration:' + identity,
                            'fingerprint': {'scheme': {'name': 'lean-declaration-identity', 'version': '1'}, 'digest': identity},
                            'searchShape': {'renderedType': 'True', 'typeStructural': structural,
                                            'typeStatus': 'lean-rendered', 'typeTextTruncated': False}}]}


def test_stored_type_keeps_exact_declaration_and_type_identity():
    result = candidate_type_evidence(_artifact(), 'Demo.proof')
    assert result['typeText'] == 'True'
    assert result['candidateName'] == 'Demo.proof'
    assert result['typeTextTruncated'] is False


@pytest.mark.parametrize('mutation', ['missing', 'wrong-name', 'ambiguous', 'missing-type', 'blank',
                                      'truncated', 'unavailable', 'structural-mismatch', 'wrong-local-id'])
def test_stored_type_rejects_missing_ambiguous_or_mismatched_evidence(mutation):
    artifact = copy.deepcopy(_artifact())
    row = artifact['subjectRefs'][0]
    actions = {
        'missing': lambda: artifact['subjectRefs'].clear(),
        'wrong-name': lambda: row.__setitem__('display', 'Other.proof'),
        'ambiguous': lambda: artifact['subjectRefs'].append(copy.deepcopy(row)),
        'missing-type': lambda: row.pop('searchShape'),
        'blank': lambda: row['searchShape'].__setitem__('renderedType', ' '),
        'truncated': lambda: row['searchShape'].__setitem__('typeTextTruncated', True),
        'unavailable': lambda: row['searchShape'].__setitem__('typeStatus', 'unavailable'),
        'structural-mismatch': lambda: row['searchShape'].__setitem__('typeStructural', 'Bool'),
        'wrong-local-id': lambda: row.__setitem__('localId', 'declaration:other'),
    }
    actions[mutation]()
    with pytest.raises(ValueError):
        candidate_type_evidence(artifact, 'Demo.proof')
