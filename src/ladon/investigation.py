"""Source-bound investigation bookkeeping; never a mathematical verdict."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import UTC, datetime
from pathlib import Path

CONTRACT_FIELDS = (
    "objects",
    "assumptions",
    "domains",
    "quantifiers",
    "conclusion",
    "dependencies",
    "neededImplication",
)
MAX_PLAN_BYTES = 4 * 1024 * 1024
MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_RECORDS = 4096


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _object(value, label):
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _text(value, label):
    _require(isinstance(value, str) and value.strip(), f"{label} must be nonempty text")
    return value


def _integer(value, label, minimum=1, maximum=None):
    _require(type(value) is int and value >= minimum, f"{label} must be an integer >= {minimum}")
    _require(maximum is None or value <= maximum, f"{label} exceeds its bound")
    return value


def _array(value, label):
    _require(isinstance(value, list) and len(value) <= MAX_RECORDS, f"invalid {label}")
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_plan(path: Path, *, max_bytes=None):
    if max_bytes is None:
        max_bytes = MAX_PLAN_BYTES
    _require(type(max_bytes) is int and 1 <= max_bytes <= 32 * 1024**2, "invalid JSON input byte bound")
    with path.open("rb") as stream:
        data = stream.read(max_bytes + 1)
    _require(len(data) <= max_bytes, f"plan exceeds {max_bytes} bytes")
    try:
        return json.loads(
            data,
            object_pairs_hook=_pairs,
            parse_constant=lambda x: _require(False, f"nonfinite JSON value: {x}"),
        )
    except (UnicodeDecodeError, RecursionError) as exc:
        raise ValueError("plan must be bounded UTF-8 JSON") from exc


class SourceReader:
    """Read only regular UTF-8 files beneath the explicitly supplied root."""

    def __init__(self, root: Path):
        try:
            self.root = root.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ValueError("source root is unavailable") from exc
        _require(self.root.is_dir(), "source root must be a directory")
        self.cache = {}
        self.total = 0

    def read(self, name):
        try:
            return self._read(name)
        except (OSError, RuntimeError) as exc:
            raise ValueError("source is unavailable beneath allowed root") from exc

    def _read(self, name):
        name = _text(name, "source path")
        path = (self.root / name).resolve(strict=True)
        _require(path.is_relative_to(self.root), "source escapes allowed root")
        if path in self.cache:
            return self.cache[path]
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        with os.fdopen(os.open(path, flags), "rb") as stream:
            _require(
                stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "source is not a regular file"
            )
            descriptor = Path(f"/proc/self/fd/{stream.fileno()}")
            if descriptor.exists():
                _require(
                    descriptor.resolve().is_relative_to(self.root), "opened source escapes root"
                )
            data = stream.read(MAX_SOURCE_BYTES + 1)
        _require(len(data) <= MAX_SOURCE_BYTES, "source exceeds 8 MiB")
        self.total += len(data)
        _require(self.total <= MAX_TOTAL_BYTES, "sources exceed 128 MiB")
        try:
            lines = data.decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise ValueError("source must be UTF-8 text, not a PDF or binary") from exc
        _require(bool(lines), "source has no lines")
        result = (hashlib.sha256(data).hexdigest(), lines)
        self.cache[path] = result
        return result

    def span(self, record, quote_key=None):
        record = _object(record, "source reference")
        digest, lines = self.read(record.get("path"))
        _require(record.get("sha256") == digest, "stale source digest")
        start = _integer(record.get("startLine"), "startLine")
        end = _integer(record.get("endLine"), "endLine", start, len(lines))
        quote = "\n".join(lines[start - 1 : end])
        if quote_key:
            _require(_text(record.get(quote_key), quote_key) == quote, "quoted source span changed")
        return quote


def _contract(value):
    value = _object(value, "local contract")
    for field in CONTRACT_FIELDS:
        _text(value.get(field), f"contract.{field}")


def _blocker(value):
    value = _object(value, "blocker")
    for key in ("kind", "evidence", "nextAction", "unblockCondition"):
        _text(value.get(key), f"blocker.{key}")


def initialize(text: Path, root: Path, *, minutes=90, unit_lines=80, now=None, derivations=False,
               correspondence=False):
    if correspondence:
        if derivations:
            raise ValueError("correspondence and derivations cannot be combined")
        from ladon.investigation_correspondence import initialize_v3

        return initialize_v3(text, root, minutes=minutes, unit_lines=unit_lines, now=now)
    _integer(unit_lines, "unit_lines", maximum=10000)
    _integer(minutes, "minutes", maximum=10080)
    reader = SourceReader(root)
    try:
        path = text.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("text source is unavailable") from exc
    _require(path.is_relative_to(reader.root), "text escapes allowed root")
    name = str(path.relative_to(reader.root))
    digest, lines = reader.read(name)
    starts = range(1, len(lines) + 1, unit_lines)
    _require(len(starts) <= MAX_RECORDS, "too many units; increase unit-lines")
    units = [
        {
            "id": f"unit-{i + 1:04d}",
            "startLine": start,
            "endLine": min(start + unit_lines - 1, len(lines)),
            "inventory": "pending",
            "note": "",
        }
        for i, start in enumerate(starts)
    ]
    return {
        "version": 2 if derivations else 1,
        "startedAt": (now or datetime.now(UTC)).isoformat(),
        "budgetSeconds": minutes * 60,
        "scope": {"path": name, "sha256": digest, "startLine": 1, "endLine": len(lines)},
        "units": units,
        "claims": [],
    }


def assess(plan, root: Path, *, now=None):
    plan = _object(plan, "plan")
    if plan.get("version") == 3:
        from ladon.investigation_correspondence import assess_v3

        return assess_v3(plan, root, now=now)
    _require(
        type(plan.get("version")) is int and plan["version"] in (1, 2), "unsupported plan version"
    )
    elapsed, budget = _elapsed_budget(plan, now)
    reader = SourceReader(root)
    scope = _object(plan.get("scope"), "scope")
    reader.span(scope)
    units, by_id, pending = _assessed_units(plan, scope)
    claims, ordered = _assessed_claims(plan, reader, scope, by_id)
    blocked, reviewed = _claim_queue(ordered, pending)
    pending, reviewed, findings = _derivation_priority(plan, reader, pending, reviewed, claims)
    status = _work_status(elapsed, budget, pending, blocked)
    result = {
        "schema": f"ladon-investigation-status-v{plan['version']}",
        "status": status,
        "mayFinalize": status != "continue",
        "elapsedSeconds": elapsed,
        "remainingSeconds": max(0, budget - elapsed),
        "next": pending,
        "blocked": blocked,
        "counts": {
            "units": len(units),
            "pendingUnits": sum(u["inventory"] == "pending" for u in units),
            "claims": len(claims),
            "reviewedClaims": reviewed,
            "actionable": len(pending),
            "blockedClaims": len(blocked),
        },
        "authority": "source binding and authored workflow bookkeeping only",
        "nonclaims": [
            "No mathematical truth or semantic inventory completeness is certified.",
            "No Lean, network, model service or automatic semantic comparison was run.",
            "Inventory, interpretations, judgments, blockers and start time are authored.",
        ],
    }

    if plan["version"] == 2:
        result["authority"] = "source binding, authored reviews and exact scalar witness replay"
        result["findings"] = findings
        result["nonclaims"].append(
            "Rational witnesses check authored scalar interpretations only; "
            "reviewer labels do not establish independent identities."
        )
    return result


def _elapsed_budget(plan, now):
    budget = _integer(plan.get("budgetSeconds"), "budgetSeconds", maximum=604800)
    started = datetime.fromisoformat(_text(plan.get("startedAt"), "startedAt"))
    _require(
        started.tzinfo is not None and started.utcoffset().total_seconds() == 0,
        "startedAt must be UTC with a timezone",
    )
    current = now or datetime.now(UTC)
    _require(current.tzinfo is not None, "current time must have timezone")
    elapsed = (current - started).total_seconds()
    _require(elapsed >= 0, "startedAt is in the future")
    return elapsed, budget


def _assessed_units(plan, scope):
    units = _array(plan.get("units"), "units")
    _require(bool(units), "source scope needs units")
    for unit in units:
        _object(unit, "unit")
        _integer(unit.get("startLine"), "unit.startLine")
        _integer(unit.get("endLine"), "unit.endLine", unit["startLine"], scope["endLine"])
    units = sorted(units, key=lambda u: u["startLine"])
    by_id = {}
    cursor = scope["startLine"]
    pending = []
    for unit in units:
        uid = _text(unit.get("id"), "unit id")
        _require(uid not in by_id, "duplicate unit id")
        _require(unit["startLine"] == cursor, "unit partition has a gap or overlap")
        cursor = unit["endLine"] + 1
        _require(unit.get("inventory") in ("pending", "done"), "invalid inventory state")
        if unit["inventory"] == "done":
            _text(unit.get("note"), "attributed inventory note")
        else:
            pending.append(
                {
                    "kind": "inventory-source",
                    "unit": uid,
                    "startLine": unit["startLine"],
                    "endLine": unit["endLine"],
                }
            )
        by_id[uid] = unit
    _require(cursor == scope["endLine"] + 1, "unit partition omits source scope")
    return units, by_id, pending


def _assessed_claims(plan, reader, scope, by_id):
    claims = _array(plan.get("claims"), "claims")
    seen = set()
    ordered = []
    for claim in claims:
        _object(claim, "claim")
        cid = _text(claim.get("id"), "claim id")
        _require(cid not in seen, "duplicate claim id")
        seen.add(cid)
        _require(
            isinstance(claim.get("unit"), str) and claim["unit"] in by_id, "claim has unknown unit"
        )
        unit = by_id[claim["unit"]]
        start = _integer(claim.get("startLine"), "claim.startLine", unit["startLine"])
        _integer(claim.get("endLine"), "claim.endLine", start, unit["endLine"])
        reader.span(
            {
                **scope,
                **{k: claim[k] for k in ("startLine", "endLine")},
                "quote": claim.get("quote"),
            },
            "quote",
        )
        state = claim.get("state")
        _require(state in ("captured", "contract", "reviewed", "blocked"), "invalid claim state")
        if state in ("contract", "reviewed"):
            _contract(claim.get("contract"))
        if state == "reviewed":
            formal = _object(claim.get("formal"), "formal source")
            reader.span(formal, "statement")
            _contract(formal.get("contract"))
            judgment = _object(claim.get("judgment"), "judgment")
            _require(
                judgment.get("statement") in ("aligned", "mismatch", "unresolved"),
                "invalid statement judgment",
            )
            _require(
                judgment.get("method") in ("same", "different", "unresolved"),
                "invalid method judgment",
            )
            _text(judgment.get("evidence"), "judgment evidence")
        if state == "blocked":
            _blocker(claim.get("blocker"))
        ordered.append(claim)
    return claims, ordered


def _claim_queue(ordered, pending):
    blocked = []
    reviewed = 0
    for claim in sorted(ordered, key=lambda c: (c["startLine"], c["id"])):
        state = claim["state"]
        if state == "blocked":
            blocked.append({"claim": claim["id"], "blocker": claim["blocker"]})
            continue
        if state == "captured":
            kind = "write-exact-contract"
        elif state == "contract":
            kind = "compare-formal-contract"
        elif "unresolved" in (claim["judgment"]["statement"], claim["judgment"]["method"]):
            kind = "resolve-local-obligation"
        else:
            reviewed += 1
            continue
        pending.append(
            {
                "kind": kind,
                "claim": claim["id"],
                "unit": claim["unit"],
                "startLine": claim["startLine"],
                "endLine": claim["endLine"],
                "sourceAssertion": claim["quote"],
            }
        )
    return blocked, reviewed


def _derivation_priority(plan, reader, pending, reviewed, claims):
    findings = []
    if plan["version"] == 2:
        from ladon.investigation_derivation import derivation_work

        priority, findings, suspicious, open_claims = derivation_work(plan, reader)
        # One concrete step queue replaces a vague parent follow-up until resolved.
        remaining = [item for item in pending if item.get("claim") not in open_claims]
        concerned = [item for item in remaining if item.get("claim") in suspicious]
        ordinary = [item for item in remaining if item.get("claim") not in suspicious]
        pending = priority + concerned + ordinary
        reviewed -= sum(_completed_open_claim(c, open_claims) for c in claims)
    return pending, reviewed, findings


def _work_status(elapsed, budget, pending, blocked):
    if elapsed >= budget and (pending or blocked):
        status = "incomplete-budget"
    elif pending:
        status = "continue"
    elif blocked:
        status = "incomplete-blocked"
    else:
        status = "recorded-work-complete"
    return status


def step_subject(plan, claim, step):
    from ladon.investigation_derivation import step_subject as subject

    return subject(plan, claim, step)


def _completed_open_claim(claim, open_claims):
    return (
        claim["id"] in open_claims
        and claim["state"] == "reviewed"
        and "unresolved" not in (claim["judgment"]["statement"], claim["judgment"]["method"])
    )
