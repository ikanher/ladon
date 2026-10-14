"""Check missing prose/formal implications against their original generated goals.

The source interpretation and object map remain attributed inputs. Only actual
Lean capture/completion with independent replay supplies mathematical authority.
"""

from __future__ import annotations

import copy
import json
import re
import tempfile
from pathlib import Path

from ladon.correspondence_execution_accounting import execution_accounting, stage
from ladon.correspondence_implementation import implementation_digest
from ladon.correspondence_interpretation import (
    LOWERING_PROFILE,
    UnsupportedInterpretation,
    binder_identities,
    closed,
    lower_domain,
    lower_formula,
    validate_interpretation,
)
from ladon.correspondence_maps import map_references, mapped_expression, validate_object_map
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import digest, extract_proof_slice, pinned_toolchain, slice_identity
from ladon.scoped_slice import profile_is_scoped
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

SCHEMA = "ladon-correspondence-plan-v2"
_LOCAL = re.compile(r"[A-Za-z_α-ωΑ-Ω][A-Za-z_0-9α-ωΑ-Ω]*\Z")
_LOADED_IMPLEMENTATION = implementation_digest()


def _parts(record, reserved=()):
    scope, prefix = {}, []
    identities = binder_identities(record["formula"])
    node = record["formula"]
    while node["tag"] == "forall":
        binder = node["binder"]
        name = f"ladonNL{len(scope)}"
        while name in reserved:
            name += "_"
        domain = lower_domain(binder["domain"], scope, identities)
        prefix.append(f"∀ ({name} : {domain}), ")
        scope[binder["id"]] = name
        node = node["body"]
    premises = []
    while node["tag"] == "implies":
        premises.append(lower_formula(node["premise"], record["symbols"], _scope=scope))
        node = node["conclusion"]
    assumption = "(" + " ∧ ".join(premises) + ")" if premises else "True"
    conclusion = lower_formula(node, record["symbols"], _scope=scope)
    return scope, "".join(prefix), assumption, conclusion


def _fvars(expression):
    structural = expression["structural"]
    if not structural.startswith("ladon-expr-dag-v1:"):
        raise ValueError("missing actual structural expression")
    dag = json.loads(structural.removeprefix("ladon-expr-dag-v1:"))
    return {node[1] for node in dag["nodes"] if node[0] == "fvar"}


def _check_slice(proof_slice):
    if not isinstance(proof_slice, dict) or proof_slice.get("schema") != "ladon-proof-slice-v1":
        raise ValueError("correspondence requires source-bound extraction, not an authored graph")
    if proof_slice.get("status") != "extracted" or not proof_slice.get("complete"):
        raise ValueError("no completed selected application extraction")
    from ladon.proof_slice_validation import validate_slice_shape

    validate_slice_shape(proof_slice)
    if proof_slice.get("sliceId") != slice_identity(proof_slice):
        raise ValueError("altered extraction observation")
    if not proof_slice.get("processReceipts") or any(
        row["returncode"] != 0 for row in proof_slice["processReceipts"]
    ):
        raise ValueError("missing successful extraction receipts")


def _plan_shell(interpretation, proof_slice, object_map):
    _check_slice(proof_slice)
    record = validate_interpretation(interpretation, None)
    object_map = validate_object_map(object_map)
    return record, {
        "schema": SCHEMA,
        "loweringProfile": LOWERING_PROFILE,
        "interpretation": record,
        "slice": copy.deepcopy(proof_slice),
        "objectMap": copy.deepcopy(object_map),
        "obligations": [
            {
                "id": "conditional",
                "kind": "conditional-validity",
                "goal": proof_slice["nodes"][0]["closedType"],
                "status": "open",
            }
        ],
        "residuals": [],
    }


def _lower_interpretation(plan, record, proof_slice):
    try:
        formula = lower_formula(record["formula"], record["symbols"])
        lowered = _parts(record, [row["name"] for row in proof_slice["localContext"]])
    except UnsupportedInterpretation as error:
        plan["residuals"].append({"kind": "unsupported-interpretation", "reason": str(error)})
        return None
    scope, prefix, assumptions, conclusion = lowered
    return formula, scope, prefix, assumptions, conclusion


def _check_object_map(proof_slice, object_map, scope):
    objects = {
        row["name"]
        for row in proof_slice["localContext"]
        if not row["isProp"] and row["letValue"] is None
    }
    if any(key not in objects or any(ref not in scope for ref in map_references(value))
           for key, value in object_map.items()):
        raise ValueError("unknown object map reference or escaped binder")
    _reject_nested_object_map(proof_slice, object_map)
    return objects


def _reject_nested_object_map(proof_slice, object_map):
    if not profile_is_scoped(proof_slice):
        return
    selected = proof_slice["observation"]["applications"][proof_slice["selection"]["occurrence"]]
    nested = set(selected["nestedLocalIds"])
    if any(row["name"] in object_map and row["localId"] in nested
           for row in proof_slice["localContext"]):
        raise ValueError("escaped witness: nested scope cannot map to an outer prose object")


def _record_local_name_residuals(locals_, plan):
    names = [row["name"] for row in locals_]
    if len(set(names)) == len(names) and all(_LOCAL.fullmatch(name) for name in names):
        return
    plan["residuals"].append(
        {
            "kind": "unsupported-local-names",
            "reason": "requires unique printable formal local names",
        }
    )


def _mapped_object_binding(row, object_map, scope, allowed, lets, plan):
    if not _fvars(row["type"]) <= allowed:
        plan["residuals"].append({"kind": "dependent-object-type", "local": row["name"]})
        return
    expression = mapped_expression(object_map[row["name"]], scope, plan["interpretation"]["symbols"])
    lets.append(f"let {row['name']} : {row['type']['display']} := {expression}; ")
    allowed.add(row["localId"])


def _local_value_binding(row, allowed, lets, plan):
    if _fvars(row["letValue"]) <= allowed and _fvars(row["type"]) <= allowed:
        lets.append(
            f"let {row['name']} : {row['type']['display']} := {row['letValue']['display']}; "
        )
        allowed.add(row["localId"])
    else:
        plan["residuals"].append({"kind": "local-value-provider", "local": row["name"]})


def _local_bindings(proof_slice, object_map, scope, plan):
    locals_ = proof_slice["localContext"]
    objects = _check_object_map(proof_slice, object_map, scope)
    _record_local_name_residuals(locals_, plan)
    lets, allowed = [], set()
    for row in locals_:
        if row["name"] in object_map:
            _mapped_object_binding(row, object_map, scope, allowed, lets, plan)
        elif row["letValue"] is not None and not row["isProp"]:
            _local_value_binding(row, allowed, lets, plan)
        elif row["name"] in objects:
            plan["residuals"].append({"kind": "missing-object-map", "local": row["name"]})
    return "".join(lets), allowed


def _make_obligations(
    proof_slice, object_map, formula, scope, prefix, assumptions, conclusion, plan
):
    lets, allowed = _local_bindings(proof_slice, object_map, scope, plan)
    wrap = prefix + lets
    node = proof_slice["nodes"][0]
    obligations = [
        {
            "id": "interpretation",
            "kind": "welltypedness",
            "goal": f"({formula}) → ({formula})",
            "status": "open",
        },
        {
            "id": "conditional",
            "kind": "conditional-validity",
            "goal": node["closedType"],
            "status": "open",
        },
    ]
    # Elaborating this goal checks every direct map's declared formal type.
    if not plan["residuals"]:
        obligations.append(
            {
                "id": "object-map",
                "kind": "representation-transport",
                "goal": wrap + "True",
                "status": "open",
            }
        )
    for premise in node["premises"]:
        identity = f"premise-{premise['occurrence']}"
        if plan["residuals"] or not _fvars(premise["proposition"]) <= allowed:
            plan["residuals"].append(
                {
                    "kind": "premise-supply",
                    "occurrence": premise["occurrence"],
                    "reason": "missing mapping or proof-dependent proposition",
                }
            )
        else:
            obligations.append(
                {
                    "id": identity,
                    "kind": "premise-supply",
                    "goal": wrap + f"({assumptions}) → ({premise['proposition']['display']})",
                    "status": "open",
                }
            )
    if not plan["residuals"] and _fvars(node["type"]) <= allowed:
        obligations.append(
            {
                "id": "conclusion",
                "kind": "conclusion-transfer",
                "goal": wrap + f"({assumptions}) → ({node['type']['display']}) → ({conclusion})",
                "status": "open",
            }
        )
    else:
        plan["residuals"].append(
            {"kind": "conclusion-transfer", "reason": "unsupported object/proof dependencies"}
        )
    plan["obligations"] = obligations


def prepare_correspondence(interpretation, proof_slice, object_map):
    record, plan = _plan_shell(interpretation, proof_slice, object_map)
    link_slice, link_map = _transport_inputs(proof_slice, object_map)
    lowered = _lower_interpretation(plan, record, link_slice)
    if lowered is not None:
        formula, scope, prefix, assumptions, conclusion = lowered
        _make_obligations(
            link_slice, link_map, formula, scope, prefix, assumptions, conclusion, plan
        )
    _provider_obligations(plan, proof_slice)
    plan["planId"] = digest(plan)
    return plan


def _provider_obligations(plan, proof_slice):
    if not profile_is_scoped(proof_slice):
        return
    for premise in proof_slice["nodes"][0]["premises"]:
        plan["obligations"].append({
            "id": f"provider-{premise['occurrence']}",
            "kind": "premise-provider-validity",
            "goal": premise["providerObservation"]["closedType"],
            "status": "open",
        })


def _actual_typed_subject(typed):
    frames = [line.removeprefix("LADON_TYPED_SUBJECT ") for line in typed.stdout.splitlines()
              if line.startswith("LADON_TYPED_SUBJECT ")]
    if len(frames) != 1:
        raise ValueError("missing unique actual typed subject observation")
    return json.loads(frames[0])


def _verify_prepared_inputs(prepared, root, source, toolchain):
    if prepared is None:
        return
    from ladon.correspondence_preparation import PreparedSourceContext
    if not isinstance(prepared, PreparedSourceContext) or prepared.root != root:
        raise ValueError("stale or unowned prepared source context")
    prepared.verify_inputs(root, source, toolchain)


def _generated_prelude(prepared, source, symbols, goal):
    from ladon.correspondence_preparation import RESET, source_prelude
    declarations = "\n".join(
        f"#check ({row['leanName']} : {row['leanType']})" for row in symbols.values())
    prefix = (prepared.import_prefix + RESET.encode() if prepared is not None
              else source_prelude(source))
    return prefix.decode() + declarations + f"\n#ladon_typed_subject ({goal})\n"


def _write_goal_source(path, text):
    if len(text.encode()) > 8 * 1024**2:
        raise ValueError("generated module exceeds source byte bound")
    path.write_text(text)


def _check_goal(goal, term, root, source, symbols, toolchain, *, prepared=None):
    # Copy the original source, rather than import a possibly stale target olean.
    # Its direct compiled imports are fingerprinted by capture/completion.
    _verify_prepared_inputs(prepared, root, source, toolchain)
    state = root / ".ladon/correspondence"
    state.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="goal-", dir=state) as temporary:
        path = Path(temporary) / "LadonCorrespondence.lean"
        prelude = _generated_prelude(prepared, source, symbols, goal)
        # Observe the original copied-source proposition even during reuse.
        # Imported modules do not export every local elaboration extension.
        typing_prelude = (_generated_prelude(None, source, symbols, goal)
                          if prepared is not None else prelude)
        _write_goal_source(path, typing_prelude)
        execution = prepare_direct_lean_execution(
            root, None, toolchain, require_compiled_module=False
        )
        with stage("typing"):
            typed = run_bounded_target_process(
                [*execution.command, str(path)],
                cwd=root,
                env=execution.environment,
                timeout_seconds=60,
                max_output_bytes=8 * 1024**2,
                max_rss_bytes=32 * 1024**3,
            )
        if not typed.succeeded:
            from dataclasses import asdict

            return {"status": "unresolved", "typecheck": asdict(typed)}
        typed_subject = _actual_typed_subject(typed)
        text = prelude + f"\nexample : {goal} := by\n  skip\n"
        _write_goal_source(path, text)
        # The generated file is deliberately part of this pinned source context.
        # Resolve after writing it, then keep it unchanged through independent replay.
        toolchain = pinned_toolchain(root)
        with stage("capture"):
            capture = capture_source_goal(
                SourceGoalCaptureRequest(
                    root,
                    str(path.relative_to(root)),
                    "LadonCorrespondence",
                    len(text.splitlines()),
                    4,
                    toolchain,
                )
            )
        if capture["status"] != "captured":
            from dataclasses import asdict

            return {"status": "unresolved", "capture": capture, "typecheck": asdict(typed)}
        if (prepared is not None
                and typed_subject["subject"]["structural"]
                != capture["capture"]["goal"]["typeStructural"]):
            return {
                "status": "unresolved", "capture": capture,
                "typecheck": __import__("dataclasses").asdict(typed),
                "typedSubject": typed_subject,
                "diagnostic": {
                    "code": "prepared-goal-subject-mismatch",
                    "message": "Original-source proposition differs from prepared captured goal.",
                },
            }
        if any(
            not row["implementationDetail"] for row in capture["capture"]["goal"]["localContext"]
        ):
            return {
                "status": "unresolved",
                "capture": capture,
                "typecheck": __import__("dataclasses").asdict(typed),
                "diagnostic": {
                    "code": "unexpected-generated-goal-context",
                    "message": "Generated obligations cannot inherit ambient locals.",
                },
            }
        with stage("completion-replay-trust"):
            completion = complete_source_goal(
                SourceGoalCompletionRequest(root, capture["capture"], term, toolchain)
            )
        if prepared is not None:
            prepared.verify()
        return {
            "status": "supported" if completion["status"] == "completed" else "unresolved",
            "capture": capture,
            "completion": completion,
            "goalOrigin": "generated-correspondence-obligation",
            "typedSubject": typed_subject,
            "typecheck": __import__("dataclasses").asdict(typed),
        }


def _validate_current_plan(plan, native_artifacts):
    keys = {"schema", "loweringProfile", "interpretation", "slice", "objectMap", "obligations", "residuals", "planId"}
    if isinstance(plan, dict) and "interpretationRef" in plan:
        keys.add("interpretationRef")
        if native_artifacts is None:
            raise ValueError("native prepared plan requires its exact validated artifact batch")
    closed(
        plan,
        keys,
        "correspondence plan",
    )
    if plan["schema"] != SCHEMA or plan["loweringProfile"] != LOWERING_PROFILE:
        raise ValueError("unknown correspondence lowering profile; historical plans require fresh preparation")


def _rebuild_original_plan(plan, repo_root, source_root, native_artifacts):
    _validate_current_plan(plan, native_artifacts)
    root = Path(repo_root).resolve(strict=True)
    validate_interpretation(plan["interpretation"], Path(source_root or root))
    selection = plan["slice"]["selection"]
    fresh = extract_proof_slice(
        root,
        selection["sourceFile"],
        selection["module"],
        selection["declaration"],
        selection["application"],
        selection["occurrence"],
        scoped=profile_is_scoped(plan["slice"]),
    )
    if fresh.get("sliceId") != plan["slice"]["sliceId"]:
        raise ValueError("stale source, context, toolchain, or selected application")
    rebuilt = prepare_correspondence(plan["interpretation"], plan["slice"], plan["objectMap"])
    if "interpretationRef" in plan:
        from ladon.proofir_correspondence import bind_native_interpretation

        rebuilt = bind_native_interpretation(
            rebuilt, native_artifacts, source_root=Path(source_root or root)
        )
    if plan != rebuilt:
        raise ValueError("correspondence goal or original contract changed")
    return root, selection, fresh


def _validate_term_row(row, obligations, supplied):
    closed(row, {"obligation", "term", "mode"}, "supplied term")
    identity = row["obligation"]
    if (
        identity not in obligations
        or identity in supplied
        or row["mode"] not in {"prove", "refute"}
    ):
        raise ValueError("unknown/duplicate obligation or mode")
    term = row["term"]
    if not isinstance(term, str) or not term.strip() or len(term.encode()) > 1024**2:
        raise ValueError("invalid bounded supplied proof term")
    supplied[identity] = row


def _validate_terms(terms, plan):
    if not isinstance(terms, list) or len(terms) > 16:
        raise ValueError("terms must be a bounded list of at most sixteen attempts")
    obligations = {row["id"]: row for row in plan["obligations"]}
    supplied = {}
    for row in terms:
        _validate_term_row(row, obligations, supplied)
    return supplied


def _initial_result(plan):
    return {
        "schema": "ladon-correspondence-check-v1",
        "planId": plan["planId"],
        "conditionalValidity": "unresolved",
        "premiseEstablishment": "unresolved",
        "parentSupport": "unresolved",
        "interpretationFidelity": "attributed-unreviewed",
        "methodCorrespondence": "unreviewed",
        "extractionCompleteness": "selected-application",
        "checkerAuthority": "lean-worker",
        "checks": [],
        "residuals": copy.deepcopy(plan["residuals"]),
    }


def _automatic_terms(supplied, fresh):
    automatic = {"conditional": fresh["nodes"][0]["closedProof"]}
    if profile_is_scoped(fresh):
        automatic.update({f"provider-{p['occurrence']}": p["providerObservation"]["closedProof"]
                          for p in fresh["nodes"][0]["premises"]})
    for identity, term in automatic.items():
        if identity not in supplied:
            supplied[identity] = {"obligation": identity, "term": term, "mode": "prove"}


def _check_supplied_terms(supplied, obligations, fresh, plan, source, root, toolchain, result,
                          *, prepared=None):
    # Conditional validity concerns the actual formal proof; it is deliberately
    # separate from establishing the prose's premise providers.
    _automatic_terms(supplied, fresh)
    for index, (identity, row) in enumerate(supplied.items()):
        if index >= 16:
            result["residuals"].append({"kind": "check-attempt-limit", "obligation": identity,
                                        "reason": "sixteen total supplied and automatic replays"})
            continue
        goal = obligations[identity]["goal"]
        with stage(f"obligation:{identity}"):
            checked = _check_goal(
                f"¬ ({goal})" if row["mode"] == "refute" else goal,
                row["term"],
                root,
                source,
                plan["interpretation"]["symbols"],
                toolchain,
                prepared=prepared,
            )
        if checked["status"] == "supported" and row["mode"] == "refute":
            checked["status"] = "refuted"
        result["checks"].append(
            {"obligation": identity, "mode": row["mode"], "goal": goal, **checked}
        )
    return result


def _summarize_premises(result, plan, statuses):
    premise_ids = [row["id"] for row in plan["obligations"] if row["kind"] == "premise-supply"]
    if any(statuses.get(identity) == "refuted" for identity in premise_ids):
        result["premiseEstablishment"] = "refuted"
    elif not result["residuals"] and all(
        statuses.get(identity) == "supported" for identity in premise_ids
    ):
        result["premiseEstablishment"] = "supported"


def _summarize_parent_support(result, statuses, obligations):
    required = set(obligations)
    if not result["residuals"] and all(
        statuses.get(identity) == "supported" for identity in required
    ):
        result["parentSupport"] = "supported-for-attributed-interpretation"
    elif any(statuses.get(identity) == "refuted" for identity in required):
        result["parentSupport"] = "refuted-correspondence"


def _summarize_result(result, plan, obligations):
    statuses = {row["obligation"]: row["status"] for row in result["checks"]}
    result["conditionalValidity"] = statuses.get("conditional", "unresolved")
    _summarize_premises(result, plan, statuses)
    _summarize_parent_support(result, statuses, obligations)
    if profile_is_scoped(plan["slice"]):
        providers = [o["id"] for o in plan["obligations"]
                     if o["kind"] == "premise-provider-validity"]
        result["providerValidity"] = (
            "conditionally-supported" if all(statuses.get(i) == "supported" for i in providers)
            else "refuted" if any(statuses.get(i) == "refuted" for i in providers)
            else "unresolved"
        )


def _verify_inputs_unchanged(root, selection, source, fresh, plan, source_root):
    if (root / selection["sourceFile"]).read_bytes() != source:
        raise ValueError("source changed during correspondence checking")
    validate_interpretation(plan["interpretation"], Path(source_root or root))
    # Re-extraction rechecks the full compiled environment and helper identity
    # after the last obligation. A mid-run change cannot inherit old acceptance.
    final = extract_proof_slice(
        root,
        selection["sourceFile"],
        selection["module"],
        selection["declaration"],
        selection["application"],
        selection["occurrence"],
        scoped=profile_is_scoped(fresh),
    )
    if final.get("sliceId") != fresh["sliceId"]:
        raise ValueError("environment changed during correspondence checking")


def _check_correspondence(plan, terms, repo_root, *, source_root=None, native_artifacts=None,
                          preparation="ordinary"):
    """Rebuild and independently replay the exact original generated obligations."""
    if implementation_digest() != _LOADED_IMPLEMENTATION:
        raise ValueError("checker implementation changed after loading")
    with stage("original-extraction"):
        root, selection, fresh = _rebuild_original_plan(plan, repo_root, source_root, native_artifacts)
    supplied = _validate_terms(terms, plan)
    source = (root / selection["sourceFile"]).read_bytes()
    with stage("toolchain-setup"):
        toolchain = pinned_toolchain(root)
    obligations = {row["id"]: row for row in plan["obligations"]}
    result = _initial_result(plan)
    result["implementationDigest"] = _LOADED_IMPLEMENTATION
    _execute_terms(preparation, supplied, obligations, fresh, plan, source, root, toolchain, result)
    _summarize_result(result, plan, obligations)
    with stage("final-freshness"):
        _verify_inputs_unchanged(root, selection, source, fresh, plan, source_root)
    if implementation_digest() != _LOADED_IMPLEMENTATION:
        raise ValueError("checker implementation changed during checking")
    return result


def _execute_terms(preparation, supplied, obligations, fresh, plan, source, root, toolchain, result):
    from contextlib import nullcontext

    from ladon.correspondence_import_cache import verified_import_cache
    from ladon.correspondence_preparation import prepare_source_context
    if preparation not in {"ordinary", "request"}:
        raise ValueError("unsupported correspondence preparation mode")
    owner = (prepare_source_context(root, fresh, source, toolchain)
             if preparation == "request" else nullcontext(None))
    from ladon.correspondence_preparation import SourcePreparationFailure
    try:
        with owner as prepared:
            result["preparationMode"] = "request" if prepared is not None else "ordinary"
            with (verified_import_cache(prepared) if prepared is not None else nullcontext()):
                _check_supplied_terms(supplied, obligations, fresh, plan, source, root, toolchain,
                                      result, prepared=prepared)
            result["compiledImportIdentityReuses"] = (prepared.cached_import_reads if prepared else 0)
    except SourcePreparationFailure as error:
        error.plan_id = plan['planId']
        error.unattempted = [row['id'] for row in plan['obligations']]
        raise


def check_correspondence(plan, terms, repo_root, *, source_root=None, native_artifacts=None,
                         preparation="ordinary"):
    with execution_accounting() as accounting:
        result = _check_correspondence(plan, terms, repo_root, source_root=source_root,
                                       native_artifacts=native_artifacts, preparation=preparation)
    result["executionAccounting"] = accounting.result()
    result["executionAccounting"].update(
        distinctProseSubjects=1,
        distinctCheckedSubjects=len({(r["goal"], r["mode"]) for r in result["checks"]}),
        typingProbeCount=sum(r["obligation"] == "interpretation" for r in result["checks"]),
        substantiveCheckCount=sum(r["obligation"] != "interpretation" for r in result["checks"]),
        interpretationInputBytes=len(json.dumps(plan["interpretation"], ensure_ascii=False, separators=(",", ":")).encode()),
        suppliedTermBytes=sum(len(row["term"].encode()) for row in terms),
        checkCount=len(result["checks"]), sourceBytes=len((Path(repo_root) / plan["slice"]["selection"]["sourceFile"]).read_bytes()))
    return result


from ladon.correspondence_transport import transport_inputs as _transport_inputs
