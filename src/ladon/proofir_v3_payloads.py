"""Closed, kind-specific payload validators for ProofIR v3.

Envelope identity, canonicalization, bounds, and batch reference closure remain in
proofir_v3. This module owns only the nine native payload dialects so adding a
kind does not expand the envelope kernel into another analyzer monolith.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from ladon.proofir_attachment_policy import (
    MAX_CANDIDATES,
    POLICY_VERSION,
    RESOLVER_IDENTITY,
)
from ladon.proofir_observations import (
    AUTHORITY_BASES,
    GUARANTEE_SCOPES,
    EvidenceDimensions,
)
from ladon.proofir_v3 import (
    _closed_object,
    _digest,
    _escape,
    _fail,
    _require_ref,
    _subject_descriptor,
    _typed_reference,
    _validate_derivation_graph,
    canonical_bytes,
)


def _exact_payload(payload: Any, keys: set[str], value: Mapping[str, Any]) -> None:
    _closed_object(payload, keys, "/payload", value, "payload")


def validate_kind_payload(value: Mapping[str, Any]) -> None:
    """Dispatch a closed native artifact kind to its semantic validator."""

    kind, p, subjects, env = (
        value["artifactKind"],
        value["payload"],
        {
            _subject_descriptor(r, pointer=f"/subjectRefs/{i}")
            for i, r in enumerate(value["subjectRefs"])
        },
        value["environmentRef"],
    )
    validator = {
        "proofir.environment": _validate_environment,
        "proofir.claim": _validate_claim,
        "proofir.derivation": _validate_derivation,
        "proofir.plan": _validate_plan,
        "proofir.attempt-log": _validate_attempt,
        "proofir.check-run": _validate_check,
        "proofir.source-map": _validate_source,
        "proofir.attachment-set": _validate_attachment,
        "proofir.governance-observation": _validate_governance,
    }[kind]
    validator(p, value, subjects, env)


def _validate_environment(p, value, _subjects, env) -> None:
    """Bind an environment manifest payload to its canonical digest identity."""

    keys = {
        "prover",
        "toolchain",
        "dependencies",
        "compiledModules",
        "options",
        "trust",
        "fingerprintScheme",
    }
    _exact_payload(p, keys, value)
    dependency_count = len(p["dependencies"])
    for index, row in enumerate(p["dependencies"] + p["compiledModules"]):
        if not isinstance(row, dict):
            collection = (
                "dependencies" if index < dependency_count else "compiledModules"
            )
            _fail(
                "kind-schema-valid",
                "invalid-payload-field",
                f"/payload/{collection}/{index}",
                "invalid manifest entry",
                value,
            )
    expected = "sha256:" + hashlib.sha256(canonical_bytes(p)).hexdigest()
    if env != expected:
        _fail(
            "semantic-valid",
            "environment-digest-mismatch",
            "/environmentRef",
            "environment digest does not match payload",
            value,
        )


def _validate_claim(p, value, subjects, env) -> None:
    """Validate an assertion state over one registered statement identity.

    An asserted claim remains a claim record; this validator does not convert it
    into checker acceptance or theorem truth.
    """

    _exact_payload(p, {"claimId", "statementRef", "assertionState"}, value)
    _require_ref(
        p["statementRef"],
        "/payload/statementRef",
        subjects,
        env,
        value,
        "statement",
    )
    if p["assertionState"] not in {"asserted", "denied", "unknown"}:
        _fail(
            "kind-schema-valid",
            "invalid-enum",
            "/payload/assertionState",
            "invalid assertion state",
            value,
        )


def _validate_derivation(p, value, subjects, env) -> None:
    """Validate derivation rows and reject cyclic premise dependencies.

    The result is structural evidence only. Checker authority remains a separate
    observation/query concern and is never inferred from graph closure here.
    """

    _validate_steps(p, value, subjects, env, True)
    _validate_derivation_graph(p, value)


def _validate_steps(
    p: dict[str, Any],
    value: Mapping[str, Any],
    subjects: set[tuple[str, str]],
    env: str,
    derivation: bool,
) -> None:
    """Validate ordered plan or derivation steps against the subject registry.

    Premise order and repetition are semantic argument-slot evidence. The validator
    therefore checks each occurrence and never deduplicates the source arrays.
    """

    _validate_step_container(p, value, subjects, env, derivation)
    if not isinstance(p["steps"], list) or not p["steps"]:
        _fail(
            "kind-schema-valid",
            "invalid-steps",
            "/payload/steps",
            "steps must be non-empty",
            value,
        )
    step_keys = (
        {
            "stepRef",
            "kind",
            "ruleRef",
            "premiseRefs",
            "conclusionRef",
            "substitutions",
            "localContextRef",
            "checkRunRef",
        }
        if derivation
        else {
            "stepRef",
            "kind",
            "ruleRef",
            "premiseRefs",
            "conclusionRef",
            "substitutions",
            "localContextRef",
        }
    )
    seen: set[tuple[str, str]] = set()
    for index, step in enumerate(p["steps"]):
        _validate_step(
            step,
            f"/payload/steps/{index}",
            step_keys,
            seen,
            subjects,
            env,
            value,
            derivation,
        )


def _validate_step_container(p, value, subjects, env, derivation: bool) -> None:
    """Validate the family-specific step container before visiting its rows."""

    keys = {"planId", "goalRefs", "steps", "policy"}
    if derivation:
        keys = {"derivationId", "acyclic", "steps"}
        if p.get("acyclic") is False:
            keys.add("recursion")
    _exact_payload(p, keys, value)
    if derivation:
        _validate_acyclic_flag(p["acyclic"], value)
        if p["acyclic"] is False:
            _validate_recursion(p["recursion"], subjects, env, value)
        return
    for index, goal in enumerate(p["goalRefs"]):
        _require_ref(
            goal,
            f"/payload/goalRefs/{index}",
            subjects,
            env,
            value,
            "statement",
        )


def _validate_acyclic_flag(acyclic: Any, value: Mapping[str, Any]) -> None:
    """Require an explicit Boolean recursion policy selector."""

    if not isinstance(acyclic, bool):
        _fail(
            "kind-schema-valid",
            "invalid-field",
            "/payload/acyclic",
            "acyclic must be boolean",
            value,
        )


def _validate_recursion(
    recursion: Any,
    subjects: set[tuple[str, str]],
    env: str,
    value: Mapping[str, Any],
) -> None:
    """Validate explicit SCC policy and artifact-local component membership."""

    _closed_object(
        recursion, {"policy", "components"}, "/payload/recursion", value, "payload"
    )
    if recursion["policy"] != "declared-strongly-connected-components":
        _fail(
            "kind-schema-valid",
            "invalid-enum",
            "/payload/recursion/policy",
            "unsupported recursion policy",
            value,
        )
    components = recursion["components"]
    if not isinstance(components, list) or not components:
        _fail(
            "kind-schema-valid",
            "invalid-components",
            "/payload/recursion/components",
            "recursive derivation components must be non-empty",
            value,
        )
    seen_ids: set[str] = set()
    seen_members: set[tuple[str, str]] = set()
    for index, component in enumerate(components):
        _validate_recursive_component(
            component,
            index,
            subjects,
            env,
            value,
            seen_ids,
            seen_members,
        )


def _validate_recursive_component(
    component: Any,
    index: int,
    subjects: set[tuple[str, str]],
    env: str,
    value: Mapping[str, Any],
    seen_ids: set[str],
    seen_members: set[tuple[str, str]],
) -> None:
    """Validate one closed recursive component and its disjoint members."""

    pointer = f"/payload/recursion/components/{index}"
    _closed_object(
        component,
        {"componentId", "semantics", "statementRefs"},
        pointer,
        value,
        "payload",
    )
    component_id = component["componentId"]
    if (
        not isinstance(component_id, str)
        or not component_id
        or component_id in seen_ids
    ):
        _fail(
            "kind-schema-valid",
            "invalid-component-id",
            pointer + "/componentId",
            "componentId must be non-empty and unique",
            value,
        )
    seen_ids.add(component_id)
    if component["semantics"] != "declared-recursive-fixed-point":
        _fail(
            "kind-schema-valid",
            "invalid-enum",
            pointer + "/semantics",
            "unsupported recursive component semantics",
            value,
        )
    rows = component["statementRefs"]
    if not isinstance(rows, list) or not rows:
        _fail(
            "kind-schema-valid",
            "invalid-component-members",
            pointer + "/statementRefs",
            "component statementRefs must be non-empty",
            value,
        )
    for member_index, row in enumerate(rows):
        _validate_recursive_member(
            row, member_index, pointer, subjects, env, value, seen_members
        )


def _validate_recursive_member(
    row: Any,
    member_index: int,
    pointer: str,
    subjects: set[tuple[str, str]],
    env: str,
    value: Mapping[str, Any],
    seen_members: set[tuple[str, str]],
) -> None:
    """Resolve one SCC member and require disjoint declared components."""

    member_pointer = pointer + f"/statementRefs/{member_index}"
    _require_ref(row, member_pointer, subjects, env, value, "statement")
    member = _typed_reference(row, pointer=member_pointer)
    if member in seen_members:
        _fail(
            "kind-schema-valid",
            "duplicate-component-member",
            member_pointer,
            "statement appears in more than one recursive component",
            value,
        )
    seen_members.add(member)


def _validate_step(
    step: Any,
    pointer: str,
    step_keys: set[str],
    seen: set[tuple[str, str]],
    subjects: set[tuple[str, str]],
    env: str,
    value: Mapping[str, Any],
    derivation: bool,
) -> None:
    """Validate one closed step, its identity, references, and substitutions."""

    if not isinstance(step, dict):
        _closed_object(step, step_keys, pointer, value, "payload")
    extra = sorted(set(step) - step_keys)
    if extra:
        _fail(
            "kind-schema-valid",
            "unexpected-step-key",
            pointer + "/" + _escape(extra[0]),
            "unexpected step key",
            value,
        )
    _closed_object(step, step_keys, pointer, value, "payload")
    _validate_step_identity(step["stepRef"], pointer, seen, subjects, env, value)
    _validate_step_references(step, pointer, subjects, env, value, derivation)
    _validate_substitutions(step["substitutions"], pointer, subjects, env, value)


def _validate_step_identity(step_ref, pointer, seen, subjects, env, value) -> None:
    """Resolve and register one artifact-local derivation-step identity.

    Duplicate local step identities are rejected before graph construction so later
    alternatives cannot overwrite one another.
    """

    _require_ref(
        step_ref,
        pointer + "/stepRef",
        subjects,
        env,
        value,
        "derivation-step",
    )
    identity = (step_ref["kind"], step_ref["localId"])
    if identity in seen:
        _fail(
            "reference-valid",
            "duplicate-step-reference",
            pointer + "/stepRef",
            "duplicate derivation step reference",
            value,
        )
    seen.add(identity)


def _validate_step_references(step, pointer, subjects, env, value, derivation) -> None:
    """Validate every ordered reference field owned by one plan/derivation step."""

    _require_ref(
        step["ruleRef"], pointer + "/ruleRef", subjects, env, value, "declaration"
    )
    premises = step["premiseRefs"]
    if not isinstance(premises, list):
        _fail(
            "kind-schema-valid",
            "invalid-premises",
            pointer + "/premiseRefs",
            "premiseRefs must be an array",
            value,
        )
    for index, premise in enumerate(premises):
        _require_ref(
            premise,
            pointer + f"/premiseRefs/{index}",
            subjects,
            env,
            value,
            "statement",
        )
    for field, kind in (
        ("conclusionRef", "statement"),
        ("localContextRef", "local-context"),
    ):
        _require_ref(step[field], pointer + "/" + field, subjects, env, value, kind)
    if derivation:
        _require_ref(
            step["checkRunRef"],
            pointer + "/checkRunRef",
            subjects,
            env,
            value,
            "check-run",
        )


def _validate_substitutions(substitutions, pointer, subjects, env, value) -> None:
    """Preserve substitution occurrences while rejecting conflicting bindings."""

    if not isinstance(substitutions, list):
        _fail(
            "kind-schema-valid",
            "invalid-field",
            pointer + "/substitutions",
            "substitutions must be array",
            value,
        )
    seen: dict[str, tuple[str, str]] = {}
    for index, substitution in enumerate(substitutions):
        _validate_substitution(
            substitution,
            pointer + f"/substitutions/{index}",
            seen,
            subjects,
            env,
            value,
        )


def _validate_substitution(substitution, pointer, seen, subjects, env, value) -> None:
    """Validate one term binding and compare it with prior same-name bindings.

    Repeating the identical binding remains valid; only a different term for the
    same variable is a semantic conflict.
    """

    _closed_object(substitution, {"variable", "termRef"}, pointer, value, "payload")
    variable = substitution["variable"]
    if not isinstance(variable, str) or not variable:
        _fail(
            "kind-schema-valid",
            "invalid-substitution-variable",
            pointer + "/variable",
            "substitution variable must be a non-empty string",
            value,
        )
    term_ref = substitution["termRef"]
    _require_ref(term_ref, pointer + "/termRef", subjects, env, value, "term")
    term_identity = _typed_reference(term_ref, pointer=pointer + "/termRef")
    prior = seen.get(variable)
    if prior is not None and prior != term_identity:
        _fail(
            "semantic-valid",
            "conflicting-substitution",
            pointer + "/variable",
            "substitution variable has conflicting term references",
            value,
        )
    seen[variable] = term_identity


def _validate_plan(p, value, subjects, env):
    """Validate advisory plan steps and their closed selection policy.

    Plans describe intended traversal and do not inherit derivation/checker authority.
    """

    _validate_steps(p, value, subjects, env, False)
    _closed_object(
        p["policy"],
        {"strategy", "budget", "selection"},
        "/payload/policy",
        value,
        "payload",
    )


def _validate_attempt(p, value, subjects, env):
    """Validate an advisory attempt log without elevating outcomes to proof truth.

    Attempts retain checker references, diagnostics, and residual premises, but an
    accepted outcome alone does not create an authoritative checker observation.
    """

    _exact_payload(p, {"attemptLogId", "goalRef", "attempts", "summary"}, value)
    _require_ref(p["goalRef"], "/payload/goalRef", subjects, env, value, "statement")
    if not isinstance(p["attempts"], list) or not p["attempts"]:
        _fail(
            "kind-schema-valid",
            "invalid-attempts",
            "/payload/attempts",
            "attempts must be non-empty",
            value,
        )
    for index, attempt in enumerate(p["attempts"]):
        _validate_attempt_row(
            attempt, f"/payload/attempts/{index}", subjects, env, value
        )
    _validate_attempt_summary(p["summary"], subjects, env, value)


def _validate_attempt_row(attempt, pointer, subjects, env, value) -> None:
    """Validate one closed attempt and its attributable diagnostics."""

    _closed_object(
        attempt,
        {
            "attemptId",
            "stepRef",
            "ruleRef",
            "premiseRefs",
            "conclusionRef",
            "substitutions",
            "checkRunRef",
            "outcome",
            "diagnostics",
        },
        pointer,
        value,
        "payload",
    )
    _validate_attempt_references(attempt, pointer, subjects, env, value)
    if attempt["outcome"] not in {
        "proposed",
        "accepted",
        "rejected",
        "timeout",
        "infrastructure-error",
    }:
        _fail(
            "kind-schema-valid",
            "invalid-enum",
            pointer + "/outcome",
            "invalid outcome",
            value,
        )
    _validate_ordered_diagnostics(attempt["diagnostics"], pointer, value)


def _validate_attempt_references(attempt, pointer, subjects, env, value) -> None:
    """Close every attempt reference over the envelope's exact environment.

    Premise occurrences are checked in source order and retained independently even
    when the same statement appears more than once.
    """

    for field, kind in (
        ("stepRef", "derivation-step"),
        ("ruleRef", "declaration"),
        ("conclusionRef", "statement"),
        ("checkRunRef", "check-run"),
    ):
        _require_ref(attempt[field], pointer + "/" + field, subjects, env, value, kind)
    for index, premise in enumerate(attempt["premiseRefs"]):
        _require_ref(
            premise,
            pointer + f"/premiseRefs/{index}",
            subjects,
            env,
            value,
            "statement",
        )
    _validate_substitutions(attempt["substitutions"], pointer, subjects, env, value)


def _validate_ordered_diagnostics(diagnostics, pointer, value) -> None:
    """Require diagnostic order fields to match canonical array positions.

    Contiguous explicit order makes diagnostics stable across JSON, SQLite, and
    language implementations without relying on incidental map iteration.
    """

    for index, diagnostic in enumerate(diagnostics):
        diagnostic_pointer = pointer + f"/diagnostics/{index}"
        _closed_object(
            diagnostic,
            {"stage", "code", "pointer", "message", "order"},
            diagnostic_pointer,
            value,
            "payload",
        )
        if not isinstance(diagnostic["order"], int) or diagnostic["order"] != index:
            _fail(
                "kind-schema-valid",
                "invalid-diagnostic-order",
                diagnostic_pointer + "/order",
                "diagnostic order must be contiguous",
                value,
            )


def _validate_attempt_summary(summary, subjects, env, value) -> None:
    """Validate residual statement references when the summary declares them.

    Other summary fields remain opaque unless they participate in reference closure,
    avoiding invented proof semantics for advisory attempt metadata.
    """

    if not isinstance(summary, dict) or not isinstance(
        summary.get("residualPremiseRefs"), list
    ):
        return
    for index, residual in enumerate(summary["residualPremiseRefs"]):
        _require_ref(
            residual,
            f"/payload/summary/residualPremiseRefs/{index}",
            subjects,
            env,
            value,
            "statement",
        )


def _validate_check(p, value, subjects, env):
    """Validate checker execution identity, scoped inputs, and explicit results.

    Authority is carried only by the declared guarantee fields; this validator does
    not infer stronger scope from an accepted result code.
    """

    _exact_payload(
        p,
        {
            "checkRunId",
            "checker",
            "operation",
            "inputs",
            "results",
            "outputs",
            "bounds",
            "guarantee",
        },
        value,
    )
    _validate_checker_identity(p["checker"], value)
    _validate_check_inputs(p["inputs"], value, subjects, env)
    _validate_check_outputs(p["outputs"], value)
    _validate_check_bounds(p["bounds"], value)
    _validate_check_guarantee(p["guarantee"], value)
    _validate_check_results(p["results"], value, subjects, env)
    _validate_scoped_check_guarantee(p["results"], p["guarantee"], value)


def _validate_checker_identity(checker, value) -> None:
    _closed_object(
        checker,
        {"name", "version", "implementationDigest", "executableDigest"},
        "/payload/checker",
        value,
        "payload",
    )
    for field in ("name", "version"):
        if not isinstance(checker[field], str) or not checker[field]:
            _fail(
                "kind-schema-valid",
                "invalid-checker-identity",
                f"/payload/checker/{field}",
                "checker identity fields must be non-empty",
                value,
            )
    for f in ("implementationDigest", "executableDigest"):
        if not _digest(checker[f]):
            _fail(
                "kind-schema-valid",
                "invalid-content-digest",
                f"/payload/checker/{f}",
                "invalid digest",
                value,
            )


def _validate_check_inputs(inputs, value, subjects, env) -> None:
    _closed_object(
        inputs,
        {"environmentRef", "subjectRefs", "artifactRefs"},
        "/payload/inputs",
        value,
        "payload",
    )
    if inputs.get("environmentRef") != env:
        _fail(
            "reference-valid",
            "reference-environment-mismatch",
            "/payload/inputs/environmentRef",
            "reference environment mismatch",
            value,
        )
    for i, r in enumerate(inputs.get("subjectRefs", [])):
        _require_ref(r, f"/payload/inputs/subjectRefs/{i}", subjects, env, value)
    if not isinstance(inputs["artifactRefs"], list) or not all(
        _digest(artifact_ref) for artifact_ref in inputs["artifactRefs"]
    ):
        _fail(
            "kind-schema-valid",
            "invalid-check-inputs",
            "/payload/inputs/artifactRefs",
            "input artifact references must be sha256 digests",
            value,
        )


def _validate_check_results(results, value, subjects, env) -> None:
    if not isinstance(results, list):
        _fail(
            "kind-schema-valid",
            "invalid-results",
            "/payload/results",
            "results must be array",
            value,
        )
    for i, r in enumerate(results):
        _closed_object(
            r,
            {"subjectRef", "result", "diagnostics"},
            f"/payload/results/{i}",
            value,
            "payload",
        )
        _require_ref(
            r["subjectRef"], f"/payload/results/{i}/subjectRef", subjects, env, value
        )
        if r["result"] not in {"accepted", "rejected", "unknown", "error"}:
            _fail(
                "kind-schema-valid",
                "invalid-enum",
                f"/payload/results/{i}/result",
                "invalid result",
                value,
            )


def _validate_scoped_check_guarantee(results, guarantee, value) -> None:
    if not results and guarantee["scope"] not in {"none", "process-exit"}:
        _fail(
            "semantic-valid",
            "unscoped-checker-guarantee",
            "/payload/guarantee/scope",
            "a subject guarantee requires at least one per-subject result",
            value,
        )


def _validate_check_outputs(outputs, value) -> None:
    _closed_object(
        outputs,
        {"stdoutDigest", "stderrDigest"},
        "/payload/outputs",
        value,
        "payload",
    )
    for field in ("stdoutDigest", "stderrDigest"):
        if not _digest(outputs[field]):
            _fail(
                "kind-schema-valid",
                "invalid-content-digest",
                f"/payload/outputs/{field}",
                "checker output digest must be sha256",
                value,
            )


def _validate_check_bounds(bounds, value) -> None:
    _closed_object(
        bounds,
        {"timeoutMs", "maxOutputBytes"},
        "/payload/bounds",
        value,
        "payload",
    )
    if any(
        not isinstance(bounds[field], int)
        or isinstance(bounds[field], bool)
        or bounds[field] < 1
        for field in ("timeoutMs", "maxOutputBytes")
    ):
        _fail(
            "kind-schema-valid",
            "invalid-check-bounds",
            "/payload/bounds",
            "checker bounds must be positive integers",
            value,
        )


def _validate_check_guarantee(guarantee, value) -> None:
    _closed_object(
        guarantee,
        {"scope", "statement", "authorityBasis"},
        "/payload/guarantee",
        value,
        "payload",
    )
    if (
        guarantee["scope"] not in GUARANTEE_SCOPES
        or guarantee["authorityBasis"] not in AUTHORITY_BASES
        or not isinstance(guarantee["statement"], str)
        or not guarantee["statement"]
    ):
        _fail(
            "kind-schema-valid",
            "invalid-check-guarantee",
            "/payload/guarantee",
            "checker guarantee must use typed authority and scope",
            value,
        )


def _validate_source(p, value, subjects, env):
    """Validate bounded source anchors and their explicit matching methods.

    A match-method label records how a producer located source text. It is not a
    freshness or checker-authority guarantee.
    """

    _exact_payload(p, {"sourceMapId", "anchors", "policy"}, value)
    _closed_object(
        p["policy"], {"version", "digest"}, "/payload/policy", value, "payload"
    )
    for i, a in enumerate(p["anchors"]):
        ptr = f"/payload/anchors/{i}"
        _closed_object(
            a,
            {
                "subjectRef",
                "sourcePath",
                "module",
                "declName",
                "start",
                "end",
                "contentDigest",
                "matchMethod",
            },
            ptr,
            value,
            "payload",
        )
        _require_ref(a["subjectRef"], ptr + "/subjectRef", subjects, env, value)
        if not _digest(a["contentDigest"]):
            _fail(
                "kind-schema-valid",
                "invalid-content-digest",
                ptr + "/contentDigest",
                "invalid digest",
                value,
            )
        if a["matchMethod"] not in {
            "environment-fingerprint",
            "producer-declaration",
            "content-range",
            "content-name",
            "path-range",
            "module-name",
            "name-only-diagnostic",
        }:
            _fail(
                "kind-schema-valid",
                "invalid-enum",
                ptr + "/matchMethod",
                "invalid match method",
                value,
            )


def _validate_attachment(p, value, subjects, env):
    """Validate source attachments while preserving ambiguity and rejection data.

    An empty resolver result is allowed only when a limitation records that absence;
    the validator does not fabricate a selected source candidate.
    """

    _exact_payload(p, {"attachmentSetId", "resolver", "attachments"}, value)
    _closed_object(
        p["resolver"],
        {"name", "version", "digest"},
        "/payload/resolver",
        value,
        "payload",
    )
    if p["resolver"] != RESOLVER_IDENTITY:
        _fail(
            "semantic-valid",
            "unsupported-attachment-policy",
            "/payload/resolver",
            "attachment set must name the Ladon-owned resolver policy",
            value,
        )
    for i, a in enumerate(p["attachments"]):
        _validate_attachment_decision(a, i, value, subjects, env)
    if not p["attachments"] and not value["limitations"]:
        _fail(
            "semantic-valid",
            "empty-evidence-without-limitation",
            "/limitations",
            "empty attachments require limitation",
            value,
        )


def _validate_attachment_decision(a, index, value, subjects, env) -> None:
    pointer = f"/payload/attachments/{index}"
    _closed_object(
        a,
        {
            "subjectRef",
            "selectionDecision",
            "selectedCandidateId",
            "selectedSourceRef",
            "candidates",
            "freshness",
            "decisiveEvidence",
            "rejectionReasons",
            "semanticAcceptance",
        },
        pointer,
        value,
        "payload",
    )
    _require_ref(a["subjectRef"], pointer + "/subjectRef", subjects, env, value)
    _validate_attachment_decision_fields(a, pointer, value, subjects, env)
    _validate_attachment_selection(a, pointer, value)


def _validate_attachment_decision_fields(a, pointer, value, subjects, env) -> None:
    if a["selectedSourceRef"] is not None:
        _require_ref(
            a["selectedSourceRef"],
            pointer + "/selectedSourceRef",
            subjects,
            env,
            value,
        )
    if a["selectionDecision"] not in {"selected", "ambiguous", "unresolved", "none"}:
        _fail(
            "kind-schema-valid",
            "invalid-enum",
            pointer + "/selectionDecision",
            "invalid attachment selection decision",
            value,
        )
    if a["freshness"] not in {"fresh", "stale", "unknown"}:
        _fail(
            "kind-schema-valid",
            "invalid-enum",
            pointer + "/freshness",
            "invalid attachment freshness",
            value,
        )
    if not isinstance(a["candidates"], list) or len(a["candidates"]) > MAX_CANDIDATES:
        _fail(
            "kind-schema-valid",
            "attachment-candidate-bound",
            pointer + "/candidates",
            "attachment candidates must be a bounded array",
            value,
        )
    _validate_attachment_lists(a, pointer, value)
    for candidate_index, candidate in enumerate(a["candidates"]):
        _validate_attachment_candidate(
            candidate, candidate_index, pointer, value, subjects, env
        )


def _validate_attachment_lists(a, pointer, value) -> None:
    if not isinstance(a["decisiveEvidence"], list) or not isinstance(
        a["rejectionReasons"], list
    ):
        _fail(
            "kind-schema-valid",
            "invalid-attachment-evidence",
            pointer,
            "attachment evidence and rejection reasons must be arrays",
            value,
        )
    if a["semanticAcceptance"] is not False:
        _fail(
            "semantic-valid",
            "attachment-cannot-accept-semantics",
            pointer + "/semanticAcceptance",
            "source attachment cannot establish semantic acceptance",
            value,
        )


def _validate_attachment_candidate(
    candidate, index, pointer, value, subjects, env
) -> None:
    candidate_pointer = pointer + f"/candidates/{index}"
    _closed_object(
        candidate,
        {
            "declarationId",
            "sourceRef",
            "method",
            "confidence",
            "freshness",
            "rank",
            "policyVersion",
            "decisiveEvidence",
            "rejectionReasons",
        },
        candidate_pointer,
        value,
        "payload",
    )
    _require_ref(
        candidate["sourceRef"], candidate_pointer + "/sourceRef", subjects, env, value
    )
    _validate_attachment_candidate_values(candidate, candidate_pointer, value)


def _validate_attachment_candidate_values(candidate, pointer, value) -> None:
    methods = {
        "environment-fingerprint",
        "producer-declaration",
        "content-range",
        "content-name",
        "path-range",
        "module-name",
        "name-only-diagnostic",
        "identity-conflict-diagnostic",
        "unsafe-path-diagnostic",
        "unmatched-diagnostic",
    }
    checks = (
        _valid_attachment_candidate_identity(candidate),
        _valid_attachment_candidate_enums(candidate, methods),
        _valid_attachment_candidate_rank(candidate),
        _valid_attachment_candidate_collections(candidate),
    )
    if not all(checks):
        _fail(
            "kind-schema-valid",
            "invalid-attachment-candidate",
            pointer,
            "invalid attachment candidate fields",
            value,
        )


def _valid_attachment_candidate_identity(candidate) -> bool:
    return (
        isinstance(candidate["declarationId"], str)
        and bool(candidate["declarationId"])
        and candidate["policyVersion"] == POLICY_VERSION
    )


def _valid_attachment_candidate_enums(candidate, methods) -> bool:
    return (
        candidate["method"] in methods
        and candidate["confidence"] in {"exact", "strong", "bounded-fallback", "none"}
        and candidate["freshness"] in {"fresh", "stale", "unknown"}
    )


def _valid_attachment_candidate_rank(candidate) -> bool:
    return (
        isinstance(candidate["rank"], int)
        and not isinstance(candidate["rank"], bool)
        and candidate["rank"] >= 0
    )


def _valid_attachment_candidate_collections(candidate) -> bool:
    return isinstance(candidate["decisiveEvidence"], list) and isinstance(
        candidate["rejectionReasons"], list
    )


def _validate_attachment_selection(a, pointer, value) -> None:
    if a["selectionDecision"] == "selected":
        _validate_selected_attachment(a, pointer, value)
        return
    if a["selectedCandidateId"] is not None or a["selectedSourceRef"] is not None:
        _fail(
            "semantic-valid",
            "contradictory-attachment-decision",
            pointer,
            "unselected attachment cannot retain selected identity",
            value,
        )


def _validate_selected_attachment(a, pointer, value) -> None:
    selected = [
        candidate
        for candidate in a["candidates"]
        if candidate["declarationId"] == a["selectedCandidateId"]
        and candidate["sourceRef"] == a["selectedSourceRef"]
    ]
    if len(selected) != 1 or selected[0]["method"].endswith("diagnostic"):
        _fail(
            "semantic-valid",
            "contradictory-attachment-decision",
            pointer,
            "selected attachment must identify one selectable retained candidate",
            value,
        )


def _validate_governance(p, value, subjects, env):
    """Validate one attributable governance observation and its diagnostics.

    Observation result, guarantee scope, and authority basis remain distinct fields;
    no result value silently strengthens either declared boundary.
    """

    _exact_payload(
        p,
        {
            "observationId",
            "observationKind",
            "subjectRef",
            "result",
            "guaranteeScope",
            "authorityBasis",
            "dimensions",
            "details",
            "diagnostics",
        },
        value,
    )
    _require_ref(p["subjectRef"], "/payload/subjectRef", subjects, env, value)
    try:
        dimensions = EvidenceDimensions.from_dict(p["dimensions"])
    except (KeyError, TypeError, ValueError) as exc:
        _fail(
            "kind-schema-valid",
            "invalid-evidence-dimensions",
            "/payload/dimensions",
            str(exc),
            value,
        )
    if (
        p["authorityBasis"] != dimensions.authority_basis
        or p["guaranteeScope"] != dimensions.guarantee_scope
    ):
        _fail(
            "semantic-valid",
            "contradictory-evidence-dimensions",
            "/payload/dimensions",
            "authority and guarantee must agree with the orthogonal dimensions",
            value,
        )
    for i, d in enumerate(p["diagnostics"]):
        _closed_object(
            d,
            {"stage", "code", "pointer", "message", "order"},
            f"/payload/diagnostics/{i}",
            value,
            "payload",
        )
