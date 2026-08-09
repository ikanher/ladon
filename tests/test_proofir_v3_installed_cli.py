from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from support.proofir_v3_native import claim_artifact

from ladon.proofir_v3 import canonical_bytes


def test_installed_entrypoint_exposes_bounded_v3_operations(tmp_path: Path) -> None:
    artifact = claim_artifact()
    source = tmp_path / "artifact.json"
    source.write_text(json.dumps(artifact), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "ladon.entrypoint", "proofir", "validate", str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "valid"

    canonical = tmp_path / "canonical.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "proofir",
            "canonicalize",
            str(source),
            "--out",
            str(canonical),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert canonical.read_bytes() == canonical_bytes(artifact)

    result = subprocess.run(
        [sys.executable, "-m", "ladon.entrypoint", "proofir", "inspect", str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    inspected = json.loads(result.stdout)
    assert inspected["artifactId"] == artifact["artifactId"]
    assert inspected["artifactKind"] == "proofir.claim"
