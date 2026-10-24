"""Verify the task 2.2 evidence bundle against its content manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
errors = []
for entry in manifest["files"]:
    path = ROOT / entry["path"]
    try:
        data = path.read_bytes()
    except OSError as error:
        errors.append(f"{entry['path']}: {error}")
        continue
    if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
        errors.append(f"{entry['path']}: size or SHA-256 differs")
if len(manifest["files"]) != manifest["entries"]:
    errors.append("manifest entry count differs")
if errors:
    raise SystemExit("\n".join(errors))
print(f"verified {manifest['entries']} files ({manifest['bytes']} bytes)")
