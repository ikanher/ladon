"""Fresh Real comparison requires a separate exact live relation check."""

import copy
import json

import pytest
from test_real_bound_native_records import FIXTURE


def production():
    from ladon.real_bound_native_production import recorded_production

    fixture = json.loads(FIXTURE.read_text())
    terms = {row["goal"]["id"]: row["term"] for row in fixture["check"]["result"]["checks"]}
    return recorded_production(fixture["plan"], terms, fixture["check"], fixture["sourceText"])


def install_fresh_replay(monkeypatch, transform=lambda value: value):
    import ladon.real_bound_native_analysis as analysis

    seen = []

    def replay(value, root, *, timeout_seconds):
        seen.append((value, root, timeout_seconds))
        result = copy.deepcopy(transform(value))
        result["authority"] = "fresh-lean-check"
        return result

    monkeypatch.setattr(analysis, "replay_real_bound", replay)
    return seen


def install_relation_checks(monkeypatch, statuses=("checked",)):
    import ladon.real_bound_native_analysis as analysis

    seen = []

    def check(root, left_plan, right_plan, *, timeout_seconds):
        index = len(seen)
        seen.append((root, left_plan, right_plan, timeout_seconds))
        status = statuses[min(index, len(statuses) - 1)]
        return {"status": "completed", "processReceipt": {"returnCode": 0}, "result": {
            "status": status,
            "leftPlanId": left_plan["planId"],
            "rightPlanId": right_plan["planId"],
            "checkerIdentity": "sha256:checker",
            "goal": {"sha256": f"sha256:goal-{index}"},
            "check": {"status": "supported"},
            "residual": None if status == "checked" else "real-relation-lean-check-unaccepted",
        }}

    monkeypatch.setattr(analysis, "check_real_bound_relation", check)
    return seen


def mutate_record(production_value, path, value):
    node = production_value["artifacts"][-1]["payload"]["record"]
    for part in path[:-1]:
        node = node[part]
    node[path[-1]] = value


def test_same_exact_context_resolves_only_with_a_checked_relation(monkeypatch):
    from ladon.real_bound_native_analysis import compare_real_bounds

    left, right = production(), production()
    seen = install_fresh_replay(monkeypatch)
    relations = install_relation_checks(monkeypatch)
    result = compare_real_bounds(left, right, "/source", timeout_seconds=17)

    assert result["status"] == "resolved"
    assert result["relation"] == "equivalent"
    assert result["contextMatch"] is True
    assert result["residuals"] == []
    assert len(seen) == 2
    assert all(row[1] == "/source" and 0 < row[2] <= 17 for row in seen)
    assert len(relations) == 1
    assert relations[0][0] == "/source"
    assert 0 < relations[0][3] <= 17
    assert result["relationCheckEvidence"]["goalDigest"] == "sha256:goal-0"
    assert len(result["freshCheckEvidence"]) == 4
    assert "checkRunRefs" not in result  # saved native refs are historical
    assert result["sourceTheoremProof"] == "not-checked"
    assert result["paperNormBridge"] == "unresolved"


def test_unaccepted_live_relation_check_never_promotes_context_equality(monkeypatch):
    from ladon.real_bound_native_analysis import compare_real_bounds

    left, right = production(), production()
    install_fresh_replay(monkeypatch)
    install_relation_checks(monkeypatch, ("unresolved",))

    result = compare_real_bounds(left, right, "/source")

    assert result["contextMatch"] is True
    assert result["status"] == "unresolved"
    assert result["relation"] is None
    assert result["residuals"] == [{"code": "real-relation-lean-check-unaccepted"}]


def test_resource_limited_relation_worker_is_not_promoted(monkeypatch):
    import ladon.real_bound_native_analysis as analysis

    left, right = production(), production()
    install_fresh_replay(monkeypatch)
    install_relation_checks(monkeypatch)
    checked_run = analysis.check_real_bound_relation

    def limited(*args, **kwargs):
        run = checked_run(*args, **kwargs)
        run["processReceipt"]["memoryLimited"] = True
        return run

    monkeypatch.setattr(analysis, "check_real_bound_relation", limited)
    result = analysis.compare_real_bounds(left, right, "/source")

    assert result["status"] == "unresolved"
    assert result["relation"] is None


@pytest.mark.parametrize(
    "path,value",
    [
        (("endpointId",), "endpoint:other"),
        (("application", "input", "setRef"),
         {"kind": "expression", "localId": "expr:eb73c2b2e404b23b14d6b27d15a6c2136938d4ee0e4f5c1688888442b49d3ff9"}),
        (("application", "output", "boundRef"),
         {"kind": "expression", "localId": "expr:72b35baad9a3d80074dc2b25891c2975d8a8df571bca4288ef6c5230081966b1"}),
        (("constant", "permittedBinderIds"), []),
        (("guards", "boundNonnegativeBinderId"), "b0"),
        (("interpretation",), {"kind": "prefix-family-v1", "measure":
          {"declaration": "Other.measure", "arguments": []}}),
    ],
)
def test_changed_endpoint_set_parameter_scope_guard_or_norm_stays_unresolved(
    monkeypatch, path, value
):
    from ladon.real_bound_native_analysis import compare_real_bounds

    left, right = production(), production()
    mutate_record(right, path, value)
    install_fresh_replay(monkeypatch)
    relations = install_relation_checks(monkeypatch)

    result = compare_real_bounds(left, right, "/source")

    assert result["status"] == "unresolved"
    assert result["relation"] is None
    assert result["residuals"] == [{"code": "real-bound-context-mismatch"}]
    assert result["paperNormBridge"] == "unresolved"
    assert relations == []


def test_historical_claim_without_fresh_replay_result_is_rejected(monkeypatch):
    import ladon.real_bound_native_analysis as analysis

    saved = production()
    monkeypatch.setattr(analysis, "replay_real_bound", lambda *_args, **_kwargs: saved)

    with pytest.raises(ValueError, match="fresh admitted"):
        analysis.compare_real_bounds(saved, production(), "/source")


def test_identity_propagation_checks_each_edge_independently(monkeypatch):
    from ladon.real_bound_native_analysis import propagate_real_bound_identity

    values = [production(), production(), production()]
    seen = install_fresh_replay(monkeypatch)
    relations = install_relation_checks(monkeypatch, ("checked", "unresolved"))

    result = propagate_real_bound_identity(values, "/source")

    assert result["status"] == "unresolved"
    assert result["complete"] is False
    assert [row["ruleCandidate"] for row in result["candidateEdges"]] == ["identity-v1", "identity-v1"]
    assert [row["status"] for row in result["candidateEdges"]] == ["resolved", "unresolved"]
    assert result["candidateEdges"][0]["rule"] == "identity-v1"
    assert result["candidateEdges"][0]["ruleApplication"]["goalDigest"] == "sha256:goal-0"
    assert all(row["comparisonDiagnostic"]["contextMatch"]
               for row in result["candidateEdges"])
    assert len(seen) == len(values)
    assert len(relations) == 2


def test_identity_propagation_completes_only_after_every_edge_checks(monkeypatch):
    from ladon.real_bound_native_analysis import propagate_real_bound_identity

    values = [production(), production(), production()]
    install_fresh_replay(monkeypatch)
    relations = install_relation_checks(monkeypatch, ("checked",))

    result = propagate_real_bound_identity(values, "/source")

    assert result["status"] == "resolved"
    assert result["complete"] is True
    assert [row["status"] for row in result["candidateEdges"]] == ["resolved", "resolved"]
    assert len(relations) == 2


def test_identity_propagation_stops_at_changed_context(monkeypatch):
    from ladon.real_bound_native_analysis import propagate_real_bound_identity

    values = [production(), production(), production()]
    mutate_record(values[2], ("application", "input", "setRef"),
                  {"kind": "expression", "localId": "expr:eb73c2b2e404b23b14d6b27d15a6c2136938d4ee0e4f5c1688888442b49d3ff9"})
    install_fresh_replay(monkeypatch)
    relations = install_relation_checks(monkeypatch)

    result = propagate_real_bound_identity(values, "/source")

    assert result["status"] == "unresolved"
    assert result["complete"] is False
    assert result["candidateEdges"][0]["comparisonDiagnostic"]["contextMatch"] is True
    assert result["candidateEdges"][1]["comparisonDiagnostic"]["contextMatch"] is False
    assert len(relations) == 1


def test_singleton_cannot_claim_complete_propagation(monkeypatch):
    from ladon.real_bound_native_analysis import propagate_real_bound_identity

    install_fresh_replay(monkeypatch)
    with pytest.raises(ValueError, match="2 to 128"):
        propagate_real_bound_identity([production()], "/source")
