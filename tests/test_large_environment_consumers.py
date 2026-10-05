"""Large environment capacity must survive storage and canonical consumers."""
from __future__ import annotations

import json
import subprocess

import pytest
from support.large_environment import large_environment, reference_bytes, reseal_environment
from test_result_resolution import inputs, reseal_source

from ladon.proofir_sqlite_v3 import normalized_rows
from ladon.proofir_v3 import (
    ProofIRV3Error,
    canonical_bytes,
    validate_envelope,
    validate_envelope_batch,
)
from ladon.result_resolution import resolve_result_manifest
from ladon.semantic_evidence_registry import SemanticEvidenceRegistry


def test_large_environment_round_trips_registry_without_identity_changes(tmp_path):
    artifact = large_environment()
    registry = SemanticEvidenceRegistry(tmp_path / "evidence.sqlite")
    registered = registry.register_bundle([artifact])
    assert registered["insertedArtifactRefs"] == [artifact["artifactId"]]
    assert registry.resolve_environment(artifact["environmentRef"]) == artifact
    assert registry.resolve_artifact(artifact["artifactId"]) == artifact
    assert canonical_bytes(artifact) == reference_bytes(artifact)


def test_result_resolver_preserves_exact_large_environment():
    manifest, artifacts = inputs()
    environment = large_environment()
    artifacts[0] = environment
    artifacts[1]["environmentRef"] = environment["environmentRef"]
    manifest["targets"][0]["environment"]["digest"] = environment["environmentRef"]
    reseal_source(manifest, artifacts)
    result = resolve_result_manifest(manifest, artifacts)
    assert result["targetResolutions"][0]["status"] == "resolved"
    assert result["targetResolutions"][0]["checking"] == "not-assessed"


@pytest.mark.parametrize("field", ["dependencies", "axioms", "extension", "object"])
def test_other_environment_collections_remain_bounded(field):
    artifact = large_environment()
    rows = ["x"] * 10_001
    if field == "dependencies":
        artifact["payload"]["dependencies"] = rows
    elif field == "axioms":
        artifact["payload"]["trust"]["axiomsAllowed"] = rows
    elif field == "extension":
        artifact["extensions"]["fixture.capacity/v1"] = {"nested": rows}
    else:
        artifact["extensions"]["fixture.capacity/v1"] = {str(i): 0 for i in range(10_001)}
    with pytest.raises(ProofIRV3Error):
        canonical_bytes(artifact)


@pytest.mark.parametrize("mutation", ["digest", "name", "row", "long-string", "deep"])
def test_large_module_array_still_validates_every_descendant(mutation):
    artifact = large_environment()
    row = artifact["payload"]["compiledModules"][-1]
    if mutation == "digest":
        row["digest"] = "not-a-digest"
    elif mutation == "name":
        row["module"] = ""
    elif mutation == "row":
        row["unexpected"] = True
    elif mutation == "long-string":
        row["module"] = "M" * (1024 * 1024 + 1)
    else:
        nested = []
        for _ in range(65):
            nested = [nested]
        row["module"] = nested
    reseal_environment(artifact)
    with pytest.raises(ProofIRV3Error):
        validate_envelope(artifact)


def test_large_environment_remains_within_artifact_and_batch_byte_limits():
    oversized = large_environment(32_768, name_padding=200)
    assert len(reference_bytes(oversized)) > 8 * 1024 * 1024
    with pytest.raises(ProofIRV3Error, match="byte limit"):
        validate_envelope(oversized)
    artifact = large_environment()
    wire_size = len(reference_bytes(artifact))
    with pytest.raises(ProofIRV3Error, match="batch.*byte limit"):
        validate_envelope_batch([artifact, artifact], max_batch_bytes=wire_size + 1)


def test_large_environment_rust_python_canonical_and_projection_parity(tmp_path):
    artifact = large_environment()
    vector = tmp_path / "large-environment.json"
    vector.write_text(json.dumps({"artifact": artifact}))
    result = subprocess.run(
        ["cargo", "run", "--offline", "--quiet", "-p", "proofir-ladon", "--bin",
         "proofir-parity", str(vector)], cwd="rust", capture_output=True, text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    rust = json.loads(result.stdout)
    assert rust["canonical"].encode() == canonical_bytes(artifact) == reference_bytes(artifact)
    assert rust["artifactId"] == artifact["artifactId"]
    assert rust["normalized"] == normalized_rows(artifact)
