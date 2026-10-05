"""Rejected observations retain protocol provenance without accepted fields."""
from __future__ import annotations

import pytest
from test_semantic_context_shadowing_fallback import REQUESTED, _notation_shadowed_rows

from ladon._semantic_observation_contract import _validate_context_subject
from ladon.semantic_projection_core import SemanticProjectionError


@pytest.mark.parametrize('protocol,duplicate,valid', [
    ('ladon-lean-semantic-v4/check-candidate', False, True),
    ('ladon-lean-semantic-v4/check-candidates', False, True),
    ('ladon-lean-semantic-v3/check-candidate', False, False),
    ('ladon-lean-semantic-v4/check-candidate', True, False),
    ('unknown', False, False),
])
def test_rejected_context_uses_owning_process_protocol(protocol, duplicate, valid):
    rows = _notation_shadowed_rows('local:0' if duplicate else 'local:1')
    observed = [{'name': row['userName'], 'type': row['typeDisplay']} for row in rows]
    check = {'callerLocalContext': REQUESTED, 'status': 'rejected'}
    owner = {
        'subjectRefs': [{'kind': 'local-context', 'searchShape': {'localContext': rows}}],
        'extensions': {'ladon.process-observation/v1': {
            'applicationObservationVersion': 4, 'semanticProtocol': protocol,
        }},
    }
    if valid:
        _validate_context_subject({'localContext': observed}, check, None, check_artifact=owner)
    else:
        with pytest.raises(SemanticProjectionError, match='requested prefix'):
            _validate_context_subject({'localContext': observed}, check, None, check_artifact=owner)
    assert set(check) == {'callerLocalContext', 'status'}
