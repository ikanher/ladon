from __future__ import annotations

import hashlib
from typing import Any

from ladon.proofir_attachment_policy import RESOLVER_IDENTITY
from ladon.proofir_v3 import canonical_bytes, detached_content_id

ENVIRONMENT = "sha256:" + "e" * 64


def ref(kind: str, local_id: str) -> dict[str, str]:
    return {"kind": kind, "localId": local_id}


def producer() -> dict[str, str]:
    return {
        "name": "fixture-producer",
        "version": "1.0",
        "implementation": "python",
        "buildDigest": "sha256:" + "b" * 64,
    }


def coverage(*, observed: int = 1) -> dict[str, Any]:
    return {
        "status": "complete",
        "population": {"kind": "artifact-subjects", "selector": {}},
        "universeKnown": True,
        "expected": observed,
        "discovered": observed,
        "decoded": observed,
        "valid": observed,
        "projected": observed,
        "queryMatched": observed,
        "omitted": [],
        "bounds": {"maxSubjects": 1000},
    }


def envelope(
    kind: str,
    payload: dict[str, Any],
    subjects: list[dict[str, str]],
    *,
    environment: str = ENVIRONMENT,
    limitations: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "proofirVersion": "3.0",
        "artifactKind": kind,
        "artifactId": None,
        "producer": producer(),
        "environmentRef": environment,
        "subjectRefs": subjects,
        "coverage": coverage(observed=len(subjects)),
        "payload": payload,
        "limitations": limitations or [],
        "extensions": {"example.fixture/v1": {"note": "opaque"}},
    }
    value["artifactId"] = detached_content_id(value)
    return value


def environment_artifact() -> dict[str, Any]:
    payload = {
        "prover": {"name": "Lean", "version": "4.20.0"},
        "toolchain": {"name": "elan", "version": "1.0", "commit": "abc123"},
        "dependencies": [
            {
                "name": "mathlib",
                "version": "v4.20.0",
                "source": "lake-manifest",
                "digest": "sha256:" + "d" * 64,
            }
        ],
        "compiledModules": [{"module": "Fixture.Main", "digest": "sha256:" + "a" * 64}],
        "options": {"autoImplicit": False},
        "trust": {"axiomsAllowed": [], "unsafeAllowed": False},
        "fingerprintScheme": {"name": "lean-expr", "version": "1"},
    }
    environment = "sha256:" + hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return envelope("proofir.environment", payload, [], environment=environment)


def claim_artifact() -> dict[str, Any]:
    statement = ref("statement", "statement:goal")
    return envelope(
        "proofir.claim",
        {
            "claimId": "claim:goal",
            "statementRef": statement,
            "assertionState": "asserted",
        },
        [statement],
    )


def derivation_artifact() -> dict[str, Any]:
    rule = ref("declaration", "declaration:rule")
    premise_a = ref("statement", "statement:a")
    premise_b = ref("statement", "statement:b")
    goal = ref("statement", "statement:goal")
    step = ref("derivation-step", "step:1")
    term = ref("term", "term:x")
    context = ref("local-context", "context:1")
    check = ref("check-run", "check:1")
    return envelope(
        "proofir.derivation",
        {
            "derivationId": "derivation:goal",
            "acyclic": True,
            "steps": [
                {
                    "stepRef": step,
                    "kind": "theorem-application",
                    "ruleRef": rule,
                    "premiseRefs": [premise_a, premise_b],
                    "conclusionRef": goal,
                    "substitutions": [{"variable": "x", "termRef": term}],
                    "localContextRef": context,
                    "checkRunRef": check,
                }
            ],
        },
        [rule, premise_a, premise_b, goal, step, term, context, check],
    )


def plan_artifact() -> dict[str, Any]:
    goal = ref("statement", "statement:goal")
    step = ref("derivation-step", "step:planned")
    rule = ref("declaration", "declaration:rule")
    premise = ref("statement", "statement:premise")
    context = ref("local-context", "context:plan")
    return envelope(
        "proofir.plan",
        {
            "planId": "plan:goal",
            "goalRefs": [goal],
            "steps": [
                {
                    "stepRef": step,
                    "kind": "theorem-application",
                    "ruleRef": rule,
                    "premiseRefs": [premise],
                    "conclusionRef": goal,
                    "substitutions": [],
                    "localContextRef": context,
                }
            ],
            "policy": {
                "strategy": "least-cost",
                "budget": {"maxSteps": 10},
                "selection": "deterministic",
            },
        },
        [goal, step, rule, premise, context],
        limitations=[{"id": "advisory", "message": "A plan is not proof evidence."}],
    )


def attempt_log_artifact() -> dict[str, Any]:
    goal = ref("statement", "statement:goal")
    step = ref("derivation-step", "step:attempt")
    rule = ref("declaration", "declaration:rule")
    premise = ref("statement", "statement:residual")
    check = ref("check-run", "check:attempt")
    return envelope(
        "proofir.attempt-log",
        {
            "attemptLogId": "attempt-log:goal",
            "goalRef": goal,
            "attempts": [
                {
                    "attemptId": "attempt:1",
                    "stepRef": step,
                    "ruleRef": rule,
                    "premiseRefs": [premise],
                    "conclusionRef": goal,
                    "substitutions": [],
                    "checkRunRef": check,
                    "outcome": "rejected",
                    "diagnostics": [
                        {
                            "stage": "semantic-valid",
                            "code": "type-mismatch",
                            "pointer": "/payload/attempts/0",
                            "message": "candidate did not elaborate",
                            "order": 0,
                        }
                    ],
                }
            ],
            "summary": {"outcome": "incomplete", "residualPremiseRefs": [premise]},
        },
        [goal, step, rule, premise, check],
        limitations=[{"id": "not-proof", "message": "Attempts are diagnostic."}],
    )


def check_run_artifact() -> dict[str, Any]:
    statement = ref("statement", "statement:goal")
    return envelope(
        "proofir.check-run",
        {
            "checkRunId": "check:1",
            "checker": {
                "name": "Lean",
                "version": "4.20.0",
                "implementationDigest": "sha256:" + "1" * 64,
                "executableDigest": "sha256:" + "2" * 64,
            },
            "operation": "elaborate-declaration",
            "inputs": {
                "environmentRef": ENVIRONMENT,
                "subjectRefs": [statement],
                "artifactRefs": [],
            },
            "results": [
                {"subjectRef": statement, "result": "accepted", "diagnostics": []}
            ],
            "outputs": {
                "stdoutDigest": "sha256:" + "3" * 64,
                "stderrDigest": "sha256:" + "4" * 64,
            },
            "bounds": {"timeoutMs": 1000, "maxOutputBytes": 1048576},
            "guarantee": {
                "scope": "declaration-value",
                "statement": "accepted by the named checker",
                "authorityBasis": "kernel-check",
            },
        },
        [statement],
    )


def source_map_artifact() -> dict[str, Any]:
    statement = ref("statement", "statement:goal")
    return envelope(
        "proofir.source-map",
        {
            "sourceMapId": "source-map:1",
            "anchors": [
                {
                    "subjectRef": statement,
                    "sourcePath": "Fixture/Main.lean",
                    "module": "Fixture.Main",
                    "declName": "Fixture.goal",
                    "start": {"byte": 0, "line": 1, "column": 1},
                    "end": {"byte": 42, "line": 2, "column": 1},
                    "contentDigest": "sha256:" + "c" * 64,
                    "matchMethod": "environment-fingerprint",
                }
            ],
            "policy": {"version": "1", "digest": "sha256:" + "5" * 64},
        },
        [statement],
    )


def attachment_set_artifact() -> dict[str, Any]:
    statement = ref("statement", "statement:goal")
    surface = ref("surface", "surface:1")
    return envelope(
        "proofir.attachment-set",
        {
            "attachmentSetId": "attachments:1",
            "resolver": dict(RESOLVER_IDENTITY),
            "attachments": [
                {
                    "subjectRef": statement,
                    "selectionDecision": "selected",
                    "selectedCandidateId": "declaration:Fixture.goal",
                    "selectedSourceRef": surface,
                    "candidates": [
                        {
                            "declarationId": "declaration:Fixture.goal",
                            "sourceRef": surface,
                            "method": "environment-fingerprint",
                            "confidence": "exact",
                            "freshness": "fresh",
                            "rank": 0,
                            "policyVersion": RESOLVER_IDENTITY["version"],
                            "decisiveEvidence": [
                                {"kind": "environmentRef", "value": ENVIRONMENT}
                            ],
                            "rejectionReasons": [],
                        }
                    ],
                    "freshness": "fresh",
                    "decisiveEvidence": [
                        {"kind": "environmentRef", "value": ENVIRONMENT}
                    ],
                    "rejectionReasons": [],
                    "semanticAcceptance": False,
                }
            ],
        },
        [statement, surface],
        limitations=[
            {
                "id": "attachment-does-not-establish-theorem-truth",
                "message": "Source attachment is not semantic theorem acceptance.",
            }
        ],
    )


def governance_observation_artifact() -> dict[str, Any]:
    statement = ref("statement", "statement:goal")
    return envelope(
        "proofir.governance-observation",
        {
            "observationId": "observation:1",
            "observationKind": "review-policy",
            "subjectRef": statement,
            "result": "accepted",
            "guaranteeScope": "source-surface",
            "authorityBasis": "policy-observation",
            "dimensions": {
                "assertionState": "unknown",
                "semanticValidation": "unchecked",
                "freshness": "unknown",
                "attachmentResult": "unattached",
                "coverage": "complete",
                "replayRelationship": "unbound",
                "authorityBasis": "policy-observation",
                "guaranteeScope": "source-surface",
            },
            "details": {"policyId": "review:1"},
            "diagnostics": [],
        },
        [statement],
        limitations=[
            {"id": "not-proof", "message": "Governance is not theorem truth."}
        ],
    )


def native_artifacts() -> dict[str, dict[str, Any]]:
    return {
        artifact["artifactKind"]: artifact
        for artifact in (
            environment_artifact(),
            claim_artifact(),
            derivation_artifact(),
            plan_artifact(),
            attempt_log_artifact(),
            check_run_artifact(),
            source_map_artifact(),
            attachment_set_artifact(),
            governance_observation_artifact(),
        )
    }
