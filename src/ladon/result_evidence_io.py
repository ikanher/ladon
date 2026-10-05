"""Read only explicitly selected, bounded local canonical evidence files."""
from __future__ import annotations

import os
import stat
from pathlib import Path

from ladon.proofir_v3 import MAX_ARTIFACT_BYTES, MAX_ARTIFACTS, MAX_BATCH_BYTES
from ladon.result_manifest_io import ResultManifestError, parse_result_manifest


def load_result_artifacts(paths: list[Path]) -> list[dict]:
    """Apply existing ProofIR input limits without dereferencing artifact IDs."""
    if len(paths) > MAX_ARTIFACTS:
        raise ResultManifestError('canonical artifact count exceeds the ProofIR limit')
    artifacts = []
    total = 0
    for path in paths:
        remaining = min(MAX_ARTIFACT_BYTES, MAX_BATCH_BYTES - total)
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise ResultManifestError('canonical evidence input must be a regular file')
            if metadata.st_size > remaining:
                raise ResultManifestError('canonical evidence exceeds the ProofIR input limit')
            raw = stream.read(remaining + 1)
        if len(raw) > remaining:
            raise ResultManifestError('canonical evidence exceeds the ProofIR input limit')
        total += len(raw)
        artifacts.append(parse_result_manifest(raw))
    return artifacts
