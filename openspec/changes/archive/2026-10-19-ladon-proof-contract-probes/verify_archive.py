"""Verify the frozen probe packet after relocation without rewriting its evidence."""

from __future__ import annotations

import hashlib
import json
import os
import runpy
from pathlib import Path

ORIGINAL = Path("openspec/changes/ladon-proof-contract-probes")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def repository(change: Path) -> Path:
    return next(parent for parent in change.parents
                if (parent / "pyproject.toml").is_file()
                and (parent / "src/ladon").is_dir())


def relocated(path: Path, root: Path, change: Path) -> Path:
    """Translate only the historical change prefix; keep external inputs bound."""
    normalized = Path(os.path.abspath(path))
    original = root / ORIGINAL
    if normalized.is_relative_to(original):
        return change / normalized.relative_to(original)
    return normalized


def verify_row(path: Path, row: dict) -> int:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != row["sha256"]:
        raise ValueError(f"SHA-256 differs: {path}")
    if "bytes" in row and len(data) != row["bytes"]:
        raise ValueError(f"size differs: {path}")
    return len(data)


def verify_file_manifest(manifest: dict, base: Path, root: Path, change: Path) -> int:
    rows = manifest["files"]
    total = sum(verify_row(relocated(base / row["path"], root, change), row)
                for row in rows)
    for key in ("entries", "fileCount"):
        if key in manifest and manifest[key] != len(rows):
            raise ValueError(f"manifest {key} differs: {base}")
    if "bytes" in manifest and manifest["bytes"] != total:
        raise ValueError(f"manifest byte total differs: {base}")
    return len(rows)


def verify_task3_manifest(manifest: dict, base: Path, root: Path, change: Path) -> int:
    count = 0
    for group in ("inputs", "producers", "artifacts"):
        historical_base = base if group == "artifacts" else root
        for row in manifest[group]:
            verify_row(relocated(historical_base / row["path"], root, change), row)
            count += 1
    if manifest.get("nonimplicationIsUnrelatedToApplicationFinding") is not True:
        raise ValueError("counterexample/application separation changed")
    return count


def verify_task3_contracts(root: Path, change: Path) -> None:
    """Run the unchanged report assertions with the current repository root."""
    source = change / "evidence/TASK-3-ACCEPTANCE-20261019/verify_manifest.py"
    module = runpy.run_path(str(source))
    check = module["_verify_claims"]
    check.__globals__["ROOT"] = root
    check()


def verify(change: Path, root: Path) -> tuple[int, int, int]:
    migration = read_json(change / "ARCHIVE-MIGRATION.json")
    for row in migration["files"]:
        verify_row(change / row["path"], row)
    inventory = read_json(change / "ARCHIVE-INVENTORY.json")
    rows = inventory["files"]
    if inventory["originalChangePath"] != ORIGINAL.as_posix():
        raise ValueError("unexpected original change path")
    for row in rows:
        verify_row(change / row["path"], row)
    manifests = [row for row in rows if Path(row["path"]).name.endswith("MANIFEST.json")]
    count = 0
    for row in manifests:
        relative = Path(row["path"])
        manifest = read_json(change / relative)
        base = root / ORIGINAL / relative.parent
        if "files" in manifest:
            count += verify_file_manifest(manifest, base, root, change)
        elif manifest.get("schema") == "ladon-task-3-evidence-manifest-v1":
            count += verify_task3_manifest(manifest, base, root, change)
        else:
            raise ValueError(f"unsupported manifest shape: {relative}")
    verify_task3_contracts(root, change)
    return len(rows), len(manifests), count


def main() -> int:
    change = Path(__file__).resolve().parent
    files, manifests, rows = verify(change, repository(change))
    print(f"PASS: {files} original files unchanged; {manifests} frozen manifests, "
          f"{rows} bindings, and task 3 report contracts verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
