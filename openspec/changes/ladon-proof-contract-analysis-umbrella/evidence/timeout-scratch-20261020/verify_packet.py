"""Read-only hash verification of the supervised goal scratch recovery packet."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main():
    base = Path(__file__).resolve().parent
    manifest = json.loads((base / "MANIFEST.json").read_text())
    total = 0
    for row in manifest["files"]:
        data = (base / row["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != row["sha256"] or len(data) != row["bytes"]:
            raise ValueError(f"packet file changed: {row['path']}")
        total += len(data)
    if manifest["entries"] != len(manifest["files"]) or manifest["bytes"] != total:
        raise ValueError("packet manifest totals changed")
    print(f"PASS: {manifest['entries']} packet files ({total} bytes) verified")


if __name__ == "__main__":
    main()
