"""Validate immutable native subjects without granting fresh checker authority."""

import copy
from pathlib import Path

from ladon.correspondence_archive import historical_formal_subject, interpretation_profile
from ladon.correspondence_check import prepare_correspondence
from ladon.correspondence_interpretation import (
    LEGACY_PROFILE,
    UnsupportedInterpretation,
    closed,
    lower_formula,
    validate_interpretation,
)
from ladon.proofir_correspondence import bind_native_interpretation, correspondence_artifacts
from ladon.proofir_correspondence_payloads import validate_native_interpretation_batch
from ladon.proofir_v3 import validate_envelope_batch
from ladon.scoped_slice import profile_is_scoped

CHECKED_KEYS = {"schema", "planId", "conditionalValidity", "premiseEstablishment",
                "parentSupport", "interpretationFidelity", "methodCorrespondence",
                "extractionCompleteness", "checkerAuthority", "checks", "residuals",
                "checkRunRefs", "artifacts", "plan"}


def _source_in_scope(record, root, scope):
    record = validate_interpretation(record, Path(root))
    source = record["source"]
    if (source["path"] != scope["path"] or source["sha256"] != scope["sha256"]
            or not scope["startLine"] <= source["startLine"] <= source["endLine"] <= scope["endLine"]):
        raise ValueError("correspondence source is outside investigation scope")
    return record


def _interpretation_subject(bundle, root, scope):
    closed(bundle, {"schema", "record", "loweredFormula", "fidelity", "residuals", "artifacts"},
           "interpretation bundle")
    record = _source_in_scope(bundle["record"], root, scope)
    try:
        lowered, residuals = lower_formula(record["formula"], record["symbols"],
                                         _profile=interpretation_profile(bundle)), []
    except UnsupportedInterpretation as error:
        lowered, residuals = None, [str(error)]
    if (bundle["loweredFormula"] != lowered or bundle["residuals"] != residuals
            or bundle["fidelity"] != "attributed-unreviewed"):
        raise ValueError("altered interpretation projection")
    artifacts = bundle["artifacts"]
    ref = validate_native_interpretation_batch(record, artifacts, artifacts[0]["environmentRef"],
                                               source_root=Path(root))
    return "no-counterpart", ref["artifactRef"]


def _closed_formal_bundle(bundle, checked):
    if checked:
        keys = CHECKED_KEYS | ({"providerValidity"} if profile_is_scoped(bundle["plan"]["slice"])
                               else set())
        if "compiledImportIdentityReuses" in bundle:
            keys.add("compiledImportIdentityReuses")
        if "preparationMode" in bundle:
            keys.add("preparationMode")
        if "executionAccounting" in bundle:
            keys.add("executionAccounting")
        if "implementationDigest" in bundle:
            keys.add("implementationDigest")
        closed(bundle, keys, "checked correspondence bundle")
    else:
        closed(bundle, {"schema", "plan", "artifacts"}, "prepared correspondence bundle")


def _validate_row_goals(bundle):
    if "plan" not in bundle:
        return
    obligations = {row["id"]: row["goal"] for row in bundle["plan"]["obligations"]}
    seen = set()
    for row in bundle["checks"]:
        identity = row["obligation"]
        if (identity in seen or identity not in obligations
                or row["goal"] != obligations[identity] or row["mode"] not in {"prove", "refute"}):
            raise ValueError("check goal does not bind its exact planned obligation")
        seen.add(identity)


def validate_check_receipt_bindings(bundle):
    """Bind archived row evidence; this does not perform a fresh Lean replay."""
    from ladon.correspondence_evidence import _hash

    _validate_row_goals(bundle)
    rows, refs = bundle["checks"], bundle["checkRunRefs"]
    if len(rows) != len(refs):
        raise ValueError("check receipt count changed")
    by_id = {artifact["artifactId"]: artifact for artifact in bundle["artifacts"]}
    seen = set()
    for row, ref in zip(rows, refs, strict=True):
        artifact = by_id.get(ref["artifactRef"], {})
        evidence = artifact.get("extensions", {}).get("ladon.correspondence-receipt/v1", {})
        expected = {"planId": bundle["planId"], "obligation": row["obligation"],
                    "mode": row["mode"], "goalDigest": _hash(row["goal"]),
                    "receiptDigest": _hash(row)}
        if (artifact.get("artifactKind") != "proofir.check-run"
                or ref["kind"] != "check-run"
                or artifact.get("payload", {}).get("checkRunId") != ref["localId"]
                or ref["artifactRef"] in seen
                or any(evidence.get(key) != value for key, value in expected.items())):
            raise ValueError("check receipt does not bind its exact elaborated subject and row")
        seen.add(ref["artifactRef"])


def _formal_subject(bundle, root, scope):
    checked = bundle["schema"] == "ladon-correspondence-check-v1"
    _closed_formal_bundle(bundle, checked)
    plan = bundle["plan"]
    _source_in_scope(plan["interpretation"], root, scope)
    if plan["schema"] == "ladon-correspondence-plan-v1":
        if checked:
            validate_check_receipt_bindings(bundle)
        return historical_formal_subject(bundle, Path(root), checked)
    prepared = prepare_correspondence(plan["interpretation"], plan["slice"], plan["objectMap"])
    rebuilt = bind_native_interpretation(prepared, bundle["artifacts"], source_root=Path(root))
    if plan != rebuilt or (checked and bundle["planId"] != plan["planId"]):
        raise ValueError("prepared correspondence changed")
    if checked:
        validate_check_receipt_bindings(bundle)
    _validate_native_projection(bundle, plan, checked)
    return "formal-correspondence", plan["planId"]


def _validate_native_projection(bundle, plan, checked):
    expected = correspondence_artifacts(plan, bundle if checked else None)
    correspondences = [row for row in bundle["artifacts"]
                       if row["artifactKind"] == "proofir.correspondence"]
    if not correspondences or correspondences[-1] != expected:
        raise ValueError("native correspondence does not match its immutable bundle")


def validate_bundle(bundle, root, scope):
    if not isinstance(bundle, dict) or bundle.get("schema") not in {
        "ladon-interpretation-v1", "ladon-correspondence-bundle-v1", "ladon-correspondence-check-v1",
    }:
        raise ValueError("unsupported structured bundle")
    artifacts = bundle.get("artifacts")
    if not isinstance(artifacts, (list, tuple)) or not artifacts:
        raise ValueError("structured bundle requires native artifacts")
    bundle = copy.deepcopy(bundle)
    bundle["artifacts"] = list(artifacts)
    artifacts = bundle["artifacts"]
    validate_envelope_batch(artifacts)
    kind, subject = (_interpretation_subject(bundle, root, scope)
                     if bundle["schema"] == "ladon-interpretation-v1"
                     else _formal_subject(bundle, root, scope))
    return {"kind": kind, "subject": subject, "bundle": copy.deepcopy(bundle)}


def sanitized_inputs(entry):
    bundle = entry["bundle"]
    if entry["kind"] == "no-counterpart":
        return {"interpretation": bundle["record"], "objectMap": {},
                "observedContext": {"kind": "no-counterpart"},
                "originalGoals": [], "originalResiduals": bundle["residuals"]}
    plan, slice_ = bundle["plan"], bundle["plan"]["slice"]
    selected = slice_["observation"]["applications"][slice_["selection"]["occurrence"]]
    context = {"kind": "formal-correspondence", "sliceId": slice_["sliceId"],
               "source": slice_["source"], "environment": slice_["environment"],
               "helper": slice_["helper"], "selection": slice_["selection"],
               "localContext": slice_["localContext"], "application": selected["application"],
               "applicationType": selected["applicationType"], "arguments": selected["arguments"],
               "closedConditional": selected["closedApplicationTypeText"]}
    typed = [copy.deepcopy(row["typedSubject"]) for row in bundle.get("checks", [])
             if row.get("obligation") == "interpretation" and "typedSubject" in row]
    if interpretation_profile(bundle) != LEGACY_PROFILE:
        context["elaboratedInterpretations"] = typed
        context["interpretationCheckScope"] = "typing-only; P implies P establishes neither P nor source fidelity"
    if profile_is_scoped(slice_):
        context.update(scopePath=selected["scopePath"], nestedLocalIds=selected["nestedLocalIds"])
    return {"interpretation": plan["interpretation"], "objectMap": plan["objectMap"],
            "observedContext": context,
            "originalGoals": [{key: row[key] for key in ("id", "kind", "goal")}
                              for row in plan["obligations"]],
            "originalResiduals": plan["residuals"]}
