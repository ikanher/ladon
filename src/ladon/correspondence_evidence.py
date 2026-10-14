"""Project actual correspondence completion receipts into native checker records."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from ladon.proofir_correspondence import PRODUCER, _as_exact_decimal_strings
from ladon.proofir_v3 import canonical_bytes, make_envelope


def _hash(value):
    return "sha256:" + hashlib.sha256(canonical_bytes(_as_exact_decimal_strings(value))).hexdigest()


def _envelope(kind, environment, subjects, payload, evidence):
    count = len(subjects)
    return make_envelope(
        artifact_kind=kind,
        producer=PRODUCER,
        environment_ref=environment,
        subject_refs=subjects,
        payload=payload,
        coverage={
            "status": "complete",
            "population": {"kind": "artifact-subjects", "selector": {}},
            "universeKnown": True,
            "expected": count,
            "discovered": count,
            "decoded": count,
            "valid": count,
            "projected": count,
            "queryMatched": count,
            "omitted": [],
            "bounds": {"maxSubjects": 16},
        },
        limitations=[
            {
                "id": "generated-goal",
                "message": "Authority applies to the exact generated obligation or its negation, not to prose fidelity or method.",
            }
        ],
        extensions={"ladon.correspondence-receipt/v1": evidence},
    ).to_dict()


def _stream_digest(receipt, stream):
    return receipt.get(stream + "Digest") or (
        "sha256:" + hashlib.sha256(receipt.get(stream, "").encode("utf-8")).hexdigest()
    )


def _process_evidence(row, observed):
    receipts = observed or ([row["typecheck"]] if "typecheck" in row else [])
    if not receipts or not receipts[-1].get("command"):
        raise ValueError("native check-run requires an actual supervised process receipt")
    last = receipts[-1]
    executable = Path(last["command"][0])
    return last, "sha256:" + hashlib.sha256(executable.read_bytes()).hexdigest()


def _accepted(row, completion):
    supported = (
        row["status"] in {"supported", "refuted"}
        and completion.get("status") == "completed"
        and completion.get("replay", {}).get("status") == "accepted"
        and completion.get("trust", {}).get("accepted") is True
    )
    if row["status"] in {"supported", "refuted"} and not supported:
        raise ValueError("accepted correspondence lacks independent replay and trust receipts")
    return supported


def _subject_mismatch_diagnostics(row):
    diagnostic = row.get("diagnostic", {})
    if diagnostic.get("code") != "prepared-goal-subject-mismatch":
        return []
    return [{"stage": "context-equivalence", "code": diagnostic["code"],
             "pointer": "/checks/" + row["obligation"],
             "message": diagnostic["message"], "order": 0}]


def _row_artifacts(plan, row, implementation_digest):
    env = plan["slice"]["environment"]
    completion = row.get("completion", {})
    supported = _accepted(row, completion)
    diagnostics = _subject_mismatch_diagnostics(row)
    observed = completion.get("processReceipts", [])
    identity = _hash({"planId": plan["planId"], "receipt": row})
    goal = {"kind": "statement", "localId": "obligation:" + identity[7:]}
    check_subject = {"kind": "check-run", "localId": "check:" + identity[7:]}
    declaration = {"kind": "declaration", "localId": plan["slice"]["selection"]["declaration"]}
    step = {"kind": "derivation-step", "localId": "step:" + identity[7:]}
    evidence = {
        "planId": plan["planId"],
        "obligation": row["obligation"],
        "mode": row["mode"],
        "goalDigest": _hash(row["goal"]),
        "checkedGoal": row["goal"] if row["mode"] == "prove" else "¬ (" + row["goal"] + ")",
        "receiptDigest": _hash(row),
        "captureId": completion.get("captureId"),
        "termDigest": completion.get("termDigest"),
        "replaySourceDigest": completion.get("replay", {}).get("sourceDigest"),
        "trust": completion.get("trust"),
        "status": row["status"],
    }
    # Digests come from actual supervised process output. An unsuccessful
    # preflight still receives an unknown result, with no kernel guarantee.
    last, executable_digest = _process_evidence(row, observed)
    check = _envelope(
        "proofir.check-run",
        env,
        [goal, check_subject],
        {
            "checkRunId": check_subject["localId"],
            "checker": {
                "name": "Lean source-goal completion",
                "version": "1",
                "implementationDigest": implementation_digest,
                "executableDigest": executable_digest,
            },
            "operation": "generated-correspondence-obligation-" + row["mode"],
            "inputs": {"environmentRef": env, "subjectRefs": [goal], "artifactRefs": []},
            "results": [
                {
                    "subjectRef": goal,
                    "result": "accepted" if supported else "unknown",
                    "diagnostics": diagnostics,
                }
            ],
            "outputs": {
                "stdoutDigest": _stream_digest(last, "stdout"),
                "stderrDigest": _stream_digest(last, "stderr"),
            },
            "bounds": {"timeoutMs": 60000, "maxOutputBytes": 8388608},
            "guarantee": {
                "scope": "declaration-value" if supported else "none",
                "statement": "Independent Lean replay checked the generated obligation under the recorded no-placeholder trust policy."
                if supported
                else "No completed mathematical check.",
                "authorityBasis": "kernel-check" if supported else "process-observation",
            },
        },
        evidence,
    )
    ref = {"artifactRef": check["artifactId"], **check_subject}
    attempt = _envelope(
        "proofir.attempt-log",
        env,
        [goal, declaration, step],
        {
            "attemptLogId": "attempt-log:" + identity[7:],
            "goalRef": goal,
            "attempts": [
                {
                    "attemptId": "attempt:" + identity[7:],
                    "stepRef": step,
                    "ruleRef": declaration,
                    "premiseRefs": [],
                    "conclusionRef": goal,
                    "substitutions": [],
                    "checkRunRef": ref,
                    "outcome": "accepted" if supported else ("proposed" if diagnostics else "rejected"),
                    "diagnostics": diagnostics,
                }
            ],
            "summary": {
                "outcome": "complete" if supported else "unknown",
                "residualPremiseRefs": [],
            },
        },
        evidence,
    )
    return check, attempt, ref


def completion_artifacts(plan, result):
    """Bind observed completion receipts; portable validation does not replace replay."""
    artifacts, references = [], []
    implementation = result.get("implementationDigest")
    if not isinstance(implementation, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", implementation):
        raise ValueError("native completion requires the captured checker implementation digest")
    for row in result["checks"]:
        check, attempt, ref = _row_artifacts(plan, row, implementation)
        artifacts.extend([check, attempt])
        references.append(ref)
    return artifacts, references
