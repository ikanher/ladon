from __future__ import annotations

import copy
import sqlite3

import pytest
from support.proofir_v3_native import native_artifacts

from ladon.proofir_sqlite_v3 import create_v3_schema, project_envelopes
from ladon.proofir_v3 import (
    ProofIRV3Error,
    detached_content_id,
    validate_envelope,
    validate_envelope_batch,
)


KINDS = tuple(sorted(native_artifacts()))


@pytest.mark.parametrize("kind", KINDS)
def test_every_registered_kind_has_valid_invalid_and_projection_cases(kind: str) -> None:
    source = native_artifacts()[kind]
    assert validate_envelope(source).to_dict() == source

    invalid = copy.deepcopy(source)
    invalid["payload"]["unexpected"] = True
    invalid["artifactId"] = detached_content_id(invalid)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(invalid)
    assert captured.value.diagnostic.code == "unexpected-payload-key"

    connection = sqlite3.connect(":memory:")
    create_v3_schema(connection)
    project_envelopes(connection, [source])
    assert connection.execute(
        "SELECT COUNT(*) FROM proofir_v3_artifacts WHERE content_artifact_id = ?",
        (source["artifactId"],),
    ).fetchone() == (1,)


def test_every_kind_is_named_in_the_language_neutral_inventory() -> None:
    from pathlib import Path
    import json

    inventory = json.loads(
        Path("docs/proofir-v3-corpus-inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["format"] == "proofir-v3-corpus-inventory-v2"
    assert set(inventory["artifactKinds"]) == set(KINDS)
    assert inventory["rustReady"] is False
    from pathlib import Path

    vectors = json.loads(
        Path(inventory["adversarialVectorFixture"]).read_text(encoding="utf-8")
    )
    diagnostics = json.loads(
        Path(inventory["adversarialDiagnosticFixture"]).read_text(encoding="utf-8")
    )
    assert len(vectors) == inventory["adversarialVectorCount"] == 25
    assert {vector["name"] for vector in vectors} == set(diagnostics)


def test_every_r03_vector_fails_single_and_batch_validation_before_projection() -> None:
    import json
    from pathlib import Path

    vectors = json.loads(
        Path("tests/fixtures/proofir_v3_r03_adversarial.json").read_text(encoding="utf-8")
    )
    for vector in vectors:
        artifact = copy.deepcopy(native_artifacts()[vector["kind"]])
        target = artifact["payload"]
        for part in vector["path"][:-1]:
            target = target[part]
        target[vector["path"][-1]] = vector["replacement"]
        artifact["artifactId"] = detached_content_id(artifact)
        with pytest.raises(ProofIRV3Error):
            validate_envelope_batch([artifact])
