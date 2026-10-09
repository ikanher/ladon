"""Run the active-index CLI fixture against one built wheel on both supported runtimes."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SMOKE = Path(__file__).with_name("active-index-smoke.py")
PYTHONS = {
    "3.11": Path("/home/codex/miniconda3/bin/python3.11"),
    "3.12": Path("/home/codex/.local/bin/python3.12"),
}


def run(command: list[str], *, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"{command}: {result.stdout[-2000:]} {result.stderr[-2000:]}")
    return result.stdout


with tempfile.TemporaryDirectory(prefix="ladon-active-installed-") as raw:
    temp = Path(raw)
    run(["uv", "build", "--force-pep517", "--out-dir", str(temp / "dist"), "."])
    wheel = next((temp / "dist").glob("*.whl"))
    results = {}
    for version, python in PYTHONS.items():
        venv = temp / f"venv-{version}"
        run(["uv", "venv", "--python", str(python), str(venv)])
        installed = venv / "bin/python"
        run(["uv", "pip", "install", "--python", str(installed), str(wheel)])
        run(["uv", "pip", "check", "--python", str(installed)])
        origin = run([
            str(installed), "-c", "import ladon; print(ladon.__file__)",
        ]).strip()
        assert Path(origin).is_relative_to(venv), origin
        environment = dict(os.environ, LADON_CLI=str(venv / "bin/ladon"))
        results[version] = {"originInInstalledVenv": True,
                            "smoke": json.loads(run([str(installed), str(SMOKE)], env=environment))}
    print(json.dumps({
        "wheelSha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "runtimes": results,
    }, indent=2))
