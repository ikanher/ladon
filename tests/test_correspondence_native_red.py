"""Native dialect registration must be explicit, preserving existing kinds."""
from ladon.proofir_v3 import SUPPORTED_ARTIFACT_KINDS


def test_interpretation_and_correspondence_have_native_closed_kinds():
    assert {"proofir.interpretation", "proofir.correspondence"} <= SUPPORTED_ARTIFACT_KINDS
