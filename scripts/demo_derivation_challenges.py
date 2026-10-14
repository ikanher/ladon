"""Prepare source-bound challenge packets from public elementary case inputs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def invoke(root: Path, *arguments: str) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "investigation",
            *arguments,
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return json.loads(result.stdout)


def prepare(cases: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    for path in sorted(cases.glob("*/input.json")):
        data = json.loads(path.read_text())
        folder = output / data["id"]
        folder.mkdir()
        source = folder / "source.txt"
        source.write_bytes((path.parent / "source.txt").read_bytes())
        plan_path = folder / "plan.json"
        invoke(output, "init", "--text", str(source), "--output", str(plan_path), "--derivations")
        plan = json.loads(plan_path.read_text())
        quote = "\n".join(source.read_text().splitlines())
        unit = plan["units"][0]
        unit.update(
            inventory="done", note="One elementary implication supplied in this complete source."
        )
        goal = data["goal"]
        contract = {
            "objects": "Rational scalars: " + ", ".join(goal["variables"]),
            "assumptions": json.dumps(goal["premises"], sort_keys=True),
            "domains": "Every declared variable ranges over the rational numbers.",
            "quantifiers": "For all declared variables satisfying every premise.",
            "conclusion": json.dumps(goal["conclusion"], sort_keys=True),
            "dependencies": "Only the explicitly supplied premises; inspect the source argument.",
            "neededImplication": "The premises jointly imply exactly the encoded conclusion.",
        }
        step = {
            "id": "inference",
            "startLine": 1,
            "endLine": unit["endLine"],
            "quote": quote,
            "contract": contract,
            "rule": "The inference stated in the source quotation.",
            "substitution": "Each scalar name refers to the same rational in source and AST.",
            "dependsOn": [],
            "arithmetic": goal,
        }
        plan["claims"] = [
            {
                "id": data["id"],
                "unit": unit["id"],
                "startLine": 1,
                "endLine": unit["endLine"],
                "quote": quote,
                "state": "contract",
                "contract": contract,
                "concern": "Check this local inference independently.",
                "derivation": {"author": "case-transcriber", "steps": [step]},
            }
        ]
        plan_path.write_text(json.dumps(plan, indent=2) + "\n")
        invoke(
            output,
            "challenge",
            "--plan",
            str(plan_path),
            "--claim",
            data["id"],
            "--output",
            str(folder / "challenge.json"),
        )
    print(
        json.dumps(
            {
                "status": "prepared",
                "cases": len(list(output.glob("*/challenge.json"))),
                "output": str(output),
                "nonclaim": "No case classifications were supplied.",
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("tests/fixtures/derivation_challenges"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.cases.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
