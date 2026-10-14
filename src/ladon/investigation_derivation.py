"""Source-bound authored derivations and independently attributed challenges."""

from __future__ import annotations

import hashlib
import json

from ladon.investigation import CONTRACT_FIELDS, _array, _contract, _object, _require, _text
from ladon.rational_witness import check_witness, validate_goal

CLAIM_CONTEXT = ("id", "unit", "startLine", "endLine", "quote", "contract", "formal")
STEP_FIELDS = (
    "id",
    "startLine",
    "endLine",
    "quote",
    "contract",
    "rule",
    "substitution",
    "dependsOn",
    "arithmetic",
)


def step_subject(plan, claim, step):
    derivation = claim["derivation"]
    context = {
        "scope": plan["scope"],
        "claim": {key: claim[key] for key in CLAIM_CONTEXT if key in claim},
        "author": derivation["author"],
        "steps": [
            {k: v for k, v in item.items() if k != "challenge"} for item in derivation["steps"]
        ],
        "target": step["id"],
    }
    data = json.dumps(context, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _assessment(value, label):
    value = _object(value, label)
    _require(
        value.get("outcome") in ("supported", "refuted", "unresolved"), f"invalid {label} outcome"
    )
    _text(value.get("evidence"), f"{label} evidence")
    return value


def _action(claim, kind, step=None):
    result = {
        "kind": kind,
        "claim": claim["id"],
        "unit": claim["unit"],
        "startLine": claim["startLine"],
        "endLine": claim["endLine"],
    }
    if step is not None:
        result.update(
            step=step["id"],
            startLine=step["startLine"],
            endLine=step["endLine"],
            sourceAssertion=step["quote"],
        )
    else:
        result["sourceAssertion"] = claim["quote"]
    return result


def derivation_work(plan, reader):
    """Return priority work and findings, with all source and review bindings checked."""
    priority, findings, suspicious, open_claims = [], [], set(), set()
    total = 0
    for claim in sorted(plan["claims"], key=lambda c: (c["startLine"], c["id"])):
        work, needs_steps, count = _claim_derivation_work(plan, claim, reader, findings, total)
        total += count
        if needs_steps:
            suspicious.add(claim["id"])
        if claim["state"] != "blocked":
            if work:
                open_claims.add(claim["id"])
            priority.extend(work)
    return priority, findings, suspicious, open_claims


def _claim_derivation_work(plan, claim, reader, findings, total):
    needs_steps = _needs_derivation_steps(claim, reader)
    if not needs_steps:
        return [], False, 0
    work = []
    if "contract" not in claim:
        work.append(_action(claim, "write-exact-contract"))
    if "derivation" not in claim:
        work.append(_action(claim, "decompose-derivation"))
    else:
        derivation = _object(claim["derivation"], "derivation")
        author = _text(derivation.get("author"), "derivation author")
        steps = _array(derivation.get("steps"), "derivation steps")
        _require(1 <= len(steps) <= 128, "derivation needs 1..128 steps")
        _require(total + len(steps) <= 4096, "too many derivation steps")
        _validate_derivation_steps(plan, claim, steps, reader)
        for step in steps:
            _step_work(plan, claim, step, author, work, findings)
    return work, True, len(steps) if "derivation" in claim else 0


def _validate_derivation_steps(plan, claim, steps, reader):
    seen = set()
    # Validate the entire context before hashing or consuming a challenge.
    for step in steps:
        _object(step, "step")
        sid = _text(step.get("id"), "step id")
        _require(sid not in seen, "duplicate step id")
        _require(
            type(step.get("startLine")) is int
            and type(step.get("endLine")) is int
            and claim["startLine"]
            <= step["startLine"]
            <= step["endLine"]
            <= claim["endLine"],
            "step span must be inside claim",
        )
        reader.span(
            {
                **plan["scope"],
                **{k: step[k] for k in ("startLine", "endLine")},
                "quote": step.get("quote"),
            },
            "quote",
        )
        _contract(step.get("contract"))
        _text(step.get("rule"), "step rule")
        _text(step.get("substitution"), "step substitution")
        dependencies = _array(step.get("dependsOn"), "step dependencies")
        for dep in dependencies:
            _require(
                isinstance(dep, str) and dep in seen, "dependency must name an earlier step"
            )
        _require(len(set(dependencies)) == len(dependencies), "duplicate dependency")
        seen.add(sid)
        if "assessment" in step:
            _assessment(step["assessment"], "assessment")
        if "arithmetic" in step:
            validate_goal(step["arithmetic"])


def _checked_challenge(plan, claim, step, author, challenge, findings):
    checked = None
    if challenge is not None:
        _assessment(challenge, "challenge")
        reviewer = _text(challenge.get("reviewer"), "challenge reviewer")
        _require(
            reviewer.strip() != author.strip(), "challenge needs a different reviewer"
        )
        _require(
            challenge.get("subjectSha256") == step_subject(plan, claim, step),
            "stale challenge subject",
        )
        if "witness" in challenge:
            _require("arithmetic" in step, "witness needs stored arithmetic")
            checked = check_witness(step["arithmetic"], challenge["witness"])
            _require(
                challenge["outcome"] != "refuted"
                or checked["status"] == "counterexample",
                "refutation witness does not refute the stored implication",
            )
            if checked["status"] == "counterexample":
                findings.append(
                    {
                        "kind": "checked-arithmetic-counterexample",
                        "claim": claim["id"],
                        "step": step["id"],
                        "subjectSha256": challenge["subjectSha256"],
                        "check": checked,
                        "authority": "exact authored rational implication only",
                    }
                )
    return checked


def _step_work(plan, claim, step, author, work, findings):
    assessment = step.get("assessment")
    challenge = step.get("challenge")
    checked = _checked_challenge(plan, claim, step, author, challenge, findings)
    if _counterexample_needs_reconciliation(checked, assessment, challenge):
        work.append(_action(claim, "reconcile-step", step))
    elif not assessment or assessment["outcome"] == "unresolved":
        work.append(_action(claim, "investigate-step", step))
    elif challenge is None:
        work.append(_action(claim, "challenge-step", step))
    elif (
        challenge["outcome"] == "unresolved"
        or challenge["outcome"] != assessment["outcome"]
    ):
        work.append(_action(claim, "reconcile-step", step))
    elif challenge["outcome"] == "refuted" and checked is None:
        findings.append(
            {
                "kind": "attributed-step-refutation",
                "claim": claim["id"],
                "step": step["id"],
                "evidence": challenge["evidence"],
                "authority": "agreement of authored assessments only",
            }
        )


def find_step(plan, claim_id, step_id=None):
    _require(plan.get("version") == 2, "derivation commands require a version-two plan")
    claims = [c for c in plan["claims"] if c["id"] == claim_id]
    _require(len(claims) == 1, "unknown claim")
    claim = claims[0]
    _require("derivation" in claim, "claim needs a derivation")
    if step_id is None:
        return claim, None
    steps = [s for s in claim["derivation"]["steps"] if s["id"] == step_id]
    _require(len(steps) == 1, "unknown step")
    return claim, steps[0]


def challenge_packet(plan, claim_id):
    """Call after assess: whitelist original obligations, never forward prior judgments."""
    claim, _ = find_step(plan, claim_id)
    public = _public_claim(claim)
    steps = _public_steps(plan, claim)
    return {
        "schema": "ladon-derivation-challenge-v1",
        "scope": {k: plan["scope"][k] for k in ("path", "sha256", "startLine", "endLine")},
        "claim": public,
        "author": claim["derivation"]["author"],
        "steps": steps,
        "instructions": "Challenge each original implication. Save first responses separately; "
        "a sampled success is not a proof. Reviewer identity and interpretation "
        "remain attributed, and this packet does not enforce filesystem isolation.",
    }


def _public_claim(claim):
    public = {key: claim[key] for key in ("id", "unit", "startLine", "endLine", "quote")}
    if "contract" in claim:
        public["contract"] = {key: claim["contract"][key] for key in CONTRACT_FIELDS}
    if "formal" in claim:
        formal = claim["formal"]
        public["formal"] = {
            key: formal[key] for key in ("path", "sha256", "startLine", "endLine", "statement")
        }
        public["formal"]["contract"] = {key: formal["contract"][key] for key in CONTRACT_FIELDS}
    return public


def _public_steps(plan, claim):
    steps = []
    for step in claim["derivation"]["steps"]:
        item = {key: step[key] for key in STEP_FIELDS if key in step}
        item["contract"] = {key: step["contract"][key] for key in CONTRACT_FIELDS}
        item["subjectSha256"] = step_subject(plan, claim, step)
        steps.append(item)
    return steps


def _needs_derivation_steps(claim, reader):
    if "concern" in claim:
        _text(claim["concern"], "concern")
    if "contract" in claim:
        _contract(claim["contract"])
    if "formal" in claim:
        reader.span(claim["formal"], "statement")
        _contract(claim["formal"].get("contract"))
    judgment = claim.get("judgment", {}) if claim["state"] == "reviewed" else {}
    needs_steps = (
        "concern" in claim
        or "derivation" in claim
        or (
            bool(judgment)
            and (judgment["statement"] != "aligned" or judgment["method"] != "same")
        )
    )
    return needs_steps


def _counterexample_needs_reconciliation(checked, assessment, challenge):
    return (
        checked
        and checked["status"] == "counterexample"
        and (
            not assessment
            or assessment["outcome"] != "refuted"
            or challenge["outcome"] != "refuted"
        )
    )
