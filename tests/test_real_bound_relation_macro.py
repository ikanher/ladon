"""Lean constructs Real-bound comparison propositions from live declarations."""

import json
import os
import shutil
import time
from pathlib import Path

import pytest

from ladon.derivative_prefix import plan_derivative_prefix
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_native_plan import plan_real_bound
from ladon.real_bound_observation import observe_bound_snapshot
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.semantic_lean_execution import prepare_direct_lean_execution

SOURCES = Path(__file__).parents[1] / "src/ladon/lean"


@pytest.fixture(scope="module")
def relation_project(tmp_path_factory):
    selected = os.environ.get("LADON_MATHLIB_TEST_ROOT")
    if selected is None:
        pytest.skip("set LADON_MATHLIB_TEST_ROOT to an existing compiled Mathlib project")
    chosen = Path(selected).resolve(strict=True)
    context = pinned_toolchain(chosen)
    root = tmp_path_factory.mktemp("real-bound-relation")
    (root / "lean-toolchain").write_bytes((chosen / "lean-toolchain").read_bytes())
    (root / ".lake/build/lib/lean").mkdir(parents=True)
    for index, library in enumerate(context.library_roots):
        target = root / f".lake/packages/import{index}/.lake/build/lib/lean"
        target.parent.mkdir(parents=True)
        target.symlink_to(library, target_is_directory=True)
    worker_root = root.parent / f"{root.name}-worker"
    worker_root.mkdir()
    (worker_root / "lean-toolchain").write_bytes((chosen / "lean-toolchain").read_bytes())
    (worker_root / ".lake/build/lib/lean").mkdir(parents=True)
    for index, library in enumerate(context.library_roots):
        target = worker_root / f".lake/packages/import{index}/.lake/build/lib/lean"
        target.parent.mkdir(parents=True)
        target.symlink_to(library, target_is_directory=True)
    (worker_root / "ScalarExamples.lean").write_text(source_with_alias())
    deadline = time.monotonic() + 600
    for name in ("LadonRealBound", "LadonRealBoundBinding"):
        shutil.copy2(SOURCES / f"{name}.lean", root / f"{name}.lean")
        execution = prepare_direct_lean_execution(
            root, None, pinned_toolchain(root), require_compiled_module=False
        )
        result = run_bounded_target_process(
            [*execution.command, "-o", f".lake/build/lib/lean/{name}.olean", f"{name}.lean"],
            cwd=root,
            env=execution.environment,
            timeout_seconds=min(60, deadline - time.monotonic()),
            max_output_bytes=8 * 1024**2,
            max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
        )
        assert result.succeeded, result.stdout + result.stderr
    (root / "ScalarExamples.lean").write_text(source_with_alias())
    return root, deadline, worker_root


def source_with_alias():
    source = (Path(__file__).parent / "fixtures/real_bound_native/ScalarExamples.lean").read_text()
    alias = (
        "theorem ordinaryCopy (n : Nat) : ∃ K : Real, 0 ≤ K ∧ "
        "∀ (f : Real × Real → Real) (S : Set Real) (C : Real), 0 ≤ C → "
        "envelope f S n C → envelope (transport f) S n (K * C) := ordinary n\n"
        "def impossibleEnvelope (_f : Real × Real → Real) (_S : Set Real) "
        "(_n : Nat) (_C : Real) : Prop := False\n"
        "theorem alwaysFalseEstimate (n : Nat) : ∃ K : Real, 0 ≤ K ∧ "
        "∀ (f : Real × Real → Real) (S : Set Real) (C : Real), 0 ≤ C → "
        "impossibleEnvelope f S n C → "
        "impossibleEnvelope (transport f) S n (K * C) := by\n"
        "  refine ⟨0, le_rfl, ?_⟩\n"
        "  intro f S C _ h\n"
        "  exact h\n"
    )
    prefix, suffix = source.rsplit("end ScalarExamples", 1)
    return prefix + alias + "end ScalarExamples" + suffix


def observed_type_query(targets):
    commands = "\n".join(
        f"#ladon_emit_type_json {json.dumps(target)}" for target in targets
    )
    return (
        "import LadonRealBoundBinding\n"
        + source_with_alias()
        + "\nopen Lean Elab Command\n"
        + "elab \"#ladon_emit_type_json \" target:str : command => do\n"
        + "  liftTermElabM do\n"
        + "    let value ← Ladon.RealBoundBinding.observedTypeJson target.getString.toName\n"
        + "    logInfo m!\"LADON_EXPR_JSON:{value.compress}\"\n"
        + commands
    )


def live_expected_types(root, deadline):
    targets = ("ScalarExamples.ordinary", "ScalarExamples.ordinaryCopy")
    source_path = root / "TypeJson.lean"
    source_path.write_text(
        observed_type_query(targets)
    )
    execution = prepare_direct_lean_execution(
        root, None, pinned_toolchain(root), require_compiled_module=False
    )
    result = run_bounded_target_process(
        [*execution.command, str(source_path)],
        cwd=root,
        env=execution.environment,
        timeout_seconds=min(60, deadline - time.monotonic()),
        max_output_bytes=8 * 1024**2,
        max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
    )
    assert result.succeeded, result.stdout + result.stderr
    values = []
    for line in (result.stdout + result.stderr).splitlines():
        marker = "LADON_EXPR_JSON:"
        if marker in line:
            values.append(line.split(marker, 1)[1])
    assert len(values) == len(targets), result.stdout + result.stderr
    return values


def relation_source(root, expected_left, expected_right, *, right="ScalarExamples.ordinaryCopy"):
    source = source_with_alias()
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    goal = ("ladon_real_bound_relation% "
            f"{quote('ScalarExamples.ordinary')} {quote(expected_left)} "
            f"{quote(right)} {quote(expected_right)}")
    return ("import LadonRealBoundBinding\n" + source +
            f"\nexample : {goal} := by\n  intros\n  rfl\n")


def run_relation(root, deadline, source):
    path = root / "RelationCheck.lean"
    path.write_text(source)
    execution = prepare_direct_lean_execution(
        root, None, pinned_toolchain(root), require_compiled_module=False
    )
    return run_bounded_target_process(
        [*execution.command, str(path)],
        cwd=root,
        env=execution.environment,
        timeout_seconds=min(60, deadline - time.monotonic()),
        max_output_bytes=8 * 1024**2,
        max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
    )


def test_relation_goal_is_generated_from_both_current_source_declarations(relation_project):
    root, deadline, _worker_root = relation_project
    expected_left, expected_right = live_expected_types(root, deadline)
    result = run_relation(
        root, deadline, relation_source(root, expected_left, expected_right)
    )
    assert result.succeeded, result.stdout + result.stderr


def test_relation_helper_rejects_a_stale_expected_expression(relation_project):
    root, deadline, _worker_root = relation_project
    expected, expected_right = live_expected_types(root, deadline)
    changed = expected.replace('"const":"Nat"', '"const":"Int"', 1)
    assert changed != expected
    result = run_relation(
        root, deadline, relation_source(root, changed, expected_right)
    )
    assert not result.succeeded
    assert "differs from the observed" in result.stdout + result.stderr


def test_supervised_relation_worker_checks_current_source_bound_plans(relation_project):
    _root, _deadline, root = relation_project
    snapshots = [
        produce_formal_snapshot(root, "ScalarExamples.lean", "ScalarExamples", declaration)
        for declaration in ("ScalarExamples.ordinary", "ScalarExamples.ordinaryCopy")
    ]
    plans = [
        plan_real_bound(plan_derivative_prefix(observe_bound_snapshot(snapshot, root)))
        for snapshot in snapshots
    ]

    from ladon.real_bound_native_check import check_real_bound_relation

    run = check_real_bound_relation(root, plans[0], plans[1], timeout_seconds=120)

    assert run["status"] == "completed", run.get("diagnostic")
    assert run["result"]["status"] == "checked", json.dumps(run["result"], indent=2)[:6000]
    assert run["result"]["leftPlanId"] == plans[0]["planId"]
    assert run["result"]["rightPlanId"] == plans[1]["planId"]
    assert run["result"]["goal"]["proposition"].startswith("ladon_real_bound_relation%")
    assert run["result"]["check"]["status"] == "supported"
    assert run["processReceipt"]["returnCode"] == 0

    source_path = root / "ScalarExamples.lean"
    original = source_path.read_bytes()
    try:
        source_path.write_bytes(original + b"\n-- stale-source control\n")
        stale = check_real_bound_relation(root, plans[0], plans[1], timeout_seconds=120)
        assert stale["status"] == "rejected"
        assert stale["diagnostic"]["code"] == "worker-rejected"
        assert stale["result"] is None
    finally:
        source_path.write_bytes(original)


def test_supervised_relation_worker_does_not_accept_a_false_relation(relation_project):
    _root, _deadline, root = relation_project
    snapshots = [
        produce_formal_snapshot(root, "ScalarExamples.lean", "ScalarExamples", declaration)
        for declaration in ("ScalarExamples.ordinary", "ScalarExamples.alwaysFalseEstimate")
    ]
    plans = [
        plan_real_bound(plan_derivative_prefix(observe_bound_snapshot(snapshot, root)))
        for snapshot in snapshots
    ]

    from ladon.real_bound_native_check import check_real_bound_relation

    run = check_real_bound_relation(root, plans[0], plans[1], timeout_seconds=120)

    assert run["status"] == "completed", run.get("diagnostic")
    assert run["result"]["status"] == "unresolved"
    assert run["result"]["residual"] == "real-relation-lean-check-unaccepted"
    assert run["result"]["check"]["status"] != "supported"
    assert run["processReceipt"]["returnCode"] == 0


def test_live_public_comparison_replays_both_native_productions(relation_project):
    if os.environ.get("LADON_REAL_BOUND_LIVE_ANALYSIS") != "1":
        pytest.skip("set LADON_REAL_BOUND_LIVE_ANALYSIS=1 for the multi-minute fresh-replay gate")
    _helper_root, _deadline, root = relation_project
    snapshots = [
        produce_formal_snapshot(root, "ScalarExamples.lean", "ScalarExamples", declaration)
        for declaration in ("ScalarExamples.ordinary", "ScalarExamples.ordinaryCopy")
    ]
    plans = [
        plan_real_bound(plan_derivative_prefix(observe_bound_snapshot(snapshot, root)))
        for snapshot in snapshots
    ]
    terms = {
        "predicate-admission":
            "by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl",
        "scalar-semantics": "by intros; exact ⟨rfl, rfl, rfl⟩",
    }

    from ladon.real_bound_native_analysis import (
        compare_real_bounds,
        propagate_real_bound_identity,
    )
    from ladon.real_bound_native_production import produce_real_bound

    saved = [produce_real_bound(root, plan, terms, timeout_seconds=180) for plan in plans]
    assert all(row["status"] == "admitted" for row in saved)
    assert all(row["authority"] == "fresh-lean-check" for row in saved)
    result = compare_real_bounds(saved[0], saved[1], root, timeout_seconds=600)

    assert result["status"] == "resolved"
    assert result["relation"] == "equivalent"
    assert result["contextMatch"] is True
    assert len(result["freshCheckEvidence"]) == 4
    assert result["contractRefs"][0] != result["contractRefs"][1]
    assert result["relationCheckEvidence"]["leftPlanId"] == plans[0]["planId"]
    assert result["relationCheckEvidence"]["rightPlanId"] == plans[1]["planId"]
    assert result["sourceTheoremProof"] == "not-checked"
    assert result["paperNormBridge"] == "unresolved"

    propagated = propagate_real_bound_identity(saved, root, timeout_seconds=600)
    assert propagated["status"] == "resolved"
    assert propagated["complete"] is True
    assert len(propagated["candidateEdges"]) == 1
    edge = propagated["candidateEdges"][0]
    assert edge["status"] == "resolved"
    assert edge["rule"] == "identity-v1"
    assert propagated["contractRefs"][0] != propagated["contractRefs"][1]
    assert edge["ruleApplication"]["inputContractRef"] == propagated["contractRefs"][0]
    assert edge["ruleApplication"]["outputContractRef"] == propagated["contractRefs"][1]
    assert edge["ruleApplication"]["goalDigest"].startswith("sha256:")
