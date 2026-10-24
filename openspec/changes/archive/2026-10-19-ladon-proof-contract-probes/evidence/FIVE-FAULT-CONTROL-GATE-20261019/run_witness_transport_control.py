"""Freshly check the strong-to-weak witness control in the campaign context."""
from __future__ import annotations

import json
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_probes import check_application_probe, plan_application_probe

GATE = Path(__file__).resolve().parent
RUN = GATE / "fresh-run-03"
DEADLINE = float(json.loads((GATE / "fresh-run-01/RESULT.json").read_text())["deadlineMonotonic"])
OUT = RUN / "witness-dependence/strong-to-weak-control-02"
if OUT.exists():
    raise SystemExit(f"refusing to overwrite existing attempt: {OUT}")
OUT.mkdir()
family_dir = RUN / "witness-dependence"
context = json.loads((family_dir / "context.json").read_text())
sides = json.loads((family_dir / "actual-sides.json").read_text())
repo = (family_dir / "repo").resolve()
limits = {"timeout_seconds": 30, "max_rss_bytes": 12 * 1024**3,
          "max_output_bytes": 8 * 1024**2}
request = {"repoRoot": str(repo), "context": context, "left": sides[0], "right": sides[1],
           "template": {"familyId": "witness-dependence", "version": "witness-dependence-v2",
                        "kind": "implication", "direction": "left-to-right"},
           "deadlineMonotonic": DEADLINE, "limits": limits}
terms = {"formal-reading": "Iff.rfl", "probe": """by
  intro h
  obtain ⟨w, hw⟩ := h
  intro x
  exact ⟨w, hw x⟩"""}
(OUT / "request.json").write_text(json.dumps(request, sort_keys=True, indent=2) + "\n")
(OUT / "terms.json").write_text(json.dumps(terms, sort_keys=True, indent=2) + "\n")
planned = plan_application_probe(request)
(OUT / "planned.json").write_text(json.dumps(planned, sort_keys=True, indent=2) + "\n")
if planned.get("status") != "planned":
    raise SystemExit(f"planning did not complete: {planned.get('diagnostic')}")
started = time.monotonic()
checked = check_application_probe(request, planned["planId"], terms)
(OUT / "checked.json").write_text(json.dumps(checked, sort_keys=True, indent=2) + "\n")
if checked.get("status") != "checked-local-implication" or len(checked.get("goals", [])) != 2:
    raise SystemExit(f"strong-to-weak control failed: {checked.get('status')}")
accepted = []
for goal in checked["goals"]:
    raw = load_goal_evidence(repo, goal["result"])
    if goal.get("status") != "checked-support" or not _accepted_check(raw):
        raise SystemExit(f"control receipt rejected: {goal.get('goalId')}")
    accepted.append(goal["goalId"])
if checked["artifact"]["payload"].get("checkRunRefs") != [] or any(
        goal.get("status") != "open" for goal in checked["artifact"]["payload"]["result"]["goals"]):
    raise SystemExit("checked authority leaked into the open plan")
result = {"status": "PASS", "family": "witness-dependence", "control": "strong-to-weak",
          "elapsedSeconds": time.monotonic() - started, "acceptedGoals": accepted,
          "deadlineMonotonic": DEADLINE, "cacheReuse": "none"}
(OUT / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
