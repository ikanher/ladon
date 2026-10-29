"""Closed Real records using scoped expression fingerprints and typed ownership."""

import hashlib
from copy import deepcopy

from ladon.proof_contract_payloads import closed, identifier, rows
from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_binding import _alpha_expression
from ladon.real_bound_native_profile import PROFILE_ID

SCHEMA = "ladon-real-bound-record-v1"
APPLICATION_KEYS = {"functionRef", "setRef", "orderRef", "boundRef"}


def expression_subject(expression):
    digest = snapshot_identity({"expression": _alpha_expression(expression)})
    return {"kind": "expression", "localId": "expr:" + digest[7:], "fingerprint": {
        "scheme": {"name": "ladon-scoped-bound-expression", "version": "1"}, "digest": digest}}


def local_ref(subject):
    return {key: subject[key] for key in ("kind", "localId")}


def build_record(plan, evidence, check_refs):
    observation = plan["bindingPlan"]["observation"]
    candidate = observation["candidate"]
    subjects = {}

    def expr(value):
        subject = expression_subject(value)
        subjects[subject["localId"]] = subject
        return local_ref(subject)

    telescope = [{**{key: value for key, value in row.items() if key != "type"},
                  "typeRef": expr(row["type"])} for row in candidate["telescope"]]
    application = {"predicateRef": expr(candidate["input"]["predicate"]),
                   "operatorRef": expr(candidate["operator"])}
    for side in ("input", "output"):
        application[side] = {key + "Ref": expr(candidate[side][key])
                             for key in ("function", "set", "order", "bound")}
    endpoint = snapshot_identity({"predicate": application["predicateRef"],
                                  "operator": application["operatorRef"]})
    snapshot = observation["statementSnapshot"]
    binding = plan["bindingPlan"]
    interpretation = ({"kind": "joint-real-frechet-prefix-v1"}
                      if "derivativeProfile" in binding else
                      {"kind": "prefix-family-v1", "measure": deepcopy(binding["measure"])})
    record = {
        "schema": SCHEMA, "profileId": PROFILE_ID,
        "endpointId": endpoint, "conclusionId": "conclusion:" + plan["planId"][7:],
        "source": {"observationId": observation["snapshotId"],
                   "statementSnapshotId": snapshot["snapshotId"],
                   **deepcopy(snapshot["source"]), **deepcopy(snapshot["selection"])},
        "telescope": telescope, "roles": deepcopy(candidate["roles"]),
        "application": application, "constant": deepcopy(candidate["constant"]),
        "loss": candidate["loss"],
        "guards": {"constantNonnegativeRef": expr(candidate["guards"]["constantNonnegative"]["expression"]),
                   "boundNonnegativeBinderId": candidate["guards"]["boundNonnegative"]},
        "origins": {"input": candidate["input"]["originPath"],
                    "output": candidate["output"]["originPath"],
                    "constantGuard": candidate["guards"]["constantNonnegative"]["originPath"]},
        "interpretation": interpretation,
        "admission": {"state": "recorded-checked", "scope": "predicate-and-canonical-scalars",
                      "planId": plan["planId"], "checkerIdentity": evidence["checkerIdentity"],
                      "evidenceDigest": snapshot_identity(evidence),
                      "predicateCheckRef": check_refs[0], "scalarCheckRef": check_refs[1],
                      "goalDigests": [goal_digest(check) for check in evidence["checks"]]},
    }
    return record, list(subjects.values())


def goal_digest(check):
    structural = check["evidence"]["typedSubject"]["subject"]["structural"]
    return "sha256:" + hashlib.sha256(structural.encode()).hexdigest()


def validate_record(record):
    closed(record, {"schema", "profileId", "endpointId", "conclusionId", "source", "telescope",
                    "roles", "application", "constant", "loss", "guards", "origins",
                    "interpretation", "admission"}, "Real record")
    if record["schema"] != SCHEMA or record["profileId"] != PROFILE_ID:
        raise ValueError("unsupported Real record schema/profile")
    if type(record["loss"]) is not int or not 0 <= record["loss"] <= 2**53 - 1:
        raise ValueError("Real loss must be a bounded nonnegative integer")
    for key in ("endpointId", "conclusionId"):
        identifier(record[key], key)
    closed(record["source"], {"observationId", "statementSnapshotId", "path", "sha256", "module",
                              "declaration"}, "Real source")
    for key, value in record["source"].items():
        identifier(value, key)
    _scope(record)
    _applications(record)
    _interpretation(record["interpretation"], record["telescope"])
    _admission(record["admission"])
    return record


def _scope(record):
    rows(record["telescope"], "Real telescope", minimum=1)
    binders, universals = [], []
    allowed = None
    for index, row in enumerate(record["telescope"]):
        closed(row, {"binderId", "quantifier", "binderInfo", "typeRef", "originPath"}, "Real binder")
        if row["binderId"] != f"b{index}" or row["quantifier"] not in {"forall", "exists"}:
            raise ValueError("Real telescope must retain ordered quantified binders")
        if row["binderInfo"] not in {"explicit", "implicit", "strict-implicit", "instance-implicit"}:
            raise ValueError("unsupported Real binder information")
        identifier(row["originPath"], "binder origin")
        _expression_ref(row["typeRef"])
        binders.append(row["binderId"])
        if row["quantifier"] == "exists":
            if allowed is not None:
                raise ValueError("Real record requires one existential constant")
            allowed = list(universals)
            anchor = row["binderId"]
        else:
            universals.append(row["binderId"])
    _roles_and_guards(record, binders, universals, allowed, anchor if allowed is not None else None)


def _roles_and_guards(record, binders, universals, allowed, anchor):
    closed(record["roles"], {"function", "set", "order", "bound", "constant"}, "Real roles")
    role_values = list(record["roles"].values())
    if len(set(role_values)) != 5 or not set(role_values) <= set(binders):
        raise ValueError("Real roles must retain distinct in-scope binders")
    closed(record["constant"], {"binderId", "permittedBinderIds"}, "Real constant")
    if (allowed is None or record["constant"] != {"binderId": anchor, "permittedBinderIds": allowed}
            or record["roles"]["constant"] != anchor):
        raise ValueError("Real constant permissions differ from its exact lexical scope")
    closed(record["guards"], {"constantNonnegativeRef", "boundNonnegativeBinderId"}, "Real guards")
    _expression_ref(record["guards"]["constantNonnegativeRef"])
    if record["guards"]["boundNonnegativeBinderId"] not in universals:
        raise ValueError("Real bound guard must reference an actual universal binder")


def _expression_ref(ref):
    closed(ref, {"kind", "localId"}, "Real expression reference")
    if ref["kind"] != "expression":
        raise ValueError("Real expression requires an expression subject")
    identifier(ref["localId"], "Real expression ID")


def _applications(record):
    app = record["application"]
    closed(app, {"predicateRef", "operatorRef", "input", "output"}, "Real application")
    for key in ("predicateRef", "operatorRef"):
        _expression_ref(app[key])
    for side in ("input", "output"):
        closed(app[side], APPLICATION_KEYS, "Real application arguments")
        for ref in app[side].values():
            _expression_ref(ref)
    expected = snapshot_identity({"predicate": app["predicateRef"], "operator": app["operatorRef"]})
    if record["endpointId"] != expected or app["input"]["setRef"] != app["output"]["setRef"]:
        raise ValueError("Real endpoint or application set differs")
    closed(record["origins"], {"input", "output", "constantGuard"}, "Real origins")
    for origin in record["origins"].values():
        identifier(origin, "Real expression origin")


def _interpretation(value, telescope):
    if value == {"kind": "joint-real-frechet-prefix-v1"}:
        return
    closed(value, {"kind", "measure"}, "Real interpretation")
    if value["kind"] != "prefix-family-v1":
        raise ValueError("unsupported Real interpretation")
    closed(value["measure"], {"declaration", "arguments"}, "Real measure")
    identifier(value["measure"]["declaration"], "measure declaration")
    rows(value["measure"]["arguments"], "measure arguments")
    if not set(value["measure"]["arguments"]) <= {r["binderId"] for r in telescope}:
        raise ValueError("measure arguments escape the Real telescope")


def _admission(value):
    closed(value, {"state", "scope", "planId", "checkerIdentity", "evidenceDigest",
                   "predicateCheckRef", "scalarCheckRef", "goalDigests"}, "Real recorded admission")
    if value["state"] != "recorded-checked" or value["scope"] != "predicate-and-canonical-scalars":
        raise ValueError("saved Real admission must remain historical")
    from ladon.proofir_v3 import _digest

    if (not isinstance(value["goalDigests"], list) or len(value["goalDigests"]) != 2
            or not all(_digest(digest) for digest in value["goalDigests"])):
        raise ValueError("Real admission requires both exact typed goal fingerprints")
    for key in ("planId", "checkerIdentity", "evidenceDigest"):
        identifier(value[key], key)
    _check_refs(value)


def _check_refs(value):
    for key in ("predicateCheckRef", "scalarCheckRef"):
        ref = value[key]
        closed(ref, {"artifactRef", "kind", "localId"}, "Real check reference")
        if ref["kind"] != "check-run":
            raise ValueError("Real admission requires typed check references")
    if value["predicateCheckRef"] == value["scalarCheckRef"]:
        raise ValueError("predicate and scalar checks require distinct exact owners")
