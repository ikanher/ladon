"""Altered scoped observations cannot acquire checking authority by rehashing."""

import copy
import hashlib
import shutil
from pathlib import Path

import pytest

from ladon.correspondence_check import check_correspondence, prepare_correspondence
from ladon.proof_slice import extract_proof_slice, slice_identity


def test_scoped_and_premises_instantiations_and_later_facts_cannot_be_rewritten(tmp_path):
    fixture = Path(__file__).parent / "fixtures/correspondence_m1"
    root = tmp_path / "repo"
    shutil.copytree(fixture, root, ignore=shutil.ignore_patterns(".ladon", "*.olean"))
    source = root / "predecessor.txt"
    record = {"id": "tamper-control", "source": {
        "path": source.name, "startLine": 1, "endLine": 1,
        "quote": source.read_text().strip(), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
        "formula": {"tag": "const", "name": "True"}, "symbols": {}}
    actual = extract_proof_slice(root, "Scoped.lean", "Scoped", "Scoped.chain", "Scoped.combine",
                                scoped=True)
    assert actual["complete"]
    missing = copy.deepcopy(actual)
    missing["nodes"][0]["premises"].pop()
    missing["sliceId"] = slice_identity(missing)
    with pytest.raises(ValueError, match="projections disagree"):
        prepare_correspondence(record, missing, {})
    swapped = copy.deepcopy(actual)
    args = swapped["nodes"][0]["arguments"]
    args[0]["expression"], args[1]["expression"] = args[1]["expression"], args[0]["expression"]
    swapped["sliceId"] = slice_identity(swapped)
    with pytest.raises(ValueError, match="projections disagree"):
        prepare_correspondence(record, swapped, {})
    # A coordinated wire rewrite passes shape validation, but exact re-extraction
    # must reject the invented closed provider proposition and proof.
    invented = copy.deepcopy(actual)
    provider = invented["observation"]["applications"][0]["providerObservations"][0]
    provider.update(closedType="True", closedProof="True.intro")
    observation = invented["nodes"][0]["premises"][0]["providerObservation"]
    observation.update(closedType="True", closedProof="True.intro")
    invented["sliceId"] = slice_identity(invented)
    plan = prepare_correspondence(record, invented, {})
    with pytest.raises(ValueError, match="stale source, context"):
        check_correspondence(plan, [], root)
