"""Native feasibility experiment; successful checks are not public lift receipts.

Run with PYTHONPATH=src from the Ladon checkout. The output directory must be new.
All six cases share one deadline; no downloads, builds, or retries are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import time
from pathlib import Path

import ladon
from ladon.proof_contract_bridge import _resource_stop
from ladon.proof_contract_lift_goals import plan_nat_rational_lift
from ladon.proof_contract_obligation_supervision import _execute_job
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/proof_contract_lifting"
MAPPING = """intro n
    change (n < 2 → n = 0) ↔ (((n : Rat) < ((2 : Nat) : Rat)) →
      ((n : Rat) = ((0 : Nat) : Rat)))
    rw [Rat.natCast_lt_natCast, Rat.natCast_inj]"""
REALIZATION = f"""by
  refine ⟨Iff.rfl, ?_, ?_, ?_⟩
  · {MAPPING}
  · refine ⟨1, rfl, ?_⟩
    unfold LiftFixture.Predicate
    decide
  · intro h
    have bad : (1 : Nat) = 0 := h 1 (by decide)
    cases bad
"""
INCOMPATIBILITY = f"""by
  refine ⟨Iff.rfl, ?_, ?_⟩
  · {MAPPING}
  · rintro ⟨n, h⟩
    have bad := congrArg Rat.num h
    change Int.ofNat n = Int.negSucc 0 at bad
    cases bad
"""


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _goal():
    return {
        "variables": ["x"],
        "premises": [{"op": "lt", "left": {"var": "x"}, "right": {"rat": 2}}],
        "conclusion": {"op": "eq", "left": {"var": "x"}, "right": {"rat": 0}},
    }


def _cases():
    return [
        ("realization", "1", "realization", REALIZATION, "checked", "nat-cast-v1", False),
        ("incompatible", "-1", "incompatibility", INCOMPATIBILITY, "checked", "nat-cast-v1", False),
        ("unsupported", "1", "realization", None, "unsupported", "analytic-v1", False),
        ("changed-witness", "1/2", "realization", REALIZATION, "proof-rejected", "nat-cast-v1", False),
        ("omitted-assumption", "1", "realization", REALIZATION, "proof-rejected", "nat-cast-v1", True),
        ("admitted-proof", "1", "realization", "by sorry", "trust-rejected", "nat-cast-v1", False),
    ]


def _request(case, source):
    name, value, mode, _term, _expected, profile, strict = case
    witness = {"id": name, "status": "abstract-countermodel", "assignment": {"x": value}}
    interpretation = {
        "profile": profile, "source": {"path": "Fixture.lean", "sha256": _digest(source)},
        "formalClaim": "LiftFixture.StrictClaim" if strict else "LiftFixture.Claim",
        "formalPredicate": "LiftFixture.StrictPredicate" if strict else "LiftFixture.Predicate",
    }
    return plan_nat_rational_lift(_goal(), witness, interpretation, mode=mode)


def _check(workspace, plan, term, deadline):
    limits = {"timeout_seconds": 120, "max_output_bytes": 8 * 1024**2,
              "max_rss_bytes": DEFAULT_MAX_RSS_BYTES}
    request = {
        "repoRoot": str(workspace), "sourcePath": "Fixture.lean",
        "sourceDigest": "sha256:" + plan["interpretation"]["source"]["sha256"],
        "goal": plan["goal"], "term": term, "symbols": {},
    }
    return _execute_job(
        {"version": 1, "operation": "check-goal", "request": request},
        {**limits, "deadlineMonotonic": deadline},
        {"receipt": None, "inputDigest": None, "bounds": None}, None,
        worker_module="ladon.proof_contract_bridge_worker",
    )


def _accepted(raw):
    completion = raw.get("completion") or {}
    capture = (raw.get("capture") or {}).get("capture") or {}
    replay, trust = completion.get("replay") or {}, completion.get("trust") or {}
    return all((raw.get("status") == "supported", completion.get("status") == "completed",
                replay.get("status") == "accepted", trust.get("accepted") is True,
                trust.get("coverage") == "complete", _same_goal(completion, capture)))


def _same_goal(completion, capture):
    original = (completion.get("application") or {}).get("originalGoal") or {}
    goal = capture.get("goal") or {}
    return (bool(goal.get("typeStructural"))
            and original.get("typeStructural") == goal["typeStructural"]
            and original.get("localContext") == goal.get("localContext"))


def _observed(checked):
    if checked.get("status") != "completed":
        return checked.get("status", "incomplete")
    raw = checked.get("result") or {}
    if _accepted(raw):
        return "checked"
    completion = raw.get("completion") or {}
    if completion.get("status") == "trust-rejected":
        return "trust-rejected"
    # A timeout or infrastructure failure cannot pass a mathematical negative control.
    if completion.get("status") == "rejected":
        return "rejected"
    return "unresolved"


def _run_case(case, workspace, output, source, deadline):
    name, _value, _mode, term, expected, _profile, _strict = case
    started = time.monotonic()
    plan = _request(case, source)
    _write(output / (name + "-plan.json"), plan)
    if time.monotonic() >= deadline:
        return {"case": name, "expected": expected, "observed": "incomplete", "passed": False}
    if plan["status"] == "unsupported":
        checked, observed = None, "unsupported"
    else:
        (output / (name + "-term.lean")).write_text(term)
        checked = _check(workspace, plan, term, deadline)
        _write(output / (name + "-check.json"), checked)
        observed = _observed(checked)
    row = {"case": name, "planId": plan["planId"], "expected": expected,
           "observed": observed, "passed": _case_passed(expected, observed),
           "elapsedSeconds": time.monotonic() - started}
    row["resourceStop"] = _resource_stop(checked, {"max_rss_bytes": DEFAULT_MAX_RSS_BYTES})
    print(json.dumps(row), flush=True)
    return row


def _case_passed(expected, observed):
    if expected == "proof-rejected":
        return observed in {"rejected", "trust-rejected"}
    return observed == expected


def _effective_deadline(started, timeout, external):
    if external is None:
        return started + timeout
    if type(external) not in (int, float) or not math.isfinite(external):
        raise ValueError("external deadline must be a finite native number")
    return min(started + timeout, external)


def run(output, timeout, external_deadline=None):
    Path(ladon.__file__).resolve().relative_to(ROOT / "src")
    started = time.monotonic()
    deadline = _effective_deadline(started, timeout, external_deadline)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    workspace.mkdir()
    for name in ("lean-toolchain", "Fixture.lean"):
        shutil.copyfile(FIXTURE / name, workspace / name)
    source = (workspace / "Fixture.lean").read_bytes()
    identity = {"sourceSha256": _digest(source),
                "plannerSha256": _digest((ROOT / "src/ladon/proof_contract_lift_goals.py").read_bytes()),
                "runnerSha256": _digest(Path(__file__).read_bytes()),
                "toolchain": (workspace / "lean-toolchain").read_text().strip()}
    _write(output / "start.json", {"deadlineMonotonic": deadline, "startedMonotonic": started,
                                  "timeoutSeconds": timeout, "externalDeadline": external_deadline,
                                  "identity": identity})
    rows = []
    for case in _cases():
        rows.append(_run_case(case, workspace, output, source, deadline))
        if rows[-1].get("resourceStop") or time.monotonic() >= deadline:
            break
    unchanged = (workspace / "Fixture.lean").read_bytes() == source
    result = {"schema": "ladon-lift-feasibility-experiment-v1", "cases": rows,
              "passed": len(rows) == len(_cases()) and all(row["passed"] for row in rows) and unchanged,
              "sourceUnchanged": unchanged, "elapsedSeconds": time.monotonic() - started,
              "identity": identity, "scope": "constructed-source-interpretation-only",
              "publicLiftClassifierImplemented": False, "sourceFormulaFidelity": "unverified"}
    _write(output / "RESULT.json", result)
    return 0 if result["passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--deadline-monotonic", type=float,
                        help="Reuse an earlier absolute deadline on this host; cannot extend the budget.")
    args = parser.parse_args()
    if not 1 <= args.timeout_seconds <= 1800:
        parser.error("timeout must be within the shared 30-minute gate")
    return run(args.output, args.timeout_seconds, args.deadline_monotonic)


if __name__ == "__main__":
    raise SystemExit(main())
