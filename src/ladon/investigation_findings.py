"""Attributed investigation findings and bounded source coverage summaries."""

from __future__ import annotations

import copy

from ladon.proof_slice import digest


def _legacy_row(claim, scope):
    judgment = claim["judgment"]
    source = {key: copy.deepcopy(scope[key]) for key in ("path", "sha256")}
    source.update({key: copy.deepcopy(claim[key]) for key in
                   ("startLine", "endLine", "quote")})
    identity = {"claim": claim["id"], "source": source, "judgment": judgment}
    return {
        "kind": "legacy-claim-review",
        "findingId": digest(identity),
        "claim": claim["id"],
        "source": source,
        "statementRelation": judgment["statement"],
        "methodRelation": judgment["method"],
        "sourceFidelity": "attributed-unreviewed",
        "formalSupport": "recorded-reference-only" if claim.get("formal") else "not-recorded",
        "mathematicalFalsity": "not-established",
        "evidence": judgment["evidence"],
        "dependencies": claim.get("contract", {}).get("dependencies", "Authored claim contract."),
        "attribution": "Authored legacy judgment; attribution does not establish truth.",
    }


def legacy_findings(plan, derivation_findings=None):
    """Project discrepant legacy judgments and preserve v2 derivation checks."""
    rows = []
    for claim in plan.get("claims", []):
        if claim.get("state") != "reviewed":
            continue
        judgment = claim.get("judgment")
        if not judgment or not ({judgment.get("statement"), judgment.get("method")}
                                & {"mismatch", "different", "unresolved"}):
            continue
        rows.append(_legacy_row(claim, plan["scope"]))
    if plan.get("version") == 2:
        rows.extend(copy.deepcopy(derivation_findings or []))
    return rows


def _source_from_entry(entry):
    bundle = entry["bundle"]
    if "plan" in bundle and "interpretation" in bundle["plan"]:
        return copy.deepcopy(bundle["plan"]["interpretation"]["source"])
    if "interpretation" in bundle:
        return copy.deepcopy(bundle["interpretation"]["source"])
    if "record" in bundle and "source" in bundle["record"]:
        return copy.deepcopy(bundle["record"]["source"])
    for artifact in bundle.get("artifacts", []):
        payload = artifact.get("payload", {})
        record = payload.get("record", payload.get("interpretation", {}))
        if isinstance(record, dict) and isinstance(record.get("source"), dict):
            return copy.deepcopy(record["source"])
    return {}


def _review_label(rows, key):
    labels = {row.get(key) for row in rows}
    if len(labels) > 1:
        return "conflicted"
    return next(iter(labels)) if labels else "unresolved"


def _subject_rows(rows, subject):
    return [copy.deepcopy(row) for row in rows if row.get("subject") == subject]


def _requires_finding(statement, method, fidelity):
    return statement in {"mismatch", "unresolved", "conflicted"} or method in {
        "different", "unresolved", "conflicted"} or fidelity != "faithful"


def _native_finding(plan, entry, responses, include_aligned):
    subject = entry["subject"]
    firsts = _subject_rows(plan.get("responses", []), subject)
    history = _subject_rows(plan.get("reconciliations", []), subject)
    effective = _subject_rows(responses, subject)
    if not effective:
        return None
    statement = _review_label(effective, "classification")
    method = _review_label(effective, "method")
    fidelity = _review_label(effective, "sourceFidelity")
    had_difference = any(_requires_finding(row["classification"], row["method"], row["sourceFidelity"])
                         for row in firsts)
    if not (include_aligned or had_difference or _requires_finding(statement, method, fidelity)):
        return None
    source = _source_from_entry(entry)
    identity = {"subject": subject, "source": source}
    return {
        "kind": "native-correspondence-review", "findingId": digest(identity),
        "subject": subject, "source": source, "statementRelation": statement,
        "methodRelation": method,
        "sourceFidelity": "conflicted" if fidelity == "conflicted" else fidelity,
        "formalSupport": "not-established" if entry["kind"] == "no-counterpart" else "recorded-links-only",
        "mathematicalFalsity": "not-established",
        "evidence": [row.get("evidence", "") for row in effective],
        "dependencies": entry["bundle"].get("dependencies", "Authored correspondence dependencies."),
        "attribution": "Attributed native review; labels do not establish truth.",
        "responses": firsts, "history": history, "effectiveResponses": effective,
    }


def native_findings(plan, entries, responses, *, include_aligned=False):
    """Project discrepant native reviews with firsts and correction history."""
    return [finding for entry in entries
            if (finding := _native_finding(plan, entry, responses, include_aligned)) is not None]


def coverage_summary(plan):
    """Summarize authored inventory coverage without claiming whole-paper review."""
    units = plan.get("units", [])
    claims = plan.get("claims", [])
    return {
        "totalUnits": len(units),
        "surveyedUnits": sum(unit.get("inventory") == "done" for unit in units),
        "totalClaims": len(claims),
        "reviewedClaims": sum(claim.get("state") == "reviewed" for claim in claims),
        "wholePaperCertified": False,
        "authority": "Authored inventory and review records only.",
    }
