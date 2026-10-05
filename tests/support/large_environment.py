"""Large environment vectors built without the production canonical encoder."""
from __future__ import annotations

import hashlib
import json

from support.proofir_v3_native import environment_artifact


def reference_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode()


def reseal_environment(artifact):
    artifact["environmentRef"] = "sha256:" + hashlib.sha256(
        reference_bytes(artifact["payload"])
    ).hexdigest()
    detached = {key: value for key, value in artifact.items() if key != "artifactId"}
    artifact["artifactId"] = "sha256:" + hashlib.sha256(reference_bytes(detached)).hexdigest()
    return artifact


def large_environment(count=10_517, *, name_padding=0):
    artifact = environment_artifact()
    artifact["payload"]["compiledModules"] = [
        {"module": f"Fixture.Module{i:05d}" + "x" * name_padding,
         "digest": "sha256:" + f"{i:064x}"}
        for i in range(count)
    ]
    return reseal_environment(artifact)
