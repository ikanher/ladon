"""Finish the inequality family within the original shared gate deadline."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
GATE = Path(__file__).resolve().parent
DEADLINE = float(json.loads((GATE / "fresh-run-01/RESULT.json").read_text())["deadlineMonotonic"])
START = DEADLINE - 1800
OUT = GATE / "fresh-run-03/inequality-wrapper"
if OUT.exists():
    raise SystemExit(f"refusing to overwrite retained attempt: {OUT}")
OUT.mkdir()
SOURCE = (ROOT / "openspec/changes/ladon-proof-contract-probes/evidence/"
          "INEQUALITY-DIRECTION-20261019/qualify-final.py")
script = SOURCE.read_text(encoding="utf-8")
for old, new in [
    ("import time\n", "import time\nimport os\n"),
    ("base = Path(__file__).resolve().parent",
     "base = Path(os.environ['LADON_GATE_OUTPUT']).resolve()"),
    ("planned = plan_application_probe(request)",
     "(attempt / f\"{label}-request.json\").write_text(json.dumps(request, sort_keys=True, indent=2))\n    planned = plan_application_probe(request)"),
    ("deadline = started + 1800", "deadline = float(os.environ['LADON_GATE_DEADLINE'])"),
]:
    if old not in script:
        raise RuntimeError(f"inequality qualifier patch anchor absent: {old!r}")
    script = script.replace(old, new, 1)
script_path = OUT.parent / "inequality-resume-qualify.py"
script_path.write_text(script, encoding="utf-8")
env = dict(os.environ)
env["LADON_GATE_OUTPUT"] = str(OUT.resolve())
env["LADON_GATE_DEADLINE"] = str(DEADLINE)
env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
started = time.monotonic()
try:
    proc = subprocess.run([sys.executable, str(script_path), "inequality-direction"],
                          cwd=ROOT, env=env, capture_output=True, text=True,
                          timeout=max(1.0, DEADLINE - time.monotonic()), check=False)
    stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
except subprocess.TimeoutExpired as error:
    stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
    stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
    returncode = -1
(OUT / "stdout.txt").write_text(stdout, encoding="utf-8")
(OUT / "stderr.txt").write_text(stderr, encoding="utf-8")
result_path = OUT / "inequality-direction/RESULT.json"
result = json.loads(result_path.read_text()) if result_path.is_file() else None
record = {"returncode": returncode, "elapsedSeconds": time.monotonic() - started,
          "campaignElapsedSeconds": time.monotonic() - START,
          "stdoutSha256": hashlib.sha256(stdout.encode()).hexdigest(),
          "stderrSha256": hashlib.sha256(stderr.encode()).hexdigest(),
          "result": result}
(OUT / "process-result.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(json.dumps({"returncode": returncode, "elapsedSeconds": record["elapsedSeconds"],
                  "campaignElapsedSeconds": record["campaignElapsedSeconds"],
                  "resultStatus": result.get("status") if result else None}, sort_keys=True), flush=True)
if returncode != 0 or not result or result.get("status") != "PASS":
    raise SystemExit(1)
