import argparse
import hashlib
import json
import time
from pathlib import Path

from ladon._proof_contract_context_goals import build_context_goals
from ladon.correspondence_check import prepare_correspondence
from ladon.proof_slice import extract_proof_slice

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
out = args.output.resolve()
report = {
    "scope": "Mathematical diagnostic probe, not scored full-corpus baseline; both conditionals are valid, source error not asserted",
    "cases": [],
    "status": "running",
}
var = {"tag": "var", "id": "n"}


def const(n):
    return {"tag": "const", "name": str(n)}


def eq(a, b):
    return {"tag": "eq", "left": a, "right": b}


def implies(a, b):
    return {"tag": "implies", "premise": a, "conclusion": b}


for name, hypotheses, conclusion, quote in [
    (
        "impossible",
        [eq(var, const(0)), eq(var, const(1))],
        eq(var, const(37)),
        "If a natural n equals both zero and one, then n = 37.",
    ),
    (
        "inhabited",
        [eq(var, const(0))],
        eq({"tag": "app", "symbol": "add", "args": [var, const(1)]}, const(1)),
        "If a natural n equals zero, then n + 1 = 1.",
    ),
]:
    start = time.monotonic()
    slice = extract_proof_slice(
        root,
        "Contexts.lean",
        "Contexts",
        "FeasibilityProbe." + name + "_use",
        "FeasibilityProbe." + name + "_step",
        0,
        scoped=True,
    )
    if not slice.get("complete"):
        raise RuntimeError(json.dumps(slice)[:3000])
    body = conclusion
    for h in reversed(hypotheses):
        body = implies(h, body)
    formula = {
        "tag": "forall",
        "binder": {"id": "n", "name": "n", "domain": "Nat"},
        "body": body,
    }
    reading = {
        "id": name,
        "source": {
            "path": "claim-" + name + ".txt",
            "startLine": 1,
            "endLine": 1,
            "quote": quote,
            "sha256": hashlib.sha256(quote.encode()).hexdigest(),
        },
        "formula": formula,
        "symbols": {"add": {"leanName": "Nat.add", "leanType": "Nat → Nat → Nat"}},
    }
    (root / ("claim-" + name + ".txt")).write_text(quote)
    plan = prepare_correspondence(reading, slice, {"n": "n"})
    goals = build_context_goals(
        plan, {"probe": "actual native extraction; no checked-status promotion"}
    )
    report["cases"].append(
        {
            "id": name,
            "expectedContext": (
                "inconsistent" if name == "impossible" else "witnessed"
            ),
            "sourceErrorExpected": False,
            "seconds": time.monotonic() - start,
            "slice": slice,
            "goals": goals,
            "residuals": plan["residuals"],
        }
    )
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(
        name, [(g["id"], g["goal"]) for g in goals if g["id"] == "domain"], flush=True
    )
report["status"] = "observed"
out.write_text(json.dumps(report, indent=2) + "\n")
