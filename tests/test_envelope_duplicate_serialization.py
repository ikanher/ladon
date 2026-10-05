"""Reject ambiguous serialized objects at the envelope ownership boundary."""

import pytest
from support.proofir_v3_native import claim_artifact

from ladon.proofir_v3 import ProofIRV3Error, validate_envelope, validate_envelope_batch


@pytest.mark.parametrize("batch", [False, True])
@pytest.mark.parametrize("nested", [False, True])
def test_duplicate_serialized_object_keys_are_rejected(batch, nested):
    class DuplicatePairs(dict):
        def items(self):
            pairs = list(super().items())
            return pairs + [pairs[-1]]

    raw = claim_artifact()
    if nested:
        raw["extensions"] = DuplicatePairs(raw["extensions"])
    else:
        raw = DuplicatePairs(raw)
    with pytest.raises(ProofIRV3Error, match="duplicate serialized object key"):
        if batch:
            validate_envelope_batch([raw])
        else:
            validate_envelope(raw)
