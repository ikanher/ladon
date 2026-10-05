"""Replay the frozen exposition's offline CLI scenarios; never start Lean."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ladon.result_manifest_io import content_revision


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def variants(original: dict) -> list[tuple[str, dict]]:
    """Create clearly synthetic inputs without editing the frozen manifest."""
    result = [("baseline", copy.deepcopy(original))]
    for name in ("stale-claim", "stale-target", "nonexistent-target", "dangling-component", "wrong-revision"):
        item = copy.deepcopy(original)
        claim = next(c for c in item["claims"] if c["id"] == "cor:fixed-epoch-all-horizon")
        target = next(t for t in item["targets"] if t["id"] == "uniform-total")
        if name == "stale-claim":
            claim["statement"] += "\nSynthetic changed statement for review-currency testing."
            claim["revision"] = content_revision("claim", claim)
        elif name == "stale-target":
            target["typeText"] += " → False /- synthetic target edit -/"
            target["revision"] = content_revision("target", target)
        elif name == "nonexistent-target":
            target["name"] = "Mf.DP.BaselineDeliberatelyNonexistentDeclaration"
            target["revision"] = content_revision("target", target)
        elif name == "dangling-component":
            item["links"][0]["componentIds"] = ["not-a-declared-component"]
        else:
            claim["statement"] += "\nSynthetic edit without updating its revision."
        item["revision"] = content_revision("manifest", item)
        result.append((name, item))
    return result


def run(console: Path, output: Path, name: str, arguments: list[str]) -> dict:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    command = [str(console), *arguments]
    started = time.monotonic()
    result = subprocess.run(command, cwd=output, env=environment, capture_output=True, timeout=30, check=False)
    (output / (name + ".stdout")).write_bytes(result.stdout)
    (output / (name + ".stderr")).write_bytes(result.stderr)
    record = {
        "id": name, "argv": command, "cwd": str(output), "exitCode": result.returncode,
        "elapsedSeconds": time.monotonic() - started,
        "stdout": name + ".stdout", "stderr": name + ".stderr",
    }
    save(output / (name + ".command.json"), record)
    return record


def verify(record: dict, output: Path) -> None:
    name = record["id"]
    stdout = (output / record["stdout"]).read_text()
    stderr = (output / record["stderr"]).read_text()
    invalid = name in {"dangling-component", "wrong-revision", "inspect", "guide"}
    assert record["exitCode"] == (2 if invalid else 0), (name, stderr)
    if invalid:
        assert not stdout, name
        assert json.loads(stderr)["diagnostic"]["code"], name
        return
    verify_valid(json.loads(stdout), name)


def verify_valid(payload: dict, name: str) -> None:
    """Check offline scope and the expected current/historical review split."""
    assert payload["status"] == "valid", name
    assert payload["validationScope"] == "offline-manifest-integrity", name
    assert payload["canonicalResolution"]["status"] == "not-assessed", name
    assert payload["mapping"]["linkedComponents"] == 11, name
    assert payload["mapping"]["unmappedComponents"] == 19, name
    expected_historical = 0 if name == "baseline" else 1
    assert payload["reviewSummary"]["historical"] == expected_historical, name
    assert payload["reviewSummary"]["current"] == 11 - expected_historical, name


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ladon", type=Path, default=Path(sys.executable).with_name("ladon"))
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    base = Path(__file__).resolve().parent
    original_bytes = (base / "manifest.json").read_bytes()
    original = json.loads(original_bytes)
    records = []
    for name, manifest in variants(original):
        path = output / (name + ".json")
        save(path, manifest)
        record = run(args.ladon.resolve(), output, name, ["result", "validate", str(path)])
        verify(record, output)
        records.append(record)
    text_record = run(args.ladon.resolve(), output, "baseline-text", ["result", "validate", str(output / "baseline.json"), "--format", "text"])
    assert text_record["exitCode"] == 0
    text_payload = dict(line.split(": ", 1) for line in (output / text_record["stdout"]).read_text().splitlines())
    json_payload = json.loads((output / "baseline.stdout").read_text())
    assert {key: json.loads(value) for key, value in text_payload.items()} == json_payload
    records.append(text_record)
    for name in ("inspect", "guide"):
        record = run(args.ladon.resolve(), output, name, ["result", name, str(output / "baseline.json")])
        verify(record, output)
        records.append(record)
    assert (base / "manifest.json").read_bytes() == original_bytes
    save(output / "summary.json", {
        "status": "passed", "scope": "Frozen offline exposition baseline, including expected unavailable operations",
        "manifestDigest": "sha256:" + hashlib.sha256(original_bytes).hexdigest(),
        "cases": records, "caseCount": len(records), "leanRun": False,
    })
    print(f"PASS: {len(records)} offline scenarios; no Lean execution. Captures: {output}")


if __name__ == "__main__":
    main()
