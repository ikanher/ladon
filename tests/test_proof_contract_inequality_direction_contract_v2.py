"""Source-bound acceptance tests for inequality-direction-v2."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

TEMPLATE = {
    "familyId": "inequality-direction",
    "version": "inequality-direction-v2",
    "direction": "right-to-left",
    "kind": "counterexample",
}
LEGACY = {**TEMPLATE, "version": "inequality-direction-v1"}


def _record(root, name, reversed_order):
    quote = ("For every natural x, x is at most zero." if reversed_order
             else "For every natural x, zero is at most x.")
    (root / f"{name}.txt").write_text(quote + "\n", encoding="utf-8")
    x = {"id": "x", "name": "x", "domain": "Nat"}
    left = {"tag": "var", "id": "x"} if reversed_order else {"tag": "const", "name": "0"}
    right = {"tag": "const", "name": "0"} if reversed_order else {"tag": "var", "id": "x"}
    return {
        "id": name,
        "source": {
            "path": f"{name}.txt", "startLine": 1, "endLine": 1, "quote": quote,
            "sha256": hashlib.sha256((quote + "\n").encode()).hexdigest(),
        },
        "formula": {"tag": "forall", "binder": x,
                    "body": {"tag": "le", "left": left, "right": right}},
        "symbols": {},
    }


def _pair(tmp_path, *, left_reversed=True, mutation=None, context_ids=None, endpoints=None):
    from ladon.correspondence_check import prepare_correspondence
    from ladon.proof_contract_artifacts import source_contract_artifact
    from ladon.proofir_correspondence import (
        bind_native_interpretation,
        correspondence_artifacts,
        interpretation_artifacts,
    )

    root = tmp_path / "source"
    root.mkdir(parents=True, exist_ok=True)
    fixture = (Path(__file__).resolve().parents[1]
               / "tests/fixtures/proof_contract_application_probes/context.json")
    original = json.loads(fixture.read_text())
    proof_slice = next(a for a in original["artifacts"]
                       if a["artifactKind"] == "proofir.correspondence")["payload"]["slice"]
    artifacts, sides = [], []
    for index, reversed_order in enumerate((left_reversed, not left_reversed)):
        record = _record(root, f"reading-{index}", reversed_order)
        if mutation:
            mutation(record, index)
        source_map, interpretation = interpretation_artifacts(
            record, proof_slice["environment"], source_root=root)
        endpoint = endpoints[index] if endpoints else "relation:Nat.le"
        context_id = context_ids[index] if context_ids else "object:nat-order"
        contract = {
            "profileId": "norm-scale-v1", "endpointId": endpoint,
            "context": {"objectId": context_id, "domainId": "domain:Nat",
                        "scaleId": "scale:none", "representationId": "representation:original"},
            "telescope": [{"binderId": "x", "typeId": "Nat", "quantifier": "forall"}],
            "assumptions": [], "conclusionId": endpoint,
            "features": {
                "regularity": {"state": "unknown", "scaleId": "scale:none", "offset": None,
                               "reason": "not modeled by inequality-direction profile"},
                "constantDependencies": {"state": "unknown", "allowedBinderIds": None,
                                         "reason": "not modeled by inequality-direction profile"},
                "witnessDependencies": [],
            },
        }
        owner = source_contract_artifact(
            contract, contract_id=f"contract:reading-{index}",
            environment_ref=proof_slice["environment"],
            source_map_refs=[{"artifactRef": source_map["artifactId"], "kind": "source-map",
                              "localId": source_map["payload"]["sourceMapId"]}],
            residuals=[{"code": "profile-feature-omitted",
                        "message": "Other mathematical features are outside this profile.",
                        "feature": "inequality-direction-v2"}],
        )
        prepared = prepare_correspondence(record, proof_slice, {})
        prepared = bind_native_interpretation(prepared, [source_map, interpretation], source_root=root)
        correspondence = correspondence_artifacts(prepared)
        artifacts.extend([source_map, interpretation, owner, correspondence])
        sides.append({
            "contractRef": {"artifactRef": owner["artifactId"], "kind": "contract",
                            "localId": owner["payload"]["contractId"]},
            "correspondenceRef": {"artifactRef": correspondence["artifactId"],
                                  "kind": "correspondence",
                                  "localId": correspondence["payload"]["correspondenceId"]},
        })
    return {"artifacts": artifacts}, sides


def _plan(data, template=TEMPLATE):
    from ladon.proof_contract_probe_artifacts import application_probe_artifact

    context, sides = data
    return application_probe_artifact(
        context, *sides, template, analysis_id="analysis:inequality-direction"
    )["payload"]["result"]


def _template_result(data, template=TEMPLATE, shared_slice=None, *, contract_mutation=None):
    from ladon._proof_contract_probe_pair import resolve_pair
    from ladon._proof_contract_probe_templates import template_result

    context, sides = data
    left, right = resolve_pair(context["artifacts"], *sides)
    left_contract = copy.deepcopy(left["contract"]["payload"]["record"])
    if contract_mutation:
        contract_mutation(left_contract)
    selected_slice = shared_slice or left["correspondence"]["payload"]["slice"]
    return template_result(
        left["reading"]["payload"]["record"], right["reading"]["payload"]["record"],
        left_contract, right["contract"]["payload"]["record"], selected_slice, template,
    )


def test_profile_plan_and_v1_compatibility(tmp_path):
    from ladon._proof_contract_probe_templates import application_probe_profile

    assert application_probe_profile()["inequality-direction"] == {
        "version": "inequality-direction-v2", "implemented": True,
    }
    result = _plan(_pair(tmp_path))
    assert result["status"] == "planned"
    assert result["scope"] == "closed-nat-zero-inequality-direction-v2"
    assert [g["goalId"] for g in result["goals"]] == ["formal-reading", "probe"]
    assert "v0 ≤ 0" in result["goals"][1]["goal"]
    assert "0 ≤ v0" in result["goals"][1]["goal"]
    assert result["goals"][0]["status"] == result["goals"][1]["status"] == "open"
    assert result["checkerAuthority"] == result["wholeMethodAuthority"] == "none"
    legacy = _plan(_pair(tmp_path / "legacy"), LEGACY)
    assert legacy["status"] == "unsupported" and legacy["goals"] == []


def test_valid_nat_direction_implication_control_and_selected_direction(tmp_path):
    result = _plan(_pair(tmp_path),
                   {**TEMPLATE, "direction": "left-to-right", "kind": "implication"})
    assert result["status"] == "planned"
    goal = result["goals"][1]["goal"]
    assert goal.index("v0 ≤ 0") < goal.rindex("0 ≤ v0")
    reverse = _plan(_pair(tmp_path / "reverse"),
                    {**TEMPLATE, "direction": "right-to-left", "kind": "implication"})
    assert reverse["status"] == "planned"
    reverse_goal = reverse["goals"][1]["goal"]
    assert reverse_goal.index("0 ≤ v0") < reverse_goal.rindex("v0 ≤ 0")


@pytest.mark.parametrize("mutation", [
    lambda record, index: record["formula"]["body"]["right"].update(name="1") if index == 0 else None,
    lambda record, index: record["formula"]["body"].update(tag="lt") if index == 0 else None,
    lambda record, index: record["formula"]["binder"].update(domain="Int") if index == 0 else None,
    lambda record, index: record["formula"]["body"].update(
        left={"tag": "app", "symbol": "f", "args": [{"tag": "var", "id": "x"}]}
    ) if index == 0 else None,
    lambda record, index: record["formula"]["binder"].update(id="y") if index == 1 else None,
])
def test_nearby_ast_shapes_do_not_plan(tmp_path, mutation):
    def mutate_record(record, index):
        mutation(record, index)

    try:
        result = _plan(_pair(tmp_path, mutation=mutate_record))
    except (ValueError, TypeError):
        return
    assert result["status"] in {"unsupported", "rejected"}
    assert result["goals"] == []


def test_native_contract_identity_assumption_and_feature_drift_stay_unsupported(tmp_path):
    result = _plan(_pair(tmp_path, context_ids=("object:nat-order", "object:other")))
    assert result["status"] == "unsupported" and result["goals"] == []
    result = _plan(_pair(tmp_path / "endpoint", endpoints=("relation:Other", "relation:Other")))
    assert result["status"] == "unsupported" and result["goals"] == []
    data = _pair(tmp_path / "contract")
    result = _template_result(
        data, contract_mutation=lambda contract: contract["assumptions"].append(
            {"predicateId": "assumption:h"}
        ),
    )
    assert result["status"] == "unsupported" and result["goals"] == []


@pytest.mark.parametrize("bad_slice", [
    {"localContext": ["h"], "complete": True, "status": "extracted",
     "nodes": [{"kind": "application", "premises": [], "closedType": "∀ (x : Nat), 0 ≤ x"}]},
    {"localContext": [], "complete": True, "status": "extracted",
     "nodes": [{"kind": "application", "premises": ["h"], "closedType": "∀ (x : Nat), 0 ≤ x"}]},
    {"localContext": [], "complete": True, "status": "extracted",
     "nodes": [{"kind": "application", "premises": [], "closedType": "∀ (x : Nat), 0 ≤ x"},
               {"kind": "application", "premises": [], "closedType": "∀ (x : Nat), 0 ≤ x"}]},
])
def test_shared_application_must_be_one_closed_premisefree_node(tmp_path, bad_slice):
    result = _template_result(_pair(tmp_path), shared_slice=bad_slice)
    assert result["status"] == "unsupported" and result["goals"] == []
