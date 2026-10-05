"""Contract tests for bounded large compiled-module environments."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from support.proofir_v3_native import environment_artifact

from ladon.proofir_v3 import (
    MAX_COLLECTION_ITEMS,
    ProofIRV3Error,
    canonical_bytes,
    detached_content_id,
    validate_envelope,
)
from ladon.semantic_candidate_worker import _environment_artifact


@pytest.mark.parametrize("module_count", [10_517, 32_768])
def test_environment_artifact_round_trips_all_compiled_module_identities(
    tmp_path: Path, module_count: int
) -> None:
    """The environment's one exceptional collection limit preserves exact rows."""
    olean = tmp_path / "shared-fixture.olean"
    olean.write_bytes(b"compiled fixture bytes")
    executable = tmp_path / "lean"
    executable.write_bytes(b"lean executable fixture")
    imported = [
        {"module": f"Fixture.Module{i:05d}", "oleanPath": str(olean)}
        for i in range(module_count)
    ]
    emitted = _environment_artifact(
        tmp_path,
        {
            "importedModules": imported,
            "leanVersion": "4.33.0",
            "leanCommit": "fixture-commit",
            "executablePath": str(executable),
            "universePolicy": "lean-level-mvar-succ-zero/v1",
        },
    )

    # Exercise actual canonical bytes and the public validator; no mocked
    # successful validator or producer-only assertion can satisfy this gate.
    wire = canonical_bytes(emitted)
    decoded: dict[str, Any] = json.loads(wire)
    validated = validate_envelope(decoded).to_dict()
    rows = validated["payload"]["compiledModules"]
    assert len(rows) == module_count
    assert [row["module"] for row in rows] == sorted(
        item["module"] for item in imported
    )
    assert {row["digest"] for row in rows} == {
        "sha256:" + hashlib.sha256(b"compiled fixture bytes").hexdigest()
    }
    assert canonical_bytes(validated) == wire


def test_ordinary_canonical_collections_keep_the_generic_item_limit() -> None:
    with pytest.raises(
        ProofIRV3Error,
        match=f"collection exceeds item limit: {MAX_COLLECTION_ITEMS}",
    ):
        canonical_bytes({"ordinaryItems": [None] * (MAX_COLLECTION_ITEMS + 1)})


def test_environment_producer_rejects_32769_modules_before_file_reads(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="32,769 imported modules; evidence limit is 32,768"):
        _environment_artifact(tmp_path, {"importedModules": [{}] * 32_769})


def test_environment_reader_rejects_duplicate_module_identity() -> None:
    artifact = environment_artifact()
    artifact["payload"]["compiledModules"] = [
        {"module": "Duplicate", "digest": "sha256:" + "1" * 64},
        {"module": "Duplicate", "digest": "sha256:" + "2" * 64},
    ]
    artifact["environmentRef"] = "sha256:" + hashlib.sha256(
        canonical_bytes(artifact["payload"])
    ).hexdigest()
    artifact["artifactId"] = detached_content_id(artifact)
    with pytest.raises(ProofIRV3Error, match="duplicate.*module|repeats.*module"):
        validate_envelope(artifact)


@pytest.mark.parametrize("location", ["generic-key", "extension", "nested-manifest"])
def test_large_module_allowance_does_not_escape_environment_root(location: str) -> None:
    rows = [{"module": f"M{i}", "digest": "sha256:" + "1" * 64} for i in range(10_001)]
    artifact = environment_artifact()
    if location == "generic-key":
        value = {"compiledModules": rows}
    elif location == "extension":
        artifact["extensions"]["fixture.modules/v1"] = {"compiledModules": rows}
        value = artifact
    else:
        artifact["payload"]["compiledModules"] = rows
        value = {"unrelated": artifact["payload"]}
    with pytest.raises(ProofIRV3Error, match="collection exceeds item limit: 10000"):
        canonical_bytes(value)
