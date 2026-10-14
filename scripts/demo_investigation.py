"""Portable authored comparisons; no detection or theorem-certification claim."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def run(root, *args, expected=0):
    result = subprocess.run(
        [sys.executable, "-m", "ladon.entrypoint", "investigation", *args, "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != expected:
        raise RuntimeError(result.stdout + result.stderr)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    root = parser.parse_args().output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    source = root / "exposition.txt"
    lines = [
        "For every positive N and real vector a of length N, sum |a_i| <= C max |a_i| with C independent of N. Bound each summand by the maximum and add.",
        "For every positive N and real vector a of length N, sum |a_i| <= N max |a_i|. Bound each summand by the maximum and add.",
    ]
    source.write_text("\n".join(lines) + "\n")
    formal = root / "counterpart.txt"
    formal.write_text(
        "For every positive N and real vector a of length N, sum |a_i| <= N max |a_i|. Sum the N termwise bounds.\n"
    )
    plan_path = root / "plan.json"
    run(root, "init", "--text", str(source), "--output", str(plan_path), "--unit-lines", "1")
    early = run(root, "finish", "--plan", str(plan_path), expected=2)
    assert early["status"] == "continue"
    plan = json.loads(plan_path.read_text())
    contract = {
        "objects": "a real vector a with N entries; sum of absolute entries and their maximum",
        "assumptions": "N is a positive integer",
        "domains": "N in positive integers; a in R^N",
        "quantifiers": "for every N and every a",
        "conclusion": "sum |a_i| <= N max |a_i|",
        "dependencies": "termwise domination by max |a_i|",
        "neededImplication": "adding N termwise bounds gives the asserted total bound",
    }
    bound = {
        "path": formal.name,
        "sha256": hashlib.sha256(formal.read_bytes()).hexdigest(),
        "startLine": 1,
        "endLine": 1,
        "statement": formal.read_text().rstrip("\n"),
        "contract": contract,
    }
    for i, unit in enumerate(plan["units"]):
        unit.update(
            inventory="done", note="One assertion and its stated argument captured in this unit."
        )
        local = dict(contract)
        if i == 0:
            local.update(
                quantifiers="there exists finite C independent of N, for every N and a",
                conclusion="sum |a_i| <= C max |a_i|",
            )
        plan["claims"].append(
            {
                "id": f"claim-{i + 1}",
                "unit": unit["id"],
                "startLine": i + 1,
                "endLine": i + 1,
                "quote": lines[i],
                "state": "reviewed",
                "contract": local,
                "formal": bound,
                "judgment": {
                    "statement": "mismatch" if i == 0 else "aligned",
                    "method": "same",
                    "evidence": (
                        "Both arguments add the N termwise bounds. The first conclusion is unsupported: a_i=1 gives N <= C for all N. The counterpart retains the factor N."
                        if i == 0
                        else "Both claims retain the factor N, and both arguments add exactly N termwise bounds."
                    ),
                },
            }
        )
    plan_path.write_text(json.dumps(plan, indent=2) + "\n")
    final = run(root, "finish", "--plan", str(plan_path))
    assert final["status"] == "recorded-work-complete"
    assert final["counts"]["reviewedClaims"] == 2
    (root / "status.json").write_text(json.dumps(final, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": final["status"],
                "output": str(root),
                "authority": "authored portable comparison demonstration only",
            }
        )
    )


if __name__ == "__main__":
    main()
