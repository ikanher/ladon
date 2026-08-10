from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ladon.proofir_sqlite_v3 import normalized_rows
from ladon.proofir_v3 import canonical_bytes, validate_envelope


def test_rust_and_python_execute_the_same_normalized_vector() -> None:
    vector_path = Path("tests/fixtures/proofir_v3_parity/normalized-row-vector.json")
    vector = json.loads(vector_path.read_text(encoding="utf-8"))
    checked = validate_envelope(vector["artifact"])
    assert checked.content_id == vector["artifactId"]
    assert (
        canonical_bytes(vector["artifact"]).decode("utf-8") == vector["canonicalJson"]
    )
    result = subprocess.run(
        [
            "cargo",
            "run",
            "--offline",
            "-q",
            "-p",
            "proofir-ladon",
            "--bin",
            "proofir-parity",
            f"../{vector_path}",
        ],
        cwd="rust",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    rust = json.loads(result.stdout)
    assert rust["artifactId"] == vector["artifact"]["artifactId"]
    assert rust["canonical"] == canonical_bytes(vector["artifact"]).decode("utf-8")
    assert rust["normalized"] == normalized_rows(vector["artifact"])
