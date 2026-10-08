"""Replay one audit source using Ladon's existing bounded process owner.

Run from the Ladon repository: uv run python PATH/replay.py RUN_ID FILE.lean
Each run is append-only; failed source bytes are retained beside the output.
These are ordinary compiler records, not canonical Ladon proof receipts.
"""
from pathlib import Path
import dataclasses
import hashlib
import json
import os
import re
import shutil
import sys
from ladon.process_supervisor import run_bounded_target_process

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
FIXTURE = ROOT / ".codex/state/proof-correspondence-audit-r70/fixture"
run_id, source = sys.argv[1:]
path = Path(source).resolve()
out = HERE / "runs" / run_id
out.mkdir()  # never replace an earlier attempt
shutil.copyfile(path, out / path.name)
cmd = [str(Path.home() / ".elan/bin/lake"), "env", "lean", str(path)]
result = run_bounded_target_process(cmd, cwd=FIXTURE, timeout_seconds=180,
    max_output_bytes=8 * 1024 * 1024, max_rss_bytes=32 * 1024**3, env=os.environ)
(out / "stdout.txt").write_text(result.stdout)
(out / "stderr.txt").write_text(result.stderr)
axioms = re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]", result.stdout)
allowed = {"propext", "Classical.choice", "Quot.sound"}
policy = [{"declaration": name, "axioms": [a.strip() for a in values.split(",") if a.strip()],
           "permitted": all(a.strip() in allowed for a in values.split(",") if a.strip())}
          for name, values in axioms]
record = dataclasses.asdict(result)
record.pop("stdout"); record.pop("stderr")
record.update({"cwd": str(FIXTURE), "source": str(path.relative_to(ROOT)),
    "sourceSha256": hashlib.sha256(path.read_bytes()).hexdigest(), "axiomPolicy": policy,
    "policyScope": "only explicitly printed declarations; no claim about unprinted enclosing modules",
    "leanToolchain": (FIXTURE / "lean-toolchain").read_text().strip(),
    "manifestSha256": hashlib.sha256((FIXTURE / "lake-manifest.json").read_bytes()).hexdigest(),
    "supervisorSha256": hashlib.sha256((ROOT / "src/ladon/process_supervisor.py").read_bytes()).hexdigest(),
    "memoryLimitBytes": 32 * 1024**3, "memoryMechanism": "sampled aggregate process-tree RSS",
    "kind": "ordinary compiler observation, root-authored record"})
(out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"run": run_id, "returncode": result.returncode,
    "elapsedSeconds": result.elapsed_seconds, "peakRssBytes": result.peak_rss_bytes,
    "printedPolicyResults": policy}, indent=2))
print(result.stdout)
print(result.stderr)
sys.exit(0 if result.succeeded else 1)
