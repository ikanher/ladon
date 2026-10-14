"""Keep mathematical review, recorded formal links and source coverage separate."""

import copy
from pathlib import Path

from ladon.correspondence_archive import interpretation_profile
from ladon.correspondence_interpretation import LEGACY_PROFILE
from ladon.investigation import assess
from ladon.investigation_work_blockers import separate_blocked_work


def _reviews_resolved(reviews):
    return bool(reviews) and all(
        response["classification"] != "unresolved" and response["sourceFidelity"] == "faithful"
        and response["method"] != "unresolved" for response in reviews
    )


def _method_review(reviews):
    methods = {response["method"] for response in reviews}
    if len(methods) == 1 and "unresolved" not in methods:
        return next(iter(methods)) + "-attributed"
    return "unresolved-attributed"


def _review_summary(subject, responses):
    reviews = [response for response in responses if response["subject"] == subject]
    resolved = _reviews_resolved(reviews) and len(
        {response["classification"] for response in reviews}
    ) <= 1
    return {"mathematicalReview": "complete-attributed" if resolved else "incomplete-review",
            "interpretationFidelity": "faithful-attributed" if resolved else "unresolved-attributed",
            "methodReview": _method_review(reviews)}


def _obligation_work(subject, obligation):
    if obligation["status"] == "supported":
        return None
    kind = ("refuted-correspondence-link" if obligation["status"] == "refuted"
            else "check-correspondence-link")
    return {"kind": kind, "subject": subject, "obligation": copy.deepcopy(obligation)}


def _formal_work(entry):
    subject = entry["subject"]
    if interpretation_profile(entry["bundle"]) == LEGACY_PROFILE:
        return "incomplete-semantic-migration", [{"kind": "refresh-semantic-profile",
                                                   "subject": subject,
                                                   "reason": "historical untyped evidence requires fresh typed checks and reviews"}]
    if entry["kind"] == "no-counterpart":
        return "incomplete-no-counterpart", [{"kind": "missing-formal-counterpart", "subject": subject}]
    return _recorded_link_work(entry)


def _recorded_link_work(entry):
    subject = entry["subject"]
    bundle = entry["bundle"]
    artifact = [row for row in bundle["artifacts"] if row["artifactKind"] == "proofir.correspondence"][-1]
    payload = artifact["payload"]
    queue = [{"kind": "correspondence-residual", "subject": subject, "residual": row}
             for row in payload["residuals"]]
    queue.extend(work for obligation in payload["obligations"]
                 if (work := _obligation_work(subject, obligation)) is not None)
    if not queue and payload["dimensions"]["parentSupport"] == "supported-for-attributed-interpretation":
        return "recorded-links-complete-unreplayed", []
    if not queue:
        queue.append({"kind": "qualify-recorded-checks", "subject": subject})
    return "incomplete-formal-links", queue


def _bundle_status(entry, responses):
    review = _review_summary(entry["subject"], responses)
    formal, work = _formal_work(entry)
    row = {"subject": entry["subject"], "kind": entry["kind"],
           "formalCorrespondence": formal, **review}
    if review["mathematicalReview"] != "complete-attributed":
        work.append({"kind": "independent-step-review", "subject": entry["subject"]})
    elif review["methodReview"] == "unresolved-attributed":
        work.append({"kind": "reconcile-method-review", "subject": entry["subject"]})
    return row, work


def _formal_summary(entries, bundles):
    if bool(entries) and all(
        row["formalCorrespondence"] == "recorded-links-complete-unreplayed" for row in bundles
    ):
        return "recorded-links-complete-unreplayed"
    if not entries or any(row["kind"] == "no-counterpart" for row in entries):
        return "incomplete-no-counterpart"
    return "incomplete-formal-links"


def _final_status(result, entries, bundles, queue):
    inventory_complete = result["counts"]["pendingUnits"] == 0 and not result["next"]
    math_complete = bool(entries) and inventory_complete and not result["blocked"] and all(
        row["mathematicalReview"] == "complete-attributed" for row in bundles
    )
    formal_complete = _formal_summary(entries, bundles) == "recorded-links-complete-unreplayed"
    formal = _formal_summary(entries, bundles)
    finalized = math_complete and formal_complete and not queue
    status = _workflow_status(result, queue, finalized)
    return math_complete, formal, finalized, status


def assess_structured(plan, root, entries, responses, *, now=None):
    base = {key: copy.deepcopy(plan[key]) for key in
            ("version", "startedAt", "budgetSeconds", "scope", "units", "claims")}
    base["version"] = 1
    result = assess(base, Path(root), now=now)
    bundles, priority = [], []
    for entry in entries:
        bundle, work = _bundle_status(entry, responses)
        bundles.append(bundle)
        priority.extend(work)
    if not entries:
        priority.append({"kind": "author-structured-interpretation", "reason": "no counterpart recorded"})
    queue, blocked = separate_blocked_work(plan, priority + result["next"])
    result["blocked"] = result["blocked"] + blocked
    math_complete, formal_status, _finalized, status = _final_status(result, entries, bundles, queue)
    result.update(schema="ladon-investigation-status-v3", bundles=bundles,
                  mathematicalReview="complete-attributed" if math_complete else "incomplete-review",
                  formalCorrespondence=formal_status,
                  mayFinalize=status != "continue", next=queue)
    result["status"] = status
    result["counts"].update(structuredSubjects=len(entries), firstResponses=len(plan["responses"]),
                            reconciliations=len(plan["reconciliations"]), actionable=len(queue))
    result["authority"] = "source binding, attributed reviews and stored native evidence only"
    result["nonclaims"] = ["No Lean check was replayed by status or response ingestion.",
                           "Stored formal labels and reviewer labels do not verify truth or identity.",
                           "Review completion covers the authored inventory and subjects only."]
    return result


def _workflow_status(result, queue, finalized):
    if finalized:
        return "recorded-work-complete"
    if result["remainingSeconds"] == 0:
        return "incomplete-budget"
    if result["blocked"] and not queue:
        return "incomplete-blocked"
    return "continue"
