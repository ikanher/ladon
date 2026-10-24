"""Fresh, immutable workflow receipts; attribution is not authenticated identity."""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from pathlib import Path

from ladon.correspondence_interpretation import closed, text
from ladon.investigation import assess
from ladon.proof_slice import digest

STOP_KEYS = {"schema", "actor", "at", "instructionRef", "reason", "planId", "scopeId"}


def _stop_record(record, plan, now):
    closed(record, STOP_KEYS, "user stop record")
    if record["schema"] != "ladon-investigation-user-stop-v1":
        raise ValueError("unsupported user stop record")
    for key in ("actor", "instructionRef", "reason"):
        text(record[key], key)
    at = datetime.fromisoformat(text(record["at"], "stop time"))
    started = datetime.fromisoformat(plan["startedAt"])
    if at.tzinfo is None or at.utcoffset().total_seconds() != 0 or not started <= at <= now:
        raise ValueError("stop time must be UTC within the current investigation")
    if record["planId"] != digest(plan) or record["scopeId"] != digest(plan["scope"]):
        raise ValueError("stop record is bound to a different plan or scope")
    return copy.deepcopy(record)


def _terminal_reason(status, stop):
    if stop is not None:
        return "user-stop"
    if status["remainingSeconds"] == 0:
        return "elapsed-budget"
    if status["status"] == "recorded-work-complete":
        return "recorded-completion"
    if status["blocked"] and not status["next"]:
        return "no-actionable-work-blocker"
    return None


def _has_contract_observations(plan, root):
    from ladon.investigation_observations import validated_observations

    return any(entry["record"].get("schema") == "ladon-investigation-observation-v2"
               for entry in validated_observations(plan, root))


def progress_receipt(plan, root: Path, *, finalize=False, stop_record=None, now=None):
    """Reassess exact source bytes and clock; never accept a prior receipt as authority."""
    current = now or datetime.now(UTC)
    status = assess(plan, root, now=current)
    stop = _stop_record(stop_record, plan, current) if stop_record is not None else None
    if stop is not None and not finalize:
        raise ValueError("a checkpoint cannot consume a stop instruction")
    reason = _terminal_reason(status, stop) if finalize else None
    if finalize and reason is None:
        # No output receipt: the caller must act on this queue or obtain a
        # genuine stop instruction, without resetting or exhausting the clock.
        status["mayFinalize"] = False
        return status, False
    has_contract = _has_contract_observations(plan, root)
    result = {**status, "schema": ("ladon-investigation-progress-v3" if has_contract
                                   else "ladon-investigation-progress-v2"),
              "operation": "finalize" if finalize else "checkpoint",
              "terminal": bool(finalize), "terminalReason": reason,
              "planId": digest(plan), "scopeId": digest(plan["scope"]),
              "startedAt": plan["startedAt"], "budgetSeconds": plan["budgetSeconds"],
              "recordedAt": current.isoformat(), "stopRecord": stop,
              "attribution": "Authored workflow evidence, not authenticated user identity."}
    _label_finalization(result, finalize, reason)
    result["receiptId"] = digest(result)
    return result, True


def validate_progress_receipt(receipt, plan, root: Path):
    """Validate binding and fresh source, preserving the original recorded clock."""
    _validate_receipt_binding(receipt, plan)
    now = datetime.fromisoformat(receipt["recordedAt"])
    rebuilt, saved = progress_receipt(plan, root, finalize=receipt["terminal"],
                                     stop_record=receipt["stopRecord"], now=now)
    if receipt["schema"] == "ladon-investigation-progress-v1":
        rebuilt = historical_status_projection(rebuilt, plan)
        rebuilt["schema"] = "ladon-investigation-progress-v1"
        rebuilt["receiptId"] = digest({key: value for key, value in rebuilt.items()
                                       if key != "receiptId"})
    if not saved or rebuilt != receipt:
        raise ValueError("progress receipt no longer matches exact source and plan")
    return copy.deepcopy(receipt)


def _validate_receipt_binding(receipt, plan):
    if not isinstance(receipt, dict) or receipt.get("schema") not in {
            "ladon-investigation-progress-v1", "ladon-investigation-progress-v2",
            "ladon-investigation-progress-v3"}:
        raise ValueError("unsupported progress receipt")
    if receipt.get("planId") != digest(plan) or receipt.get("scopeId") != digest(plan["scope"]):
        raise ValueError("stale progress receipt plan or scope")
    if receipt.get("receiptId") != digest({k: v for k, v in receipt.items() if k != "receiptId"}):
        raise ValueError("altered progress receipt")


def historical_status_projection(status, plan):
    """Strip additive findings fields to rebuild a frozen progress-v1 receipt."""
    result = copy.deepcopy(status)
    if plan.get("observations"):
        raise ValueError("legacy receipts cannot include new observation records")
    result.pop("coverage", None)
    for key in ("observations", "pendingObservations"):
        result.get("counts", {}).pop(key, None)
    if plan["version"] == 1:
        result.pop("findings", None)
    elif "findings" in result:
        result["findings"] = [row for row in result["findings"] if row.get("kind") not in {
            "legacy-claim-review", "native-correspondence-review", "observation"}]
        if not result["findings"] and plan["version"] != 2:
            result.pop("findings", None)
    for bundle in result.get("bundles", []):
        bundle.pop("statementReview", None)
    return result


def _label_finalization(result, finalize, reason):
    if finalize:
        result["mayFinalize"] = True
        if reason == "user-stop":
            result["status"] = "incomplete-user-stop"
