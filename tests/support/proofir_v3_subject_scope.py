"""Native-v3 fixtures for artifact-owned ProofIR subject identity.

These deliberately do not use the pre-scope ``environmentRef`` reference
shape.  A descriptor belongs to its enclosing artifact; a payload reference is
either local (``kind``/``localId``) or names an already-content-addressed,
different owner through ``artifactRef``.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ladon.proofir_v3 import detached_content_id

ENVIRONMENT = "sha256:" + "e" * 64
FOREIGN_ENVIRONMENT = "sha256:" + "f" * 64
SUPPORTED_SCHEME = {"name": "lean-expr", "version": "1"}
UNKNOWN_SCHEME = {"name": "future-opaque", "version": "9"}


def local_ref(kind: str, local_id: str) -> dict[str, str]:
    return {"kind": kind, "localId": local_id}


def external_ref(owner: str, kind: str, local_id: str) -> dict[str, str]:
    return {"artifactRef": owner, "kind": kind, "localId": local_id}


def subject(
    kind: str,
    local_id: str,
    *,
    fingerprint: str | None = None,
    scheme: dict[str, str] | None = None,
    display: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {"kind": kind, "localId": local_id}
    if fingerprint is not None:
        value["fingerprint"] = {
            "scheme": deepcopy(scheme or SUPPORTED_SCHEME),
            "digest": fingerprint,
        }
    if display is not None:
        value["display"] = display
    return value


def producer() -> dict[str, str]:
    return {
        "name": "subject-scope-fixture",
        "version": "1.0",
        "implementation": "python",
        "buildDigest": "sha256:" + "b" * 64,
    }


def coverage(subject_count: int) -> dict[str, Any]:
    return {
        "status": "complete",
        "population": {"kind": "artifact-subjects", "selector": {}},
        "universeKnown": True,
        "expected": subject_count,
        "discovered": subject_count,
        "decoded": subject_count,
        "valid": subject_count,
        "projected": subject_count,
        "queryMatched": subject_count,
        "omitted": [],
        "bounds": {"maxSubjects": 1000},
    }


def envelope(
    kind: str,
    payload: dict[str, Any],
    subjects: list[dict[str, Any]],
    *,
    environment: str = ENVIRONMENT,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "proofirVersion": "3.0",
        "artifactKind": kind,
        "artifactId": None,
        "producer": producer(),
        "environmentRef": environment,
        "subjectRefs": deepcopy(subjects),
        "coverage": coverage(len(subjects)),
        "payload": deepcopy(payload),
        "limitations": [],
        "extensions": {},
    }
    value["artifactId"] = detached_content_id(value)
    return value


def claim(
    *,
    fingerprint: str = "sha256:" + "1" * 64,
    scheme: dict[str, str] | None = None,
    environment: str = ENVIRONMENT,
    local_id: str = "statement:goal",
) -> dict[str, Any]:
    statement = subject(
        "statement",
        local_id,
        fingerprint=fingerprint,
        scheme=scheme,
        display="Fixture.goal",
    )
    return envelope(
        "proofir.claim",
        {
            "claimId": "claim:goal",
            "statementRef": local_ref("statement", local_id),
            "assertionState": "asserted",
        },
        [statement],
        environment=environment,
    )


def derivation(
    *,
    derivation_id: str = "derivation:scope",
    context_id: str = "context:shared",
    step_id: str = "step:shared",
) -> dict[str, Any]:
    refs = [
        subject("statement", "statement:premise"),
        subject("statement", "statement:goal"),
        subject("declaration", "declaration:rule"),
        subject("derivation-step", step_id),
        subject("local-context", context_id),
        subject("check-run", "check:shared"),
    ]
    return envelope(
        "proofir.derivation",
        {
            "derivationId": derivation_id,
            "acyclic": True,
            "steps": [
                {
                    "stepRef": local_ref("derivation-step", step_id),
                    "kind": "theorem-application",
                    "ruleRef": local_ref("declaration", "declaration:rule"),
                    "premiseRefs": [local_ref("statement", "statement:premise")],
                    "conclusionRef": local_ref("statement", "statement:goal"),
                    "substitutions": [],
                    "localContextRef": local_ref("local-context", context_id),
                    "checkRunRef": local_ref("check-run", "check:shared"),
                }
            ],
        },
        refs,
    )
