"""Native Real dispatch and exact evidence-owner validation."""

from ladon.proof_contract_payloads import _refs, closed, identifier, residuals
from ladon.proofir_v3 import _require_ref
from ladon.real_bound_native_profile import PROFILE_DIGEST
from ladon.real_bound_native_record import validate_record

LIMITATIONS = {
    "source-theorem-proof-not-checked": "Admission checks predicate interpretation and scalar semantics; the source theorem proof is not certified.",
    "real-admission-history-unverified": "Saved receipts are historical; semantic reuse requires fresh checking.",
    "source-contract-binding-unchecked": "Source fidelity and the paper-norm bridge remain separate obligations.",
}


def validate_payload(p, value, subjects, env):
    closed(p, {"contractId", "profileDigest", "record", "statementRef", "assumptionRefs",
               "conclusionRef", "sourceMapRefs", "checkRunRefs", "provenance", "residuals"},
           "Real native payload")
    if p["profileDigest"] != PROFILE_DIGEST:
        raise ValueError("Real profile digest mismatch")
    identifier(p["contractId"], "Real contract ID")
    if ("contract", p["contractId"]) not in subjects:
        raise ValueError("Real contract must own its typed subject")
    record = validate_record(p["record"])
    for key in ("statementRef", "conclusionRef"):
        _require_ref(p[key], "/payload/" + key, subjects, env, value, "statement")
    if p["conclusionRef"] != {"kind": "statement", "localId": record["conclusionId"]}:
        raise ValueError("Real conclusion must be owned by the exact contract")
    if p["assumptionRefs"] != []:
        raise ValueError("Real premises are retained in the full typed telescope")
    _refs(p, "sourceMapRefs", "source-map", value, subjects, env, minimum=1)
    _refs(p, "checkRunRefs", "check-run", value, subjects, env, minimum=2)
    _evidence_refs(p)
    _expressions(record, value, subjects, env)
    required = {"mode": "extracted", "fidelity": "attributed-unreviewed", "completeness": "partial",
                "checkerAuthority": "none", "mathematicalFalsity": "not-established"}
    if p["provenance"] != required:
        raise ValueError("Real saved provenance cannot promote authority")
    residuals(p["residuals"])
    if not set(LIMITATIONS) <= {row["id"] for row in value["limitations"]}:
        raise ValueError("Real historical evidence requires explicit authority limitations")


def _evidence_refs(p):
    admission = p["record"]["admission"]
    expected = [admission["predicateCheckRef"], admission["scalarCheckRef"]]
    if p["checkRunRefs"] != expected or len(p["sourceMapRefs"]) != 1:
        raise ValueError("Real evidence references differ from recorded obligations")
    if not all("artifactRef" in r for r in [p["statementRef"], *p["sourceMapRefs"], *expected]):
        raise ValueError("Real evidence must name external exact owners")


def _expressions(record, value, subjects, env):
    refs = [r["typeRef"] for r in record["telescope"]]
    refs += [record["guards"]["constantNonnegativeRef"]]
    app = record["application"]
    refs += [app["predicateRef"], app["operatorRef"], *app["input"].values(), *app["output"].values()]
    descriptors = {(r["kind"], r["localId"]): r for r in value["subjectRefs"]}
    for ref in refs:
        _require_ref(ref, "/payload/record", subjects, env, value, "expression")
        descriptor = descriptors[(ref["kind"], ref["localId"])]
        fingerprint = descriptor.get("fingerprint", {})
        if (fingerprint.get("scheme") != {"name": "ladon-scoped-bound-expression", "version": "1"}
                or ref["localId"] != "expr:" + fingerprint.get("digest", "")[7:]):
            raise ValueError("Real expression fingerprint differs from its typed subject")


def validate_owners(artifact, artifacts):
    """Resolve through the existing native batch owner index, never guessed IDs."""
    p = artifact["payload"]
    source = artifacts[p["sourceMapRefs"][0]["artifactRef"]]
    if (source["artifactKind"] != "proofir.source-map"
            or source["payload"]["sourceMapId"] != p["sourceMapRefs"][0]["localId"]):
        raise ValueError("Real source reference must name the exact source-map owner")
    _source_owner(p, source)
    for index, operation in enumerate(("predicate-admission", "scalar-semantics")):
        ref = p["checkRunRefs"][index]
        _check_owner(p, artifacts[ref["artifactRef"]], ref, operation, source, index)


def _source_owner(p, source):
    anchors = source["payload"]["anchors"]
    if len(anchors) != 1:
        raise ValueError("Real source requires its exact declaration anchor")
    anchor = anchors[0]
    own_statement = {key: p["statementRef"][key] for key in ("kind", "localId")}
    record_source = p["record"]["source"]
    if (anchor["subjectRef"] != own_statement or p["statementRef"]["artifactRef"] != source["artifactId"]
            or anchor["contentDigest"] != "sha256:" + record_source["sha256"]
            or anchor["sourcePath"] != record_source["path"]
            or anchor["module"] != record_source["module"]
            or anchor["declName"] != record_source["declaration"]):
        raise ValueError("Real source anchor differs from the recorded statement")


def _check_owner(p, owner, ref, operation, source, index):
    check = owner["payload"]
    if (owner["artifactKind"] != "proofir.check-run" or check["checkRunId"] != ref["localId"]
            or check["operation"] != "real-bound:" + operation
            or check["checker"]["implementationDigest"] != p["record"]["admission"]["checkerIdentity"]):
        raise ValueError("Real check reference has the wrong operation or checker owner")
    _goal_owner(p, owner, index)
    if (check["guarantee"]["authorityBasis"] != "stored-observation"
            or check["inputs"]["artifactRefs"] != [source["artifactId"]]
            or p["statementRef"] not in check["inputs"]["subjectRefs"]
            or len(check["results"]) != 1 or check["results"][0]["result"] != "accepted"):
        raise ValueError("Real check is missing its historical source-bound result")


def _goal_owner(p, owner, index):
    check = owner["payload"]
    digest = p["record"]["admission"]["goalDigests"][index]
    goal = {"kind": "statement", "localId": "goal:" + digest[7:]}
    descriptor = {**goal, "fingerprint": {"scheme": {"name": "lean-typed-goal", "version": "1"},
                                          "digest": digest}}
    if (descriptor not in owner["subjectRefs"] or check["results"] != [
            {"subjectRef": goal, "result": "accepted", "diagnostics": []}]
            or check["guarantee"]["scope"] != "declaration-value"):
        raise ValueError("Real check does not own the required exact typed goal result")
