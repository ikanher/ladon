"""Source-bound acceptance tests for the exact restricted-domain-v2 fragment."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

TEMPLATE = {
    "familyId": "restricted-domain",
    "version": "restricted-domain-v2",
    "direction": "left-to-right",
    "kind": "counterexample",
}
LEGACY = {**TEMPLATE, "version": "restricted-domain-v1"}


def _record(root, name, restricted, *, predicate="P", domain="Nat", bound=0):
    quote = ("For every x, if x is at most zero then P(x)." if restricted
             else "For every x, P(x).")
    (root / f"{name}.txt").write_text(quote + "\n", encoding="utf-8")
    x = {"id": "x", "name": "x", "domain": domain}
    body = {"tag": "app", "symbol": predicate,
            "args": [{"tag": "var", "id": "x"}]}
    if restricted:
        body = {"tag": "implies",
                "premise": {"tag": "le", "left": {"tag": "var", "id": "x"},
                            "right": {"tag": "const", "name": str(bound)}},
                "conclusion": body}
    return {
        "id": name,
        "source": {"path": f"{name}.txt", "startLine": 1, "endLine": 1,
                   "quote": quote, "sha256": hashlib.sha256((quote + "\n").encode()).hexdigest()},
        "formula": {"tag": "forall", "binder": x, "body": body},
        "symbols": {predicate: {"leanName": "AppProbe.P", "leanType": "Nat → Prop"}},
    }


def _pair(tmp_path, *, restricted_first=True, mutation=None, contexts=None,
          symbol_names=None, symbol_types=None, endpoints=None):
    from ladon.correspondence_check import prepare_correspondence
    from ladon.proof_contract_artifacts import source_contract_artifact
    from ladon.proofir_correspondence import (
        bind_native_interpretation,
        correspondence_artifacts,
        interpretation_artifacts,
    )

    root = tmp_path / "source"
    root.mkdir(parents=True)
    fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/proof_contract_application_probes/context.json"
    original = json.loads(fixture.read_text())
    proof_slice = next(a for a in original["artifacts"]
                       if a["artifactKind"] == "proofir.correspondence")["payload"]["slice"]
    artifacts, sides = [], []
    for index, restricted in enumerate((restricted_first, not restricted_first)):
        record = _record(root, f"reading-{index}", restricted)
        if symbol_names:
            record["symbols"]["P"]["leanName"] = symbol_names[index]
        if symbol_types:
            record["symbols"]["P"]["leanType"] = symbol_types[index]
        if mutation:
            mutation(record, index)
        source_map, interpretation = interpretation_artifacts(
            record, proof_slice["environment"], source_root=root)
        contract = {
            "profileId": "norm-scale-v1", "endpointId": endpoints[index] if endpoints else "predicate:P",
            "context": {"objectId": contexts[index] if contexts else "object:nat", "domainId": "domain:Nat",
                        "scaleId": "scale:none", "representationId": "representation:original"},
            "telescope": [{"binderId": "x", "typeId": "Nat", "quantifier": "forall"}],
            "assumptions": [], "conclusionId": endpoints[index] if endpoints else "predicate:P",
            "features": {
                "regularity": {"state": "unknown", "scaleId": "scale:none", "offset": None,
                               "reason": "not modeled by restricted-domain profile"},
                "constantDependencies": {"state": "unknown", "allowedBinderIds": None,
                                         "reason": "not modeled by restricted-domain profile"},
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
                        "feature": "restricted-domain-v2"}],
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
    artifact = application_probe_artifact(
        context, *sides, template, analysis_id="analysis:restricted-domain"
    )
    return artifact["payload"]["result"]


def test_profile_and_source_bound_restricted_domain_goals(tmp_path):
    from ladon._proof_contract_probe_templates import application_probe_profile

    assert application_probe_profile()["restricted-domain"] == {
        "version": "restricted-domain-v2", "implemented": True,
    }
    result = _plan(_pair(tmp_path))
    assert result["status"] == "planned"
    assert result["scope"] == "closed-nat-zero-restricted-domain-v2"
    assert [goal["goalId"] for goal in result["goals"]] == ["formal-reading", "probe"]
    assert "v0 ≤ 0" in result["goals"][1]["goal"]
    assert "∧ ¬" in result["goals"][1]["goal"]
    assert result["mathematicalFalsity"] == "not-established"


def test_unrestricted_to_restricted_is_the_valid_implication_control(tmp_path):
    result = _plan(_pair(tmp_path, restricted_first=False),
                   {**TEMPLATE, "direction": "left-to-right", "kind": "implication"})
    assert result["status"] == "planned"
    goal = result["goals"][1]["goal"]
    assert "(∀ (v0 : Nat), ((_root_.AppProbe.P" in goal
    assert goal.index("AppProbe.P") < goal.rindex("v0 ≤ 0")


@pytest.mark.parametrize("mutation", [
    lambda body: body["premise"]["right"].update(name="1"),
    lambda body: body["premise"].update(tag="lt"),
    lambda body: body["premise"]["left"].update(id="other"),
    lambda body: body["premise"].update(left={"tag": "const", "name": "0"},
                                         right={"tag": "var", "id": "x"}),
])
def test_nearby_guard_shapes_stay_unsupported(tmp_path, mutation):
    def mutate(record, index):
        if index == 0:
            mutation(record["formula"]["body"])
    try:
        result = _plan(_pair(tmp_path, mutation=mutate))
    except ValueError:
        return  # malformed binder references are rejected during source validation
    assert result["status"] in {"unsupported", "rejected"}
    assert result["goals"] == []


def test_different_symbol_types_and_contract_contexts_stay_unsupported(tmp_path):
    result = _plan(_pair(tmp_path, symbol_types=("Nat → Prop", "Nat → Nat")))
    assert result["status"] == "unsupported"
    assert result["goals"] == []
    result = _plan(_pair(tmp_path / "endpoint", endpoints=("predicate:Other", "predicate:Other")))
    assert result["status"] == "unsupported"
    assert result["goals"] == []
    result = _plan(_pair(tmp_path / "symbol", symbol_names=("DomainProbe.P", "DomainProbe.Q")))
    assert result["status"] == "unsupported"
    assert result["goals"] == []
    result = _plan(_pair(tmp_path / "context", contexts=("object:nat", "object:other")))
    assert result["status"] == "unsupported"
    assert result["goals"] == []


@pytest.mark.parametrize("object_map", [{}, {"unsupported": True}])
def test_early_native_pair_rejections_report_the_domain_profile_scope(monkeypatch, object_map):
    import ladon._proof_contract_probe_pair as pair_module

    rows = [
        {"correspondence": {"payload": {"slice": {"id": index}, "objectMap": object_map}}}
        for index in range(2)
    ]
    rows[1]["correspondence"]["payload"]["slice"] = (
        {"id": 0} if object_map else {"id": "different"})
    monkeypatch.setattr(pair_module, "resolve_pair", lambda *_args: rows)
    result = pair_module.derive_probe_result([], {}, {}, TEMPLATE)
    assert result["status"] == "unsupported"
    assert result["scope"] == "closed-nat-zero-restricted-domain-v2"


def test_both_source_order_permutations_preserve_original_formal_reading(tmp_path):
    for restricted_first in (True, False):
        result = _plan(_pair(tmp_path / str(restricted_first), restricted_first=restricted_first))
        assert result["status"] == "planned"
        formal = result["goals"][0]["goal"]
        assert " ↔ " in formal
        probe = result["goals"][1]["goal"]
        assert "≤ 0" in probe
        assert probe.count("AppProbe.P") == 2


def test_v1_restricted_domain_keeps_historical_unsupported_behavior(tmp_path):
    result = _plan(_pair(tmp_path), LEGACY)
    assert result == {
        "schema": "ladon-application-probe-plan-v1", "status": "unsupported",
        "template": LEGACY, "scope": "closed-nat-regularity-v1", "goals": [],
        "residuals": [{"code": "unsupported-template-family",
                       "message": "This registered family has no implemented matcher.",
                       "feature": "restricted-domain"}],
        "checkerAuthority": "none", "wholeMethodAuthority": "none",
        "sourceFidelity": "attributed-unreviewed", "mathematicalFalsity": "not-established",
    }


@pytest.mark.parametrize(("version", "scope"), [
    ("restricted-domain-v2", "closed-nat-zero-restricted-domain-v2"),
    ("restricted-domain-v1", "closed-nat-regularity-v1"),
])
def test_early_native_pair_rejection_uses_the_selected_template_scope(version, scope):
    from ladon._proof_contract_probe_pair import unsupported_result

    template = {**TEMPLATE, "version": version}
    result = unsupported_result(template, "different-application-context", "test")
    assert result["status"] == "unsupported"
    assert result["scope"] == scope
    assert result["goals"] == []
