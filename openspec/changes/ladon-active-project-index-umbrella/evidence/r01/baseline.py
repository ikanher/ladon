"""Capture the frozen HEAD wheel's index/name behavior on one disposable source tree."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError(f"{command}: {completed.stderr[-2000:]}")
    return completed.stdout


with tempfile.TemporaryDirectory(prefix="ladon-active-baseline-") as raw:
    temp = Path(raw)
    archive = temp / "source.tar"
    with archive.open("wb") as output:
        subprocess.run(["git", "archive", "HEAD"], cwd=ROOT, stdout=output, check=True)
    source = temp / "source"
    source.mkdir()
    with tarfile.open(archive) as bundle:
        bundle.extractall(source, filter="data")
    run(["uv", "build", "--force-pep517", "--out-dir", str(temp / "dist"), "."], source)
    wheel = next((temp / "dist").glob("*.whl"))
    venv = temp / "venv"
    run(["uv", "venv", "--python", "/home/codex/miniconda3/bin/python3.11", str(venv)], ROOT)
    run(["uv", "pip", "install", "--python", str(venv / "bin/python"), str(wheel)], ROOT)
    repo = temp / "lean"
    repo.mkdir()
    (repo / "Main.lean").write_text("theorem newLemmaNear : True := True.intro\n")
    cli = str(venv / "bin/ladon")

    def call(*args: str) -> dict:
        output = run([cli, "proof-search", *args, "--repo-root", str(repo), "--format", "json"], repo)
        return {"outputSha256": hashlib.sha256(output.encode()).hexdigest(),
                "outputBytes": len(output.encode()), "payload": json.loads(output)}

    built = call("index", "build")
    (repo / "Fresh.lean").write_text("theorem newLemma : True := True.intro\n")
    stored = call("search", "name", "--text", "newLemma", "--freshness", "stored")
    verified = call("search", "name", "--text", "newLemma", "--freshness", "verify")
    status = call("index", "status")
    print(json.dumps({
        "baseCommit": run(["git", "rev-parse", "HEAD"], ROOT).strip(),
        "wheelSha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "fixture": {"indexed": "newLemmaNear", "untracked": "newLemma"},
        "built": built, "stored": stored, "verified": verified, "status": status,
    }, indent=2))
