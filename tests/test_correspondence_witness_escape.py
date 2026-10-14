"""An internal existential witness cannot be mapped to a global prose object."""

import json
from pathlib import Path

import pytest

from ladon.correspondence_check import prepare_correspondence
from ladon.proof_slice import extract_proof_slice


def test_nested_witness_rejects_outer_object_mapping():
    root = Path(__file__).parent / "fixtures/correspondence_m1"
    result = extract_proof_slice(root, "Scoped.lean", "Scoped", "Scoped.witness",
                                 "Scoped.bridge", scoped=True)
    assert result["complete"] is True
    record = json.loads((root / "positive.json").read_text())
    with pytest.raises(ValueError, match="escaped.*witness|nested.*scope"):
        prepare_correspondence(record, result, {"k": "n"})
