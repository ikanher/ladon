"""Red boundary tests for the ordinary refinement workflow and report view."""
from __future__ import annotations

import copy
import hashlib
import json
import time
from pathlib import Path

import pytest

from ladon.entrypoint import main

GOAL = {
    "variables": ["x"],
    "premises": [{"op": "lt", "left": {"var": "x"}, "right": {"rat": 2}}],
    "conclusion": {"op": "eq", "left": {"var": "x"}, "right": {"rat": 0}},
}


def _source(root: Path):
    path = root / "Fixture.lean"
    data = "-- n is a natural number, so n ≥ 0.\ndef predicate (n : Nat) : Prop := n < 2 → n = 0\n"
    path.write_text(data, encoding="utf-8")
    return {
        "profile": "nat-cast-v1",
        "source": {"path": "Fixture.lean", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
        "formalClaim": "Fixture.claim",
        "formalPredicate": "Fixture.predicate",
    }


def _request(root: Path, finding_id="finding-source-1", repair_rationale=None):
    interpretation = _source(root)
    witness = {"id": "w-negative-one", "status": "abstract-countermodel", "assignment": {"x": "-1"}}
    return {
        "schema": "ladon-proof-contract-refinement-request-v1",
        "originalFinding": {
            "id": finding_id,
            "status": "abstract-countermodel",
            "discrepancy": {"kind": "encoded-counterexample", "goal": "x < 2 → x = 0"},
            "witness": copy.deepcopy(witness),
        },
        "baseGoal": copy.deepcopy(GOAL),
        "lift": {"interpretation": interpretation, "mode": "incompatibility", "term": "by omega"},
        "refinementConstraints": [{
            "id": "natural-nonnegative",
            "expression": {"op": "ge", "left": {"var": "x"}, "right": {"rat": 0}},
            "justification": {
                "kind": "source-cited-refinement",
                "source": {"path": "Fixture.lean", "startLine": 1, "endLine": 1,
                           "quote": "-- n is a natural number, so n ≥ 0.",
                           "sha256": interpretation["source"]["sha256"]},
                "nonclaim": "Span validation does not certify formula fidelity.",
            },
        }],
        "repairConstraints": [{
            "id": "claim-repair",
            "expression": {"op": "eq", "left": {"var": "x"}, "right": {"rat": 0}},
            "justification": {"kind": "proposed-repair", "rationale": repair_rationale or "Strengthen the conclusion to match the intended result."},
        }],
    }


def _refine(root, request=None, deadline=None):
    from ladon.proof_contract_refinement_workflow import refine

    deadline = time.monotonic() + 30 if deadline is None else deadline
    return refine(request or _request(root), root, deadline_monotonic=deadline,
                  max_rss_bytes=12 * 1024**3)


def test_refine_uses_only_fresh_public_lift_owner_and_one_shared_deadline(monkeypatch, tmp_path):
    from ladon import proof_contract_lift_check
    from ladon.proof_contract_lift_goals import plan_nat_rational_lift

    request = _request(tmp_path)
    calls = []

    def owner(owned, plan_id, term):
        calls.append((copy.deepcopy(owned), plan_id, term))
        assert owned["deadlineMonotonic"] == pytest.approx(deadline)
        assert owned["limits"]["max_rss_bytes"] == 12 * 1024**3
        return _positive_owner_result(owned, plan_id, request["originalFinding"]["witness"], term=term)

    monkeypatch.setattr(proof_contract_lift_check, "check_nat_rational_lift", owner)
    deadline = time.monotonic() + 30
    result = _refine(tmp_path, request, deadline)

    expected = plan_nat_rational_lift(
        request["baseGoal"], request["originalFinding"]["witness"],
        request["lift"]["interpretation"], mode=request["lift"]["mode"],
    )
    assert len(calls) == 1
    assert calls[0][1:] == (expected["planId"], request["lift"]["term"])
    assert calls[0][0]["goal"] == request["baseGoal"]
    assert calls[0][0]["witness"] == request["originalFinding"]["witness"]
    assert result["request"] == request


def test_completed_workflow_keeps_refinement_and_repair_as_sibling_evidence(monkeypatch, tmp_path):
    from ladon import proof_contract_lift_check
    from ladon.proof_contract_refinement_workflow import refine

    request = _request(tmp_path)
    original = copy.deepcopy(request["originalFinding"])
    monkeypatch.setattr(proof_contract_lift_check, "check_nat_rational_lift",
                        lambda owned, plan_id, term: _positive_owner_result(
                            owned, plan_id, original["witness"], term=term))

    result = refine(request, tmp_path, deadline_monotonic=time.monotonic() + 30,
                    max_rss_bytes=12 * 1024**3)

    assert result["status"] == "completed"
    assert result["originalClaimRefuted"] is False
    assert result["sourceFormulaFidelity"] == "unverified"
    assert result["request"]["originalFinding"] == original
    _assert_sibling_rows(result, original)


def _assert_sibling_rows(result, original):
    rows = {row["kind"]: row for row in result["branches"]}
    assert set(rows) == {"source-cited-refinement", "proposed-repair"}
    for kind, row in rows.items():
        _assert_branch_row(kind, row, original)
    assert rows["source-cited-refinement"]["branch"]["id"] != rows["proposed-repair"]["branch"]["id"]


def _assert_branch_row(kind, row, original):
    assert row["branch"]["originalFinding"] == original
    assert row["branch"]["witness"] == original["witness"]
    assert row["branch"]["branchKind"] == kind
    assert row["check"]["originalClaimRefuted"] is False
    assert row["check"]["witnessCheck"]["status"] == "outside-assumptions"
    assert row["check"]["derivedGoal"]["premises"][:len(GOAL["premises"])] == GOAL["premises"]


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(extraAuthority={"lifted": True}),
    lambda r: r["originalFinding"]["witness"]["assignment"].update(x="0"),
    lambda r: r["refinementConstraints"].append(copy.deepcopy(r["repairConstraints"][0])),
    lambda r: (r["refinementConstraints"].clear(), r["repairConstraints"].clear()),
])
def test_invalid_request_is_rejected_before_public_lift(monkeypatch, tmp_path, mutation):
    from ladon import proof_contract_lift_check
    from ladon.proof_contract_refinement_workflow import refine

    request = _request(tmp_path)
    mutation(request)
    monkeypatch.setattr(proof_contract_lift_check, "check_nat_rational_lift",
                        lambda *_args: pytest.fail("invalid request reached lift owner"))
    with pytest.raises((ValueError, TypeError)):
        refine(request, tmp_path, deadline_monotonic=time.monotonic() + 30,
               max_rss_bytes=12 * 1024**3)


def test_stale_source_quote_or_hash_is_rejected_before_lift(monkeypatch, tmp_path):
    from ladon import proof_contract_lift_check
    from ladon.proof_contract_refinement_workflow import refine

    request = _request(tmp_path)
    request["refinementConstraints"][0]["justification"]["source"]["quote"] = "not present"
    monkeypatch.setattr(proof_contract_lift_check, "check_nat_rational_lift",
                        lambda *_args: pytest.fail("stale citation reached lift owner"))
    with pytest.raises((ValueError, TypeError), match="stale|source|quote|digest|span"):
        refine(request, tmp_path, deadline_monotonic=time.monotonic() + 30,
               max_rss_bytes=12 * 1024**3)


def test_resource_stop_preserves_original_and_does_not_run_branch_checks(monkeypatch, tmp_path):
    from ladon import proof_contract_lift_check, proof_contract_refinement
    from ladon.proof_contract_refinement_workflow import refine

    request = _request(tmp_path)
    original = copy.deepcopy(request["originalFinding"])
    monkeypatch.setattr(proof_contract_lift_check, "check_nat_rational_lift",
                        lambda owned, _plan_id, _term: _incomplete_owner_result(
                            owned, original["witness"]))
    monkeypatch.setattr(proof_contract_refinement, "check_rational_refinement",
                        lambda *_args, **_kwargs: pytest.fail("branch ran after resource stop"))

    result = refine(request, tmp_path, deadline_monotonic=time.monotonic() + 30,
                    max_rss_bytes=12 * 1024**3)

    assert result["status"] == "incomplete"
    assert result["request"]["originalFinding"] == original
    assert result["branches"] == []


def test_inspection_accepts_self_consistent_historical_json_without_lift_authority(tmp_path):
    from ladon.proof_contract_refinement_workflow import inspect_refinement

    request = _request(tmp_path)
    artifact = _historical_artifact(request, tmp_path)
    first = inspect_refinement(artifact, tmp_path)
    assert first["status"] == "validated-historical"
    assert first["leanReplayed"] is False
    assert first["liftAuthority"] == "unverified-saved-result"

    # Keep detached-content identity self-consistent after changing saved
    # evidence. Inspection cannot turn the edited evidence into lift authority.
    forged_native = {"forged": "historical JSON"}
    artifact["liftResult"]["nativeEvidence"] = forged_native
    artifact["liftResult"]["spuriousnessEvidence"] = copy.deepcopy(forged_native)
    _rebind_saved_lift_check(artifact["liftResult"])
    _seal(artifact)
    result = inspect_refinement(artifact, tmp_path)
    assert result["status"] == "validated-historical"
    assert result["leanReplayed"] is False
    assert result["liftAuthority"] == "unverified-saved-result"
    assert result["originalClaimRefuted"] is False
    assert "formalClaimRefuted" not in result
    assert result["artifact"]["liftResult"] == artifact["liftResult"]


def test_inspection_recomputes_branch_witness_and_rejects_stale_source(tmp_path):
    from ladon.proof_contract_refinement_workflow import inspect_refinement

    request = _request(tmp_path)
    artifact = _historical_artifact(request, tmp_path)
    artifact["branches"][0]["branch"]["witness"]["assignment"]["x"] = "0"
    _seal(artifact)
    with pytest.raises((ValueError, TypeError)):
        inspect_refinement(artifact, tmp_path)

    artifact = _historical_artifact(request, tmp_path)
    (tmp_path / "Fixture.lean").write_text("-- changed\n", encoding="utf-8")
    with pytest.raises((ValueError, TypeError, OSError), match="stale|source|digest|citation"):
        inspect_refinement(artifact, tmp_path)


def _historical_artifact(request, root):
    from ladon.proof_contract_lift_goals import plan_nat_rational_lift
    from ladon.proof_contract_refinement import check_rational_refinement, create_refinement_branch
    from ladon.rational_witness import check_witness

    lift_plan = plan_nat_rational_lift(
        request["baseGoal"], request["originalFinding"]["witness"],
        request["lift"]["interpretation"], mode=request["lift"]["mode"],
    )
    witness = request["originalFinding"]["witness"]
    lift_result = _positive_owner_result({
        "repoRoot": str(root.resolve()),
        "goal": request["baseGoal"], "witness": witness,
        "interpretation": request["lift"]["interpretation"], "mode": request["lift"]["mode"],
    }, lift_plan["planId"], witness, term=request["lift"]["term"])
    branches = []
    for kind, constraints in (("source-cited-refinement", request["refinementConstraints"]),
                              ("proposed-repair", request["repairConstraints"])):
        branch = create_refinement_branch(request["originalFinding"], constraints, source_root=root)
        check = check_rational_refinement(
            branch, request["baseGoal"], witness["assignment"], source_root=root,
        )
        branches.append({"kind": kind, "branch": branch, "check": check})
    artifact = {
        "schema": "ladon-proof-contract-refinement-workflow-v1", "request": copy.deepcopy(request),
        "originalCheck": check_witness(request["baseGoal"], witness["assignment"]),
        "liftPlanId": lift_plan["planId"],
        "liftResult": lift_result,
        "branches": branches, "status": "completed", "sourceFormulaFidelity": "unverified",
        "originalClaimRefuted": False,
    }
    _seal(artifact)
    return artifact


def _positive_owner_result(owned, plan_id, witness, *, term):
    import hashlib
    from pathlib import Path

    from ladon.proof_contract_lift_check import _result
    from ladon.proof_contract_lift_goals import plan_nat_rational_lift
    from ladon.proof_contract_lift_worker import _checker_identity

    plan = plan_nat_rational_lift(
        owned["goal"], witness, owned["interpretation"], mode=owned["mode"]
    )
    assert plan["planId"] == plan_id
    root = Path(owned["repoRoot"]).resolve()
    source = owned["interpretation"]["source"]
    native_evidence = {"environmentRef": "sha256:" + "1" * 64,
                       "completion": {"axioms": [], "sorry": False}, "fixture": "checked"}
    binding = {
        "attemptId": "a" * 32, "checkerIdentity": _checker_identity(),
        "planId": plan_id, "goal": owned["goal"], "witness": plan["witness"],
        "interpretation": owned["interpretation"], "mode": owned["mode"],
        "termDigest": "sha256:" + hashlib.sha256(term.encode()).hexdigest(),
        "root": str(root), "source": source,
        "sourceDigest": "sha256:" + hashlib.sha256((root / source["path"]).read_bytes()).hexdigest(),
    }
    result = _result("spurious-countermodel", plan, witness, None)
    result.update({"sourceVerified": True, "formalClaimRefuted": False,
                   "spuriousnessEvidence": native_evidence,
                   "nativeEvidence": native_evidence,
                   "binding": binding})
    _rebind_saved_lift_check(result)
    return result


def _incomplete_owner_result(owned, witness):
    from ladon.proof_contract_lift_check import _result
    from ladon.proof_contract_lift_goals import plan_nat_rational_lift

    plan = plan_nat_rational_lift(
        owned["goal"], witness, owned["interpretation"], mode=owned["mode"]
    )
    return _result("incomplete", plan, witness, "deadline-exhausted", code="timeout")


def _rebind_saved_lift_check(lift_result):
    from ladon.proof_contract_lift_check import _digest

    raw_native = {"status": "completed", "planId": lift_result["planId"],
                  "witness": lift_result["witness"], "binding": lift_result["binding"],
                  "nativeEvidence": lift_result["nativeEvidence"]}
    lift_result["checkId"] = _digest(json.dumps(
        raw_native, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode())


def _seal(artifact):
    payload = {key: value for key, value in artifact.items() if key != "artifactId"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    artifact["artifactId"] = "sha256:" + hashlib.sha256(encoded).hexdigest()


def test_cli_refine_collision_and_exit_code_for_noncompleted(monkeypatch, tmp_path, capsys):
    from ladon import proof_contract_lift_check

    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(_request(tmp_path)), encoding="utf-8")
    output = tmp_path / "result.json"
    output.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(proof_contract_lift_check, "check_nat_rational_lift",
                        lambda *_args: pytest.fail("colliding output reached lift owner"))
    assert main(["investigation", "contract", "refine", "--input", str(request_path),
                 "--root", str(tmp_path), "--output", str(output)]) == 2
    assert output.read_text(encoding="utf-8") == "keep"
    response = capsys.readouterr().out
    assert response


def test_report_refinement_supplement_must_bind_one_existing_finding(tmp_path):
    from test_investigation_findings import observation_case

    from ladon.investigation_reporting import aggregate_report

    _base, plan = observation_case(tmp_path)
    artifact = _historical_artifact(_request(tmp_path), tmp_path)
    with pytest.raises((ValueError, TypeError), match="finding|identity|bound"):
        aggregate_report([plan], tmp_path, refinements=[artifact])


def test_report_supplement_preserves_original_finding_branches_and_plan(tmp_path):
    from test_investigation_findings import NOW, observation_case, review_observation

    from ladon.investigation_reporting import aggregate_report

    _base, plan = observation_case(tmp_path)
    reviewed, _packet, _response = review_observation(plan, tmp_path)
    base_report = aggregate_report([reviewed], tmp_path, now=NOW)
    finding_id = base_report["findings"][0]["findingId"]
    base_finding = next(row for row in base_report["findings"] if row["findingId"] == finding_id)
    artifact = _historical_artifact(_request(tmp_path, finding_id=finding_id), tmp_path)
    preserved_plan = copy.deepcopy(reviewed)

    report = aggregate_report([reviewed], tmp_path, now=NOW, refinements=[artifact])

    _assert_report_preserves(report, artifact, finding_id, base_finding, base_report)
    _assert_historical_report(report, finding_id)
    assert reviewed == preserved_plan


def _assert_report_preserves(report, artifact, finding_id, base_finding, base_report):
    assert report["schema"] == "ladon-investigation-report-v3"
    finding = next(row for row in report["findings"] if row["findingId"] == finding_id)
    assert finding["refinementIds"] == [artifact["artifactId"]]
    assert {key: value for key, value in finding.items() if key != "refinementIds"} == base_finding
    assert report["branches"] == base_report["branches"]
    assert report["observations"] == base_report["observations"]


def _assert_historical_report(report, finding_id):
    inspection = report["refinementEvidence"][0]
    assert inspection["status"] == "validated-historical"
    assert inspection["leanReplayed"] is False
    assert inspection["artifact"]["request"]["originalFinding"]["id"] == finding_id
    assert len(inspection["artifact"]["branches"]) == 2
    assert [row["kind"] for row in inspection["artifact"]["branches"]] == [
        "source-cited-refinement", "proposed-repair",
    ]
    assert report["mathematicalFalsity"] == "not-established"
    assert "id-only-attributed" in report["authority"]


def test_cli_report_accepts_repeatable_refinement_supplements(tmp_path, capsys):
    from test_investigation_findings import observation_case, review_observation

    from ladon.investigation_reporting import aggregate_report

    _base, plan = observation_case(tmp_path)
    reviewed, _packet, _response = review_observation(plan, tmp_path)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(reviewed), encoding="utf-8")
    finding_id = aggregate_report([reviewed], tmp_path)["findings"][0]["findingId"]
    first = _historical_artifact(_request(tmp_path, finding_id, "Repair rationale A."), tmp_path)
    second = _historical_artifact(_request(tmp_path, finding_id, "Repair rationale B."), tmp_path)
    first_path, second_path = tmp_path / "refinement-a.json", tmp_path / "refinement-b.json"
    first_path.write_text(json.dumps(first), encoding="utf-8")
    second_path.write_text(json.dumps(second), encoding="utf-8")

    result = main(["investigation", "report", "--plan", str(plan_path), "--root", str(tmp_path),
                   "--refinement", str(first_path), "--refinement", str(second_path)])

    assert result == 0
    report = json.loads(capsys.readouterr().out)
    assert report["schema"] == "ladon-investigation-report-v3"
    finding = next(row for row in report["findings"] if row["findingId"] == finding_id)
    assert finding["refinementIds"] == [first["artifactId"], second["artifactId"]]
