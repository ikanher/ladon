"""Deterministic native projection of historical source-bound Real evidence."""

import hashlib

from ladon.proof_contract_formal import _position
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import make_envelope, validate_envelope_batch
from ladon.real_bound_native_evidence import checked_evidence
from ladon.real_bound_native_payload import LIMITATIONS
from ladon.real_bound_native_profile import PROFILE_DIGEST
from ladon.real_bound_native_record import build_record


def _envelope(kind, env, subjects, payload):
    return make_envelope(
        artifact_kind="proofir." + kind, producer={"name": "ladon-real-bound", "version": "1"},
        environment_ref=env, subject_refs=subjects, coverage={"status": "partial", "observed": len(subjects)},
        limitations=[{"id": key, "message": message} for key, message in LIMITATIONS.items()],
        payload=payload).to_dict()


def external(artifact, kind, local_id):
    return {"artifactRef": artifact["artifactId"], "kind": kind, "localId": local_id}


def _source(plan, raw, env):
    snapshot = plan["bindingPlan"]["observation"]["statementSnapshot"]
    if not isinstance(raw, bytes) or len(raw) > 8 * 1024**2:
        raise ValueError("Real source bytes exceed the source bound")
    if hashlib.sha256(raw).hexdigest() != snapshot["source"]["sha256"]:
        raise ValueError("Real source digest differs from the admission source")
    lines = raw.decode("utf-8").splitlines(keepends=True)
    location = snapshot["observation"]["declarationRange"]
    statement = {"kind": "statement", "localId": "statement:" + snapshot["snapshotId"][7:]}
    source = {"kind": "source-map", "localId": "source:" + snapshot["snapshotId"][7:]}
    anchor = {"subjectRef": statement, "sourcePath": snapshot["source"]["path"],
              "module": snapshot["selection"]["module"], "declName": snapshot["selection"]["declaration"],
              "start": _position(lines, location["startLine"], location["startColumn"]),
              "end": _position(lines, location["endLine"], location["endColumn"]),
              "contentDigest": "sha256:" + snapshot["source"]["sha256"],
              "matchMethod": "environment-fingerprint"}
    return _envelope("source-map", env, [source, statement], {
        "sourceMapId": source["localId"], "anchors": [anchor],
        "policy": {"version": "real-source-v1", "digest": PROFILE_DIGEST}}), statement


def _check(check, evidence, source, statement, env):
    actual = check["evidence"]
    capture = actual["capture"]["capture"]
    structural = actual["typedSubject"]["subject"]["structural"]
    digest = "sha256:" + hashlib.sha256(structural.encode()).hexdigest()
    goal = {"kind": "statement", "localId": "goal:" + digest[7:]}
    subject = {**goal, "fingerprint": {"scheme": {"name": "lean-typed-goal", "version": "1"},
                                       "digest": digest}}
    check_ref = {"kind": "check-run", "localId": "check:" + snapshot_identity(check)[7:]}
    receipt = actual["completion"]["processReceipts"][-1]
    return _envelope("check-run", env, [check_ref, subject], {
        "checkRunId": check_ref["localId"], "operation": "real-bound:" + check["goal"]["id"],
        "checker": {"name": "Lean", "version": capture["environment"]["leanVersion"],
                    "implementationDigest": evidence["checkerIdentity"],
                    "executableDigest": capture["environment"]["executableDigest"]},
        "inputs": {"environmentRef": env, "subjectRefs": [goal, statement],
                   "artifactRefs": [source["artifactId"]]},
        "results": [{"subjectRef": goal, "result": "accepted", "diagnostics": []}],
        "outputs": {key: receipt[key] for key in ("stdoutDigest", "stderrDigest")},
        "bounds": {"timeoutMs": 60000, "maxOutputBytes": 8 * 1024**2},
        "guarantee": {"scope": "declaration-value", "authorityBasis": "stored-observation",
                      "statement": "Recorded source-bound kernel replay; fresh semantic use requires rechecking."},
    })


def real_bound_artifacts(plan, run, source_bytes):
    """Reconstruct recorded artifacts. Only the fresh producer may claim live checking."""
    evidence = checked_evidence(plan, run, source_bytes)
    env = plan["bindingPlan"]["observation"]["statementSnapshot"]["environment"]
    source, statement = _source(plan, source_bytes, env)
    statement_ref = external(source, kind="statement", local_id=statement["localId"])
    checks = [_check(check, evidence, source, statement_ref, env) for check in evidence["checks"]]
    refs = [external(check, "check-run", check["payload"]["checkRunId"]) for check in checks]
    record, expressions = build_record(plan, evidence, refs)
    contract_id = "contract:" + plan["planId"][7:]
    conclusion = {"kind": "statement", "localId": record["conclusionId"]}
    contract = _envelope("contract", env,
                         [{"kind": "contract", "localId": contract_id}, conclusion, *expressions], {
        "contractId": contract_id, "profileDigest": PROFILE_DIGEST, "record": record,
        "statementRef": statement_ref, "conclusionRef": conclusion, "assumptionRefs": [],
        "sourceMapRefs": [external(source, "source-map", source["payload"]["sourceMapId"])],
        "checkRunRefs": refs,
        "provenance": {"mode": "extracted", "fidelity": "attributed-unreviewed", "completeness": "partial",
                       "checkerAuthority": "none", "mathematicalFalsity": "not-established"},
        "residuals": [{"code": "paper-norm-bridge-unresolved", "feature": "interpretation",
                       "message": "The declared prefix interpretation does not establish the paper's norm."}],
    })
    artifacts = [source, *checks, contract]
    validate_envelope_batch(artifacts)
    return artifacts
