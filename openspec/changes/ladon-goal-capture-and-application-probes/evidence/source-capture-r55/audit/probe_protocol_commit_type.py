"""Transport-only falsification of malformed Lean worker metadata."""
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from types import SimpleNamespace

from ladon._source_goal_protocol import PROTOCOL, validate_observation


def main() -> None:
    source = b"example : True := by\n  skip\n"
    with tempfile.TemporaryDirectory(prefix="source-capture-audit-") as temporary:
        executable = Path(temporary) / "lean"
        executable.write_bytes(b"audited transport fixture")
        digest = "sha256:" + hashlib.sha256(executable.read_bytes()).hexdigest()
        context = SimpleNamespace(
            lean_release="4.32.1", lean_commit=None, lean_path=executable,
            lean_identity=digest,
        )
        request = {
            "requestId": "audit", "contextRef": "sha256:context", "module": "Owner",
            "filename": "Owner.lean", "sourceDigest": "sha256:" + hashlib.sha256(source).hexdigest(),
            "line": 2, "column": 6, "protocolVersion": PROTOCOL,
            "snapshotPath": "/unused",
        }
        frame = {
            "frame": "LADON_GOAL_FRAME", "protocolVersion": PROTOCOL,
            "helperVersion": "ladon-source-goal-helper-v1", "leanVersion": "4.32.1",
            "leanCommit": "", "leanExecutablePath": str(executable),
            "compiledModulePaths": [{"module": "Init", "path": "/tmp/Init.olean"}],
            "requestId": "audit", "contextRef": "sha256:context", "module": "Owner",
            "filename": "Owner.lean", "sourceDigest": request["sourceDigest"],
            "line": 2, "column": 6, "byteOffset": 27,
            "goals": [{"goalId": "g", "typeDisplay": "True", "typeStructural": "True",
                       "localContext": []}],
            "goalCount": 1, "useAfter": True, "rangeStartByte": 0, "rangeEndByte": 7,
            "namespaceName": "", "openDeclarationsStructural": "", "optionsStructural": "",
            "importedModules": ["Init"], "observationCount": 1,
        }
        validate_observation(frame, request, context, source)
        print("transport falsification accepted a syntax range disjoint from the selected byte offset")


if __name__ == "__main__":
    main()
