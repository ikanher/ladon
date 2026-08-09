from __future__ import annotations

import json
from pathlib import Path

from ladon.proofir_sqlite_v3 import normalized_rows
from ladon.proofir_v3 import validate_envelope


def test_normalized_rows_are_deterministic_and_provenance_preserving() -> None:
    vector = json.loads(
        Path("tests/fixtures/proofir_v3_parity/normalized-row-vector.json").read_text(
            encoding="utf-8"
        )
    )
    artifact = vector["artifact"]
    assert validate_envelope(artifact).content_id == vector["artifactId"]
    rows = normalized_rows(artifact)
    assert rows == vector["normalized"]
