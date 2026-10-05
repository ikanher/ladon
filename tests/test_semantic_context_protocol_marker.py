"""Malformed provenance cannot enable the v4 display-name exception."""
from __future__ import annotations

import pytest
from test_semantic_context_shadowing_fallback import REQUESTED, _notation_shadowed_rows

from ladon._semantic_observation_contract import _validate_context_subject
from ladon.semantic_projection_core import SemanticProjectionError


@pytest.mark.parametrize('version,protocol', [
    (4.0, 'ladon-lean-semantic-v4/check-candidate'),
    (True, 'ladon-lean-semantic-v4/check-candidate'),
    (4, []),
    (4, {}),
])
def test_malformed_process_marker_cannot_enable_shadowing(version, protocol):
    rows = _notation_shadowed_rows()
    observed = [{'name': row['userName'], 'type': row['typeDisplay']} for row in rows]
    owner = {
        'subjectRefs': [{'kind': 'local-context', 'searchShape': {'localContext': rows}}],
        'extensions': {'ladon.process-observation/v1': {
            'applicationObservationVersion': version, 'semanticProtocol': protocol,
        }},
    }
    with pytest.raises(SemanticProjectionError, match='requested prefix'):
        _validate_context_subject({'localContext': observed}, {'callerLocalContext': REQUESTED},
                                  None, check_artifact=owner)
