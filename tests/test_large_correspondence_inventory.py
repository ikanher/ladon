"""Canonical bounds admit module inventories only at correspondence slice paths."""
import json

import pytest

from ladon.proofir_v3 import ProofIRV3Error, canonical_bytes


def envelope(count):
    return {"proofirVersion": "3.0", "artifactKind": "proofir.correspondence",
            "payload": {"slice": {"schema": "ladon-proof-slice-v1",
                "observation": {"importedModules": [f"M{i}" for i in range(count)]},
                "compiledInventory": {"modules": [{"module": f"M{i}"} for i in range(count)]}}}}


@pytest.mark.parametrize("count", [10001, 32768])
def test_large_slice_inventory_preserves_canonical_bytes(count):
    value = envelope(count)
    expected = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    assert canonical_bytes(value) == expected


@pytest.mark.parametrize("location", ["observation", "compiledInventory"])
def test_slice_inventory_retains_upper_bound(location):
    value = envelope(0)
    key = "importedModules" if location == "observation" else "modules"
    value["payload"]["slice"][location][key] = [None] * 32769
    with pytest.raises(ProofIRV3Error, match="collection exceeds item limit: 32768"):
        canonical_bytes(value)


@pytest.mark.parametrize("location", ["nested", "extension", "wrong-kind", "wrong-schema", "other-list", "row"])
def test_slice_allowance_cannot_escape_exact_paths(location):
    value = envelope(10001)
    if location == "nested":
        value = {"unrelated": value}
    elif location == "extension":
        value["extensions"] = {"slice": value["payload"].pop("slice")}
    elif location == "wrong-kind":
        value["artifactKind"] = "proofir.observation"
    elif location == "wrong-schema":
        value["payload"]["slice"]["schema"] = "unknown"
    elif location == "other-list":
        value = envelope(0)
        value["payload"]["slice"]["observation"]["applications"] = [None] * 10001
    else:
        value = envelope(0)
        value["payload"]["slice"]["compiledInventory"]["modules"] = [{"nested": [None] * 10001}]
    with pytest.raises(ProofIRV3Error, match="collection exceeds item limit: 10000"):
        canonical_bytes(value)


def test_large_inventory_keeps_artifact_byte_bound():
    with pytest.raises(ProofIRV3Error, match="canonical payload exceeds byte limit"):
        canonical_bytes(envelope(10001), max_bytes=1024)


def test_standalone_slice_projection_preserves_the_same_module_rows():
    selected = envelope(10001)["payload"]["slice"]
    assert json.loads(canonical_bytes(selected)) == selected
    with pytest.raises(ProofIRV3Error, match="collection exceeds item limit: 10000"):
        canonical_bytes({"unrelated": selected})


def receipt(count):
    return {"goalOrigin": "generated-correspondence-obligation",
            "capture": {"schema": "ladon-source-goal-capture-result-v1",
                        "operation": "capture-source-goal",
                        "capture": {"environment": {"compiledInventory": {
                            "modules": [{"module": f"M{i}"} for i in range(count)]}}}}}


@pytest.mark.parametrize("wrapped", [False, True])
def test_large_receipt_hash_preserves_canonical_encoding(wrapped):
    import hashlib

    from ladon.correspondence_evidence import _hash

    value = receipt(10001)
    if wrapped:
        value = {"planId": "plan", "receipt": value}
    expected = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    assert _hash(value) == "sha256:" + hashlib.sha256(expected).hexdigest()


@pytest.mark.parametrize("mutation", ["overflow", "nested", "wrong-origin", "wrong-schema", "wrong-operation", "row", "extra-wrapper"])
def test_receipt_inventory_allowance_stays_bounded(mutation):
    value = receipt(10001)
    limit = 10000
    if mutation == "overflow":
        value = receipt(32769)
        limit = 32768
    elif mutation == "nested":
        value = {"unrelated": value}
    elif mutation == "wrong-origin":
        value["goalOrigin"] = "unknown"
    elif mutation in {"wrong-schema", "wrong-operation"}:
        value["capture"][mutation.removeprefix("wrong-")] = "unknown"
    elif mutation == "row":
        value = receipt(1)
        value["capture"]["capture"]["environment"]["compiledInventory"]["modules"][0]["other"] = [None] * 10001
    else:
        value = {"planId": "plan", "receipt": value, "unrelated": True}
    with pytest.raises(ProofIRV3Error, match=f"collection exceeds item limit: {limit}"):
        canonical_bytes(value)
