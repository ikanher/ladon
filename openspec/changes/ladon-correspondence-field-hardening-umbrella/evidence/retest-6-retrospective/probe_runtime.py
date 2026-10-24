"""Portable public-CLI reporting probe; authored labels are not semantic proofs."""

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
import subprocess
import tempfile


def checkout():
    return next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())


def observe():
    root = checkout()
    env = {**os.environ, "PYTHONPATH": str(root / "src")}
    rows = []
    with tempfile.TemporaryDirectory(prefix="ladon-reporting-regression-") as name:
        work = Path(name)
        source = work / "source.txt"
        source.write_text("An operator has the displayed bound.\n", encoding="utf-8")
        binding = {
            "path": "source.txt", "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "startLine": 1, "endLine": 1,
        }
        contract = {key: "Authored portable contract; no mathematical checking claimed."
                    for key in ("objects", "assumptions", "domains", "quantifiers",
                                "conclusion", "dependencies", "neededImplication")}
        for statement, method in [("aligned", "same"), ("mismatch", "different"),
                                  ("aligned", "different")]:
            case_id = f"{statement}-{method}"
            plan = {
                "version": 1, "startedAt": datetime.now(UTC).isoformat(),
                "budgetSeconds": 5400, "scope": binding,
                "units": [{"id": "u", "startLine": 1, "endLine": 1,
                           "inventory": "done", "note": "Synthetic reporting fixture."}],
                "claims": [{"id": "c", "unit": "u", "startLine": 1, "endLine": 1,
                            "quote": source.read_text().strip(), "state": "reviewed",
                            "contract": contract,
                            "formal": {**binding, "statement": source.read_text().strip(),
                                       "contract": contract},
                            "judgment": {"statement": statement, "method": method,
                                         "evidence": "Authored label for transport test only."}}],
            }
            path = work / f"{case_id}.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            command = [str(root / ".venv/bin/python"), "-m", "ladon.entrypoint",
                       "investigation", "status", "--root", str(work), "--plan", str(path)]
            proc = subprocess.run(command, env=env, text=True, capture_output=True,
                                  check=False, timeout=30)
            rows.append({"id": case_id, "inputJudgment": plan["claims"][0]["judgment"],
                         "exitCode": proc.returncode, "stdout": json.loads(proc.stdout),
                         "stderr": proc.stderr})
    return {"schema": "reporting-observation-v1", "runtimeSource": str(root / "src"),
            "authority": "Public CLI replay of authored labels, not semantic detection.",
            "cases": rows}


if __name__ == "__main__":
    print(json.dumps(observe(), indent=2))
