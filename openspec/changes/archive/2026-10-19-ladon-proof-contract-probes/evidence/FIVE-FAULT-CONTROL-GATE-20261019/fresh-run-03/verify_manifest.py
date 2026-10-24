"""Verify all fresh gate evidence and runner source hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
manifest = json.loads((BASE / "MANIFEST.json").read_text(encoding="utf-8"))
errors = []
total = 0
for entry in manifest["files"]:
    path = (BASE / entry["path"]).resolve()
    try:
        data = path.read_bytes()
    except OSError as error:
        errors.append(f"{entry['path']}: {error}")
        continue
    total += len(data)
    if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
        errors.append(f"{entry['path']}: bytes or SHA-256 differ")
if len(manifest["files"]) != manifest["entries"] or total != manifest["bytes"]:
    errors.append("manifest entry or byte total differs")
if errors:
    raise SystemExit("\n".join(errors))
print(f"verified {manifest['entries']} files ({total} bytes)")
