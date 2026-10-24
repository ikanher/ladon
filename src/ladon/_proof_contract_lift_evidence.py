"""Check the native evidence retained by a fresh, source-owned lift attempt."""
from __future__ import annotations

import hashlib
import json


def _digest(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _validate_native_evidence(native, job):
    """Recheck the worker's captured proof and trust projection before promotion."""
    evidence = native.get("nativeEvidence")
    if not isinstance(evidence, dict):
        raise TypeError("native proof evidence is missing")
    capture, completion = evidence.get("capture"), evidence.get("completion")
    if not isinstance(capture, dict) or not isinstance(completion, dict):
        raise TypeError("native capture or completion evidence is malformed")
    capture_id = _capture_identity(capture)
    _validate_subjects(evidence, capture, completion)
    _validate_completion(completion, capture_id, job["term"])
    _validate_trust(completion)
    _validate_inventory_binding(evidence, capture)


def _capture_identity(capture):
    capture_body = dict(capture)
    capture_id = capture_body.pop("captureId", None)
    raw = json.dumps(capture_body, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False).encode("utf-8")
    if capture_id != _digest(raw):
        raise ValueError("native capture identity does not match its contents")
    return capture_id


def _validate_subjects(evidence, capture, completion):
    canonical = evidence.get("canonicalTypedSubject")
    actual = evidence.get("actualTypedSubject")
    goal = capture.get("goal", {})
    application = completion.get("application", {})
    original_goal = application.get("originalGoal", {}) if isinstance(application, dict) else {}
    structural = goal.get("typeStructural")
    if not _subjects_match(canonical, actual, structural, original_goal):
        raise ValueError("semantic-goal-mismatch: canonical and native proposition structures differ")
    locals_ = goal.get("localContext")
    if not _locals_are_private(locals_):
        raise ValueError("native goal contains visible local assumptions")
    application_locals = original_goal.get("localContext")
    if application_locals != locals_ or completion.get("application", {}).get("residualGoals") != []:
        raise ValueError("proof-rejected: replayed application has locals or residual goals")


def _subjects_match(canonical, actual, structural, original_goal):
    return (type(canonical) is str and bool(canonical) and canonical == actual and canonical == structural
            and canonical == original_goal.get("typeStructural"))


def _locals_are_private(locals_):
    return isinstance(locals_, list) and all(
        isinstance(row, dict) and row.get("implementationDetail") is True for row in locals_)


def _validate_completion(completion, capture_id, term):
    if (completion.get("status") != "completed" or completion.get("captureId") != capture_id
            or completion.get("termDigest") != _digest(term.encode("utf-8"))):
        raise ValueError("proof-rejected: native completion is not bound to the supplied term and capture")


def _validate_trust(completion):
    replay, trust = completion.get("replay", {}), completion.get("trust", {})
    if not isinstance(replay, dict) or not isinstance(trust, dict):
        raise TypeError("native replay or trust evidence is malformed")
    observation = replay.get("observation", {}) if isinstance(replay, dict) else {}
    if not isinstance(observation, dict):
        raise TypeError("native replay observation is malformed")
    _validate_replay_coverage(replay, observation)
    _validate_axiom_policy(trust, observation, completion, replay)


def _validate_replay_coverage(replay, observation):
    if (replay.get("status") != "accepted" or replay.get("coverage") != "complete"
            or observation.get("coverage") != "complete"):
        raise ValueError("proof-rejected: independent replay coverage is incomplete")


def _validate_axiom_policy(trust, observation, completion, replay):
    allowed = {"propext", "Classical.choice", "Quot.sound"}
    axioms = _validate_axioms(trust, allowed)
    if trust.get("accepted") is not True:
        raise ValueError("trust-rejected: native trust projection did not accept this replay")
    observed = observation.get("observedAxioms")
    if not _string_list(observed) or set(observed) != set(axioms):
        raise ValueError("trust-rejected: replay and completion axiom projections differ")
    _validate_replay_binding(observation, completion, replay)


def _validate_axioms(trust, allowed):
    axioms = trust.get("observedAxioms")
    declared = trust.get("allowedAxioms")
    if (trust.get("policy") != "lean-standard-no-placeholders-v1"
            or not _string_list(declared) or set(declared) != allowed
            or trust.get("coverage") != "complete" or not _string_list(axioms)
            or set(axioms) - allowed):
        raise ValueError("trust-rejected: compiled proof has untrusted axiom dependencies")
    return axioms


def _string_list(value):
    return type(value) is list and all(type(item) is str for item in value)


def _validate_replay_binding(observation, completion, replay):
    source_context = replay.get("sourceContext", {})
    if not isinstance(source_context, dict):
        raise TypeError("replay source context is malformed")
    pairs = ((observation.get("captureId"), completion.get("captureId")),
             (observation.get("termDigest"), completion.get("termDigest")),
             (observation.get("sourceDigest"), replay.get("declarationBodyDigest")),
             (observation.get("sourceContextDigest"), source_context.get("digest")))
    if not all(_same_identity(left, right) for left, right in pairs):
        raise ValueError("proof-rejected: independent replay is bound to different source evidence")


def _same_identity(left, right):
    return type(left) is str and bool(left) and left == right


def _validate_inventory_binding(evidence, capture):
    environment = capture.get("environment", {})
    if not isinstance(environment, dict):
        raise TypeError("native capture environment is malformed")
    inventory = evidence.get("compiledInventory")
    if type(inventory) is not dict or not inventory or inventory != environment.get("compiledInventory"):
        raise ValueError("native compiled inventory binding changed")
    if not _same_identity(evidence.get("environmentRef"), environment.get("executionContextRef")):
        raise ValueError("native context identity differs from captured environment")
    if not _same_identity(evidence.get("executableIdentity"), environment.get("executableDigest")):
        raise ValueError("native executable identity differs from captured environment")
