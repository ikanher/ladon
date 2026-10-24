"""Isolated contract tests for the source-bound witness-dependence-v2 profile."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ladon.correspondence_check import prepare_correspondence
from ladon.proof_contract_artifacts import source_contract_artifact
from ladon.proofir_correspondence import (
    bind_native_interpretation,
    correspondence_artifacts,
    interpretation_artifacts,
)

TEMPLATE = {
    "familyId": "witness-dependence",
    "version": "witness-dependence-v2",
    "direction": "right-to-left",
    "kind": "counterexample",
}
LEGACY_TEMPLATE = {**TEMPLATE, "version": "witness-dependence-v1"}


def _record_formula(quantifiers, relation="predicate", argument_order=("w", "x")):
    w = {"id": "w", "name": "w", "domain": "Nat"}
    x = {"id": "x", "name": "x", "domain": "Nat"}
    if relation == "predicate":
        body = {"tag": "app", "symbol": "P", "args": [
            {"tag": "var", "id": identity} for identity in argument_order
        ]}
    else:
        body = {"tag": relation, "left": {"tag": "var", "id": "x"}, "right": {"tag": "var", "id": "w"}}
    if quantifiers == ("exists", "forall"):
        outer_binder, inner_binder = w, x
    else:
        outer_binder, inner_binder = x, w
    tree = {"tag": quantifiers[1], "binder": inner_binder, "body": body}
    return {"tag": quantifiers[0], "binder": outer_binder, "body": tree}


def _record(root: Path, name: str, quantifiers: tuple[str, str], relation="predicate", argument_order=("w", "x"), symbol_name="AppProbe.P"):
    statement = f"P({argument_order[0]},{argument_order[1]})" if relation == "predicate" else ("x = w" if relation == "eq" else "x ≤ w")
    quote = ("Exists w, for every x, " if quantifiers == ("exists", "forall") else "For every x, exists w, ") + statement + "."
    path = f"{name}.txt"
    (root / path).write_text(quote + "\n", encoding="utf-8")
    tree = _record_formula(quantifiers, relation=relation, argument_order=argument_order)
    return {
        "id": name,
        "source": {"path": path, "startLine": 1, "endLine": 1, "quote": quote,
                   "sha256": hashlib.sha256((quote + "\n").encode()).hexdigest()},
        "formula": tree,
        "symbols": {"P": {"leanName": symbol_name, "leanType": "Nat → Nat → Prop"}} if relation == "predicate" else {},
    }


def _contract(rows, *, object_id="object:nat", witness_allowed=None, anchored_constant=False):
    position = {binder: index for index, (binder, _kind) in enumerate(rows)}
    allowed = ["x"] if position["x"] < position["w"] else []
    if witness_allowed is not None:
        allowed = witness_allowed
    return {
        "profileId": "norm-scale-v1",
        "endpointId": "predicate:P",
        "context": {"objectId": object_id, "domainId": "domain:Nat",
                    "scaleId": "scale:none", "representationId": "representation:original"},
        "telescope": [{"binderId": binder, "typeId": "Nat", "quantifier": quantifier}
                      for binder, quantifier in rows],
        "assumptions": [],
        "conclusionId": "predicate:P",
        "features": {
            "regularity": {"state": "unknown", "scaleId": "scale:none", "offset": None, "reason": "not modeled by witness profile"},
            "constantDependencies": ({"binderId": "w", "state": "known", "allowedBinderIds": allowed, "reason": None}
                                     if anchored_constant else {"state": "unknown", "allowedBinderIds": None, "reason": "not modeled by witness profile"}),
            "witnessDependencies": [{"binderId": "w", "state": "known",
                                     "allowedBinderIds": allowed, "reason": None}],
        },
    }


def _rows(quantifiers):
    if quantifiers == ("exists", "forall"):
        return (("w", "exists"), ("x", "forall"))
    return (("x", "forall"), ("w", "exists"))


def _make_side(source_root, proof_slice, environment, index, quantifiers,
               contract_quantifiers, object_id, allowed, options):
    ident = f"reading-{index}"
    record = _record(
        source_root, ident, quantifiers, relation=options["relation"],
        argument_order=options["argument_orders"][index],
        symbol_name=options["symbol_names"][index],
    )
    if options["record_mutator"] is not None:
        options["record_mutator"](record, index)
    source_map, interpretation = interpretation_artifacts(
        record, environment, source_root=source_root
    )
    contract = _contract(
        _rows(contract_quantifiers), object_id=object_id, witness_allowed=allowed,
        anchored_constant=options["anchored_constant"],
    )
    contract_artifact = source_contract_artifact(
        contract, contract_id=f"contract:{ident}", environment_ref=environment,
        source_map_refs=[{"artifactRef": source_map["artifactId"], "kind": "source-map",
                          "localId": source_map["payload"]["sourceMapId"]}],
        residuals=[{"code": "profile-feature-omitted",
                    "message": "Regularity and scalar constant dependence are outside this witness profile.",
                    "feature": "witness-dependence-v2"}],
    )
    prepared = prepare_correspondence(record, proof_slice, {})
    prepared = bind_native_interpretation(
        prepared, [source_map, interpretation], source_root=source_root
    )
    correspondence = correspondence_artifacts(prepared)
    artifacts = [source_map, interpretation, contract_artifact, correspondence]
    side = {
        "contractRef": {"artifactRef": contract_artifact["artifactId"], "kind": "contract",
                        "localId": contract_artifact["payload"]["contractId"]},
        "correspondenceRef": {"artifactRef": correspondence["artifactId"], "kind": "correspondence",
                              "localId": correspondence["payload"]["correspondenceId"]},
    }
    return artifacts, side


def _source_bound_pair(tmp_path: Path, formula_pairs=None, contract_pairs=None,
                       contexts=None, permissions=None, record_mutator=None,
                       relation="predicate", anchored_constant=False,
                       argument_orders=None, symbol_names=None):
    source_root = tmp_path / "source"
    source_root.mkdir()
    fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/proof_contract_application_probes/context.json"
    original = json.loads(fixture.read_text())
    existing_corr = next(a for a in original["artifacts"] if a["artifactKind"] == "proofir.correspondence")
    proof_slice = existing_corr["payload"]["slice"]
    options = {
        "relation": relation, "anchored_constant": anchored_constant,
        "record_mutator": record_mutator,
        "argument_orders": _choose(argument_orders, (("w", "x"), ("w", "x"))),
        "symbol_names": _choose(symbol_names, ("AppProbe.P", "AppProbe.P")),
    }
    pairs = zip(
        _choose(formula_pairs, (("exists", "forall"), ("forall", "exists"))),
        _choose(contract_pairs, _choose(formula_pairs, (("exists", "forall"), ("forall", "exists")))),
        _choose(contexts, ("object:nat", "object:nat")),
        _choose(permissions, (None, None)),
    )
    artifacts, sides = [], []
    for index, (quantifiers, contract_quantifiers, object_id, allowed) in enumerate(pairs):
        rows, side = _make_side(
            source_root, proof_slice, proof_slice["environment"], index, quantifiers,
            contract_quantifiers, object_id, allowed, options,
        )
        artifacts.extend(rows)
        sides.append(side)
    return {"context": {"artifacts": artifacts}, "sides": sides}


def _choose(value, default):
    return default if value is None else value


def _plan(data, template=TEMPLATE):
    from ladon.proof_contract_probe_artifacts import application_probe_artifact

    artifact = application_probe_artifact(
        data["context"], *data["sides"], template, analysis_id="analysis:witness-red"
    )
    return artifact["payload"]["result"]


def test_profile_registers_witness_dependence_v2():
    from ladon._proof_contract_probe_templates import application_probe_profile

    assert application_probe_profile()["witness-dependence"] == {
        "version": "witness-dependence-v2", "implemented": True,
    }


def test_source_bound_strong_weak_witness_order_preserves_original_goals(tmp_path):
    result = _plan(_source_bound_pair(tmp_path))
    assert result["status"] == "planned"
    assert result["scope"] == "closed-nat-witness-dependence-v2"
    assert [goal["goalId"] for goal in result["goals"]] == ["formal-reading", "probe"]
    from ladon.correspondence_interpretation import lower_formula
    symbols = {"P": {"leanName": "AppProbe.P", "leanType": "Nat → Nat → Prop"}}
    strong = lower_formula(_record_formula(("exists", "forall")), symbols)
    weak = lower_formula(_record_formula(("forall", "exists")), symbols)
    formal, probe = [goal["goal"] for goal in result["goals"]]
    assert weak in formal
    assert weak in probe and strong in probe
    assert "∀" in weak and "∃" in weak and weak.index("∀") < weak.index("∃")
    assert "∃" in strong and "∀" in strong and strong.index("∃") < strong.index("∀")
    assert result["mathematicalFalsity"] == "not-established"


def test_strong_to_weak_direction_is_a_valid_implication_control(tmp_path):
    result = _plan(
        _source_bound_pair(tmp_path),
        {**TEMPLATE, "direction": "left-to-right", "kind": "implication"},
    )
    assert result["status"] == "planned"
    goal = result["goals"][1]["goal"]
    strong = lower_formula_for_test(("exists", "forall"))
    weak = lower_formula_for_test(("forall", "exists"))
    assert goal.startswith(f"({strong}) → ({weak})")


def lower_formula_for_test(quantifiers):
    from ladon.correspondence_interpretation import lower_formula

    return lower_formula(
        _record_formula(quantifiers),
        {"P": {"leanName": "AppProbe.P", "leanType": "Nat → Nat → Prop"}},
    )


def test_source_bound_matching_order_is_a_control(tmp_path):
    data = _source_bound_pair(
        tmp_path, formula_pairs=(("forall", "exists"), ("forall", "exists"))
    )
    planned = _plan(data, {**TEMPLATE, "kind": "implication"})
    assert planned["status"] == "planned"
    assert planned["goals"][1]["goal"].count("∃") == 2
    assert planned["goals"][1]["goal"].count("∀") >= 2


def test_reversed_witness_parameter_arguments_are_unsupported(tmp_path):
    result = _plan(_source_bound_pair(tmp_path, argument_orders=(("w", "x"), ("x", "w"))))
    assert result["status"] == "unsupported"
    assert result["goals"] == []


def test_same_symbol_id_with_different_lean_declarations_is_unsupported(tmp_path):
    result = _plan(_source_bound_pair(tmp_path, symbol_names=("AppProbe.P", "AppProbe.Q")))
    assert result["status"] == "unsupported"
    assert result["goals"] == []


@pytest.mark.parametrize("context_ids", [("object:nat", "object:other")])
def test_contract_context_mismatch_stays_unsupported(tmp_path, context_ids):
    result = _plan(_source_bound_pair(tmp_path, contexts=context_ids))
    assert result["status"] == "unsupported"
    assert result["goals"] == []


def test_contract_order_mismatch_rejects_source_bound_reading(tmp_path):
    data = _source_bound_pair(
        tmp_path,
        formula_pairs=(("exists", "forall"), ("forall", "exists")),
        contract_pairs=(("forall", "exists"), ("forall", "exists")),
    )
    with pytest.raises(ValueError):
        _plan(data)


def test_v1_remains_exact_historical_unsupported_plan(tmp_path):
    result = _plan(_source_bound_pair(tmp_path), LEGACY_TEMPLATE)
    assert result == {
        "schema": "ladon-application-probe-plan-v1",
        "status": "unsupported",
        "template": LEGACY_TEMPLATE,
        "scope": "closed-nat-regularity-v1",
        "goals": [],
        "residuals": [{"code": "unsupported-template-family",
                       "message": "This registered family has no implemented matcher.",
                       "feature": "witness-dependence"}],
        "checkerAuthority": "none",
        "wholeMethodAuthority": "none",
        "sourceFidelity": "attributed-unreviewed",
        "mathematicalFalsity": "not-established",
    }


def test_unknown_version_is_rejected_at_the_public_source_bound_boundary(tmp_path):
    with pytest.raises(ValueError, match="unknown template family or version"):
        _plan(_source_bound_pair(tmp_path), {**TEMPLATE, "version": "witness-dependence-v9"})


def test_witness_permission_conflict_rejects_source_bound_plan(tmp_path):
    data = _source_bound_pair(
        tmp_path,
        formula_pairs=(("forall", "exists"), ("forall", "exists")),
        permissions=([], None),
    )
    with pytest.raises(ValueError):
        _plan(data)


def test_out_of_profile_nat_relation_remains_unsupported(tmp_path):
    result = _plan(_source_bound_pair(tmp_path, relation="eq"))
    assert result["status"] == "unsupported"
    assert result["goals"] == []


def test_malformed_binder_identity_rejects_before_probe_planning(tmp_path):
    def duplicate_identity(record, _index):
        record["formula"]["body"]["binder"]["id"] = "w"

    with pytest.raises(ValueError):
        _source_bound_pair(tmp_path, record_mutator=duplicate_identity)


def test_ast_binder_identity_conflicting_with_contract_rejects(tmp_path):
    def rename_witness(record, index):
        if index != 1:
            return
        # Keep the source AST structurally well formed: rename the actual
        # existential binder and its P argument, while the source contract
        # continues to anchor witnessDependencies at the original id "w".
        exists = record["formula"]["body"]
        assert exists["tag"] == "exists"
        exists["binder"]["id"] = "otherWitness"
        record["formula"]["body"]["body"]["args"][0]["id"] = "otherWitness"

    data = _source_bound_pair(tmp_path, record_mutator=rename_witness)
    with pytest.raises(ValueError):
        _plan(data)


def test_anchored_known_constant_permission_is_outside_witness_profile(tmp_path):
    result = _plan(_source_bound_pair(tmp_path, anchored_constant=True))
    assert result["status"] in {"rejected", "unsupported"}
    assert result["goals"] == []


def test_stale_source_quote_is_rejected_before_planning(tmp_path):
    def stale_quote(record, _index):
        record["source"]["quote"] = "a stale quotation not present in the source file"

    with pytest.raises(ValueError):
        _source_bound_pair(tmp_path, record_mutator=stale_quote)


def test_cross_wired_source_contract_is_rejected_before_planning(tmp_path):
    from ladon.proof_contract_probe_artifacts import application_probe_artifact

    data = _source_bound_pair(tmp_path)
    sides = [dict(side) for side in data["sides"]]
    sides[1]["contractRef"] = data["sides"][0]["contractRef"]
    with pytest.raises((ValueError, TypeError)):
        application_probe_artifact(
            data["context"], *sides, LEGACY_TEMPLATE, analysis_id="analysis:cross-wired"
        )
