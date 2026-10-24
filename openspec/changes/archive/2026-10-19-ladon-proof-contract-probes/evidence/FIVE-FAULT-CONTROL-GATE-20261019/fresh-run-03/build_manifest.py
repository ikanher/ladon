"""Build a content manifest for fresh-run-03 and its runner inputs."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[5]
manifest_path = BASE / "MANIFEST.json"
files = {path.resolve() for path in BASE.rglob("*") if path.is_file()
         and path != manifest_path}
result = json.loads((BASE / "FRESH-RESULT.json").read_text(encoding="utf-8"))
for record in result["runnerScripts"] + result["sourceQualifiers"]:
    files.add((ROOT / record["path"]).resolve())
entries = []
for path in sorted(files):
    data = path.read_bytes()
    entries.append({"path": os.path.relpath(path, BASE), "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest()})
manifest = {"schema": "ladon-fresh-probe-gate-manifest-v1", "entries": len(entries),
            "bytes": sum(entry["bytes"] for entry in entries), "files": entries}
manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n",
                         encoding="utf-8")
print(f"wrote {len(entries)} entries ({manifest['bytes']} bytes)")
