"""Exercise existing Ladon completion on native generated feasibility goals.

This is supplied-term validation, not an unsupplied proof-search measurement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from time import monotonic

from ladon.proof_slice import pinned_toolchain
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import (
    SourceGoalCompletionRequest,
    complete_source_goal,
)

CASES = (
    ("Witness", "inhabited", False, "⟨0, rfl⟩", "completed"),
    (
        "Refutation",
        "impossible",
        True,
        "fun witness => Exists.elim witness (fun _ pair => "
        "Nat.zero_ne_one (pair.1.symm.trans pair.2))",
        "completed",
    ),
    ("Fixed", "fixed", True, "by decide", "completed"),
    ("Leak", "impossible", False, "by exact h0", "rejected"),
    ("Sorry", "impossible", False, "by sorry", "trust-rejected"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    # Freeze the complete input tree before resolving its pinned context.
    for name, subject, negate, _term, _expected in CASES:
        goal = f'premise_context% "FeasibilityProbe.Subjects.{subject}"'
        if negate:
            goal = f"¬ ({goal})"
        source = f"import Subjects\nexample : {goal} := by\n  skip\n"
        path = root / f"{name}.lean"
        if not path.exists() or path.read_text() != source:
            path.write_text(source)
    context = pinned_toolchain(root)
    started = monotonic()
    report = {
        "scope": "supplied-term validation on native generated goals; not operational discovery",
        "bounds": {"totalSeconds": 600, "maxRssBytes": 12 * 1024**3},
        "cases": [],
        "status": "running",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for name, subject, negate, term, expected in CASES:
        goal = f'premise_context% "FeasibilityProbe.Subjects.{subject}"'
        if negate:
            goal = f"¬ ({goal})"
        source = f"import Subjects\nexample : {goal} := by\n  skip\n"
        path = root / f"{name}.lean"
        remaining = 600 - (monotonic() - started)
        if remaining <= 0:
            raise RuntimeError("parent mathematical probe deadline exhausted")
        captured = capture_source_goal(
            SourceGoalCaptureRequest(
                root,
                path.name,
                name,
                3,
                6,
                context,
                timeout_seconds=min(60, remaining),
            )
        )
        row = {"id": name, "expectedStatus": expected, "capture": captured}
        report["cases"].append(row)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        if captured["status"] != "captured":
            raise RuntimeError(f"{name}: capture failed; see retained receipt")
        locals_ = captured["capture"]["goal"]["localContext"]
        if any(not local["implementationDetail"] for local in locals_):
            raise RuntimeError(f"{name}: witness environment has ambient locals")
        # Lean exposes the theorem-under-construction as an implementation
        # detail. Existing completion rejects any proof depending on it and
        # excludes it from the independently replayed closed proof context.
        row["implementationLocals"] = [local["localId"] for local in locals_]
        remaining = 600 - (monotonic() - started)
        if remaining <= 0:
            raise RuntimeError("parent mathematical probe deadline exhausted")
        result = complete_source_goal(
            SourceGoalCompletionRequest(
                root,
                captured["capture"],
                term,
                context,
                timeout_seconds=min(60, remaining),
            )
        )
        row["term"] = term
        row["completion"] = result
        row["sourceDigest"] = "sha256:" + hashlib.sha256(source.encode()).hexdigest()
        row["status"] = "passed" if result["status"] == expected else "failed"
        if expected == "completed":
            if (
                result["replay"]["status"] != "accepted"
                or not result["trust"]["accepted"]
            ):
                row["status"] = "failed"
        elif result["status"] == "completed":
            row["status"] = "failed"
        if row["status"] == "failed":
            report["status"] = "failed"
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(name, result["status"], row["status"], flush=True)
        if row["status"] != "passed":
            raise RuntimeError(
                f"{name}: completion outcome differs; see retained receipt"
            )
    report["status"] = "passed"
    report["elapsedSeconds"] = monotonic() - started
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
