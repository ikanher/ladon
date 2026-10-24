"""One bounded follow-up using the source campaign's unchanged absolute clock."""
from __future__ import annotations

import copy
import json
import time
from pathlib import Path

from ladon.proof_contract_route_context import (
    check_route_context_bridge,
    plan_route_context_bridge,
)

BASE = Path(__file__).resolve().parent
RUN = BASE / "run"
OUT = BASE / "follow-up"


def load(name):
    return json.loads((RUN / name).read_text())


def save(name, value):
    with (OUT / name).open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)


def main():
    OUT.mkdir()
    positive = load("positive-request.json")
    planned = load("positive-plan.json")
    deadline = positive["deadlineMonotonic"]
    assert deadline > time.monotonic()
    save("INHERITED-CLOCK.json", {"deadlineMonotonic": deadline,
         "startedFollowUpMonotonic": time.monotonic(), "budgetSeconds": 1200,
         "limits": positive["limits"], "priorAttempt": "../run/excluded-parent-result.json",
         "alternative": "fully qualified excluded parent identifier; no cap or clock change"})
    for name, term in (("excluded-parent", "by exact _root_.ThreeSteps.endpoint"),
                       ("closed-reading", "by assumption")):
        assert time.monotonic() < deadline
        terms = {"source-reading": term}
        save(name + "-terms.json", terms)
        result = check_route_context_bridge(positive, planned["planId"], terms)
        save(name + "-result.json", result)
        print(name, result["status"], result["elapsedSeconds"], flush=True)
        assert result["status"] == "unresolved-bridge" and not result["demandDischarged"]
        assert all(g["status"] != "checked-support" for g in result["goals"])
    for name, mutate in (
        ("changed-reading", lambda r: r["sourceBindings"]["parentInterpretationRef"].update(localId="other-reading")),
        ("wrong-provider", lambda r: r["sourceBindings"].update(providerSnapshot=load("secondBound-snapshot.json"))),
        ("forged-assumption", lambda r: r.update(assumptions=["original desired conclusion"])),
        ("forged-rule", lambda r: r["analysisArtifact"]["payload"]["request"]["ruleBindings"][0].update(ruleId="caller-rule")),
        ("changed-order", lambda r: r["selectedIdentity"].update(premiseOrdinal=999)),
    ):
        assert time.monotonic() < deadline
        request = copy.deepcopy(positive)
        mutate(request)
        save(name + "-input.json", request)
        result = plan_route_context_bridge(request)
        save(name + "-result.json", result)
        assert result["status"] == "rejected" and not result["demandDischarged"]
    request = copy.deepcopy(positive)
    request["deadlineMonotonic"] -= 0.5
    result = check_route_context_bridge(request, planned["planId"], {})
    save("changed-checkpoint-result.json", result)
    assert result["status"] == "rejected" and not result["demandDischarged"]
    for name in ("expired", "expired-native"):
        assert time.monotonic() < deadline
        request = copy.deepcopy(positive)
        if name == "expired":
            request["deadlineMonotonic"] = time.monotonic() - 1
        else:
            request["analysisArtifact"]["payload"]["request"]["bounds"]["deadlineUtc"] = "2000-01-01T00:00:00Z"
        result = plan_route_context_bridge(request)
        save(name + "-result.json", result)
        assert result["status"] == "incomplete" and "preparation" not in result
    assert time.monotonic() < deadline
    request = copy.deepcopy(positive)
    request["limits"]["max_rss_bytes"] = 1024**2
    save("memory-stop-input.json", request)
    result = plan_route_context_bridge(request)
    save("memory-stop-result.json", result)
    assert result["status"] == "incomplete" and result["memoryReportBackRequired"]
    assert not result["demandDischarged"]
    assert "Stop progress and report back to user" in result["diagnostic"]["message"]
    # No more proof work follows the deliberate memory stop.
    elapsed = time.monotonic() - (deadline - 1200)
    assert elapsed < 1200
    save("acceptance.json", {"status": "PASS", "elapsedSeconds": elapsed,
         "budgetSeconds": 1200, "includesFailedInitialDriver": True,
         "outerDeadlineMonotonic": deadline, "positiveGoals": 13,
         "originalDriverStatus": "incomplete-at-excluded-parent-timeout",
         "followUp": "one explicit alternative term under the same clock and caps",
         "memoryStop": "last/no-retry", "detectionBenefit": "unmeasured"})
    print("PASS", elapsed, flush=True)


if __name__ == "__main__":
    main()
