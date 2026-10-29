"""Fresh production, historical inspection, and explicit source-owned replay."""

from copy import deepcopy

from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_admission_check import _validate_terms
from ladon.real_bound_binding_check import verify_binding_source
from ladon.real_bound_native_artifacts import real_bound_artifacts
from ladon.real_bound_native_check import check_real_bound, native_checker_identity
from ladon.real_bound_native_history import validate_recorded_plan
from ladon.real_bound_native_plan import validate_real_plan

SCHEMA = "ladon-real-bound-production-v1"


def recorded_production(plan, terms, check, source_text):
    """Reconstruct saved observations with no claim to fresh execution authority."""
    validate_recorded_plan(plan)
    _validate_terms(plan, terms)
    if type(source_text) is not str:
        raise ValueError("recorded Real production requires exact source text")
    inner = check.get("result") or {}
    admitted = check.get("status") == "completed" and inner.get("status") == "checked"
    artifacts = real_bound_artifacts(plan, check, source_text.encode()) if admitted else []
    if admitted and terms != {r["goal"]["id"]: r["term"] for r in inner["checks"]}:
        raise ValueError("recorded proof terms differ from the checked terms")
    result = {"schema": SCHEMA, "status": "admitted" if admitted else "unresolved",
              "authority": "none", "request": {"plan": deepcopy(plan), "terms": deepcopy(terms)},
              "check": deepcopy(check), "sourceText": source_text, "artifacts": artifacts}
    result["snapshotId"] = snapshot_identity(result)
    return result


def produce_real_bound(root, plan, terms, *, timeout_seconds=600):
    validate_real_plan(plan)
    _validate_terms(plan, terms)
    _root, source, _context = verify_binding_source(root, plan["bindingPlan"])
    check = check_real_bound(root, plan, terms, timeout_seconds=timeout_seconds)
    result = recorded_production(plan, terms, check, source.decode("utf-8"))
    if result["status"] == "admitted":
        if check["result"]["checkerIdentity"] != native_checker_identity():
            raise ValueError("Real checker changed before native production")
        verify_binding_source(root, plan["bindingPlan"])
        result["authority"] = "fresh-lean-check"
        result["snapshotId"] = snapshot_identity(result)
    return result


def _verify_production(production):
    closed(production, {"schema", "status", "authority", "request", "check", "sourceText",
                        "artifacts", "snapshotId"}, "Real production")
    if production["schema"] != SCHEMA or production["snapshotId"] != snapshot_identity(production):
        raise ValueError("invalid or altered Real production identity")
    closed(production["request"], {"plan", "terms"}, "Real production request")
    if production["authority"] not in {"none", "fresh-lean-check"}:
        raise ValueError("unsupported recorded Real authority claim")
    expected = recorded_production(production["request"]["plan"], production["request"]["terms"],
                                   production["check"], production["sourceText"])
    # A producer's saved claim to freshness is not a checker capability.
    expected["authority"] = production["authority"]
    expected["snapshotId"] = snapshot_identity(expected)
    if production != expected:
        raise ValueError("Real saved production differs from exact evidence reconstruction")
    return production["request"]["plan"]


def _current_source(production, root):
    plan = production["request"]["plan"]
    validate_real_plan(plan)
    _root, source, _context = verify_binding_source(root, plan["bindingPlan"])
    if source != production["sourceText"].encode():
        raise ValueError("stale Real production source")
    inner = production["check"].get("result") or {}
    if inner.get("checkerIdentity") != native_checker_identity():
        raise ValueError("stale Real checker identity; replan and check the current implementation")


def inspect_real_bound(production, root=None):
    plan = _verify_production(production)
    if root is not None:
        _current_source(production, root)
    record = production["artifacts"][-1]["payload"]["record"] if production["artifacts"] else None
    return {"schema": "ladon-real-bound-inspection-v1", "status": "validated-historical",
            "authority": "none", "freshCheck": False, "evidenceAuthentication": "not-established",
            "sourceFreshness": "current" if root is not None else "not-checked",
            "recordedStatus": production["status"], "planId": plan["planId"],
            "contract": record, "paperNormBridge": "unresolved",
            "sourceTheoremProof": "not-checked",
            "mathematicalFalsity": "not-established"}


def replay_real_bound(production, root, *, timeout_seconds=600):
    _verify_production(production)
    _current_source(production, root)
    return produce_real_bound(root, production["request"]["plan"], production["request"]["terms"],
                              timeout_seconds=timeout_seconds)
