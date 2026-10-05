"""Bound disclosure records before discarding small mathematical observations."""
from copy import deepcopy

from test_semantic_application_context_compact import observation, transport

from ladon.semantic_projection_core import semantic_projection_bytes
from ladon.semantic_projection_fit import finalize_projection


def test_small_owned_context_survives_bounded_omission_ledger():
    check, selected = observation()
    payload = transport(check)
    payload['request'] = {'goal': '∀ (α β : Type) [Inhabited α] (x : α) (y : β), (x = x) ∧ (y = y)',
                          'module': 'BinderFixture', 'goalFingerprint': 'sha256:' + 'a' * 64,
                          'moduleFingerprint': 'sha256:' + 'b' * 64, 'localContext': []}
    card = payload['candidate']['check']
    card.update(environmentRef={'artifactRef': 'sha256:' + 'c' * 64, 'environmentRef': 'sha256:' + 'd' * 64},
                checkRunRef={'artifactRef': 'sha256:' + 'e' * 64, 'localId': 'check:' + 'f' * 64},
                receiptIdentity='sha256:' + 'a' * 64, sourceReceiptIdentity='sha256:' + 'b' * 64)
    original = deepcopy(payload)
    result = finalize_projection(payload, 8192)
    card = result['candidate']['check']
    assert card['selectedDeclaration']['typeDisplay'] == selected['typeDisplay']
    assert card['residualPremises'] == original['candidate']['check']['residualPremises']
    assert result['coverage']['omissionPopulation']['observedRecords'] == len(original['omissions'])
    assert len(semantic_projection_bytes(result)) <= 8192
    assert card['checkRunRef'] == original['candidate']['check']['checkRunRef']
