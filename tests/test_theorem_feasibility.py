from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ladon.theorem_cli import theorem_main

FIXTURE = Path(__file__).parent / "fixtures" / "theorem_feasibility"
MODULE = "FeasibilityFixture"


@pytest.fixture(scope="module")
def built_fixture(tmp_path_factory):
    repo = tmp_path_factory.mktemp("feasibility")
    shutil.copytree(FIXTURE, repo, dirs_exist_ok=True)
    (repo / "Imported.lean").write_text(f"import {MODULE}\n", encoding="utf-8")
    for command in (
        ["lake", "build"],
        ["lake", "env", "lean", "-o", ".lake/build/lib/lean/Imported.olean", "Imported.lean"],
    ):
        build = subprocess.run(
            command, cwd=repo, capture_output=True, text=True, timeout=120, check=False
        )
        assert build.returncode == 0, build.stdout + build.stderr
    return repo


@pytest.mark.parametrize(
    "name,route",
    [
        ("silly_theorem", "omega"),
        ("prove_anything", "projection"),
        ("trivialConclusion", "omega"),
        ("renamedField", "projection"),
        ("badStructureTrivial", "projection"),
        ("explicitArrow", "false-hypothesis"),
        ("verifiedClaim", "false-hypothesis"),
        ("proofDependent", "false-hypothesis"),
        ("certifiedClaim", "false-hypothesis"),
        ("chainChecked", "empty-inductive"),
        ("ranked", "nat-descent"),
        ("squareChecked", "omega"),
        ("complementary", "propositional"),
        ("complementaryReversed", "propositional"),
        ("implicationChain", "propositional"),
        ("implicationChainReversed", "propositional"),
        ("boolParam", "false-hypothesis"),
        ("dependentParam", "false-hypothesis"),
        ("polymorphicParam", "false-hypothesis"),
        ("intContradiction", "omega"),
        ("natCycle", "omega"),
        ("parityGap", "omega"),
        ("nestedProjection", "projection"),
        ("dataProjection", "projection"),
        ("projectedContradiction", "omega"),
        ("projectedAfterApply", "projection"),
        ("conjunctionAfterApply", "propositional"),
        ("arithmeticBeforeApply", "grind"),
        ("arithmeticProducesWrapper", "grind"),
        ("branchesProduceWrapper", "grind"),
        ("projectedArithmeticBeforeApply", "grind"),
        ("trueAntecedent", "grind"),
        ("emptyWitness", "grind"),
        ("disjunctionExhausted", "grind"),
        ("equalityTransport", "grind"),
    ],
)
def test_automatic_refutation(built_fixture, capsys, name, route):
    code = theorem_main(
        ["feasibility", name, "--repo-root", str(built_fixture), "--module", MODULE]
    )
    out = capsys.readouterr()
    assert code == 0, out
    result = json.loads(out.out)
    assert result["status"] == "inconsistent", result
    assert result["route"] == route
    assert result["declaration"] == name and result["module"] == MODULE
    assert result["replay"]["status"] == "accepted"
    assert result["trust"]["accepted"] is True
    assert result["compiledInputs"]["snapshotDigest"].startswith("sha256:")


def check(repo, capsys, name, *flags, module=MODULE):
    code = theorem_main(["feasibility", name, "--repo-root", str(repo), "--module", module, *flags])
    captured = capsys.readouterr()
    return code, json.loads(captured.out)


@pytest.fixture(scope="module")
def alternate_certificates(built_fixture):
    from ladon.theorem_feasibility import WORKER

    (built_fixture / "FeasibilityWorker.lean").write_bytes(WORKER.read_bytes())
    for arguments in (
        ["-o", ".lake/build/lib/lean/FeasibilityWorker.olean", "FeasibilityWorker.lean"],
        ["FeasibilityChecks.lean"],
    ):
        result = subprocess.run(
            ["lake", "env", "lean", *arguments],
            cwd=built_fixture,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    return built_fixture


def test_native_closures_match_independently_elaborated_propositions(alternate_certificates):
    assert (alternate_certificates / "wrongRefutation.olean").is_file()


@pytest.mark.parametrize(
    "name,reason",
    [
        ("inhabitedNat", "no-refutation"),
        ("propParameter", "no-refutation"),
        ("legitimateContradiction", "no-refutation"),
        ("negFalse", "no-refutation"),
        ("aliasedNegation", "no-refutation"),
        ("feasibleDependent", "no-refutation"),
        ("feasibleRecursive", "no-refutation"),
        ("feasibleRanking", "no-refutation"),
        ("feasibleSquare", "no-refutation"),
        ("implicationNearMiss", "no-refutation"),
        ("intInterval", "no-refutation"),
        ("nestedInhabited", "no-refutation"),
        ("projectedInterval", "no-refutation"),
        ("disjunctionFeasible", "no-refutation"),
        ("projectedArithmeticFeasible", "no-refutation"),
        ("wrapperAntecedentFeasible", "no-refutation"),
    ],
)
def test_unresolved_controls(built_fixture, capsys, name, reason):
    code, result = check(built_fixture, capsys, name)
    assert code == 0 and result["status"] == "unresolved", result
    assert result["reason"] == reason
    assert result["replay"]["status"] == "not-run"


def test_fail_on_unresolved_preserves_the_verdict(built_fixture, capsys):
    code, result = check(built_fixture, capsys, "feasibleRecursive", "--fail-on-unresolved")
    assert code == 1 and result["status"] == "unresolved", result


@pytest.mark.parametrize(
    "name,module",
    [
        ("silly_theorem", "Imported"),
        ("Silly_theorem", MODULE),
        ("ordinaryDefinition", MODULE),
    ],
)
def test_exact_owned_theorem_required(built_fixture, capsys, name, module):
    code, result = check(built_fixture, capsys, name, module=module)
    assert code == 2 and result["status"] == "invalid-selection", result


@pytest.mark.parametrize(
    "name,flags,reason",
    [
        ("silly_theorem", ("--max-binders", "2"), "binder-limit"),
        ("nestedProjection", ("--max-projection-depth", "1"), "projection-depth-limit"),
        ("projectedAfterApply", ("--max-projection-depth", "1"), "projection-depth-limit"),
        ("nestedProjection", ("--max-derived-facts", "1"), "derived-fact-limit"),
        ("implicationChain", ("--max-inferences", "1"), "inference-limit"),
        ("prove_anything", ("--max-dependencies", "1"), "dependency-limit"),
        ("prove_anything", ("--timeout", "0.0001"), "timeout"),
    ],
)
def test_resource_stops(built_fixture, capsys, name, flags, reason):
    code, result = check(built_fixture, capsys, name, *flags)
    assert code == 1 and result["status"] == "unresolved", result
    assert result["reason"] == reason


def substitute_certificate(monkeypatch, repo: Path, certificate: str) -> None:
    from ladon import theorem_feasibility

    run = theorem_feasibility.run_bounded_target_process

    def substitute(command, **options):
        result = run(command, **options)
        if "--run" in command and command[3] == "prove":
            shutil.copyfile(repo / f"{certificate}.olean", command[6])
        return result

    monkeypatch.setattr(theorem_feasibility, "run_bounded_target_process", substitute)


def test_replay_checks_native_auxiliaries(alternate_certificates, capsys, monkeypatch):
    substitute_certificate(monkeypatch, alternate_certificates, "withAuxiliary")
    code, result = check(alternate_certificates, capsys, "prove_anything")
    assert code == 0 and result["status"] == "inconsistent", result
    assert result["trust"]["observedAxioms"] == []


@pytest.mark.parametrize(
    "certificate,reason,exit_code",
    [
        ("wrongRefutation", "certificate-subject-mismatch", 0),
        ("collidingCertificate", "certificate-name-conflict", 0),
        ("circularRefutation", "reviewed-theorem-dependency", 0),
        ("uncheckedRefutation", "forbidden-axiom", 0),
        ("mistyped", "kernel-rejected-certificate", 1),
    ],
)
def test_replay_and_trust_reject_substituted_certificate(
    alternate_certificates,
    capsys,
    monkeypatch,
    certificate,
    reason,
    exit_code,
):
    substitute_certificate(monkeypatch, alternate_certificates, certificate)
    code, result = check(alternate_certificates, capsys, "prove_anything")
    assert code == exit_code and result["status"] == "unresolved", result
    assert result["reason"] == reason
    if certificate == "uncheckedRefutation":
        assert result["replay"]["status"] == "accepted"
        assert result["trust"]["accepted"] is False
        assert "uncheckedRefutation" in result["trust"]["observedAxioms"]
    else:
        assert result["replay"]["status"] == "rejected"


def test_changed_compiled_input_withholds_finding(built_fixture, capsys, monkeypatch):
    from ladon import theorem_feasibility

    path = built_fixture / f".lake/build/lib/lean/{MODULE}.olean"
    original = path.read_bytes()
    run = theorem_feasibility.run_bounded_target_process

    def change_after_replay(command, **options):
        result = run(command, **options)
        if "--run" in command and command[3] == "replay":
            path.write_bytes(original + b"drift")
        return result

    monkeypatch.setattr(theorem_feasibility, "run_bounded_target_process", change_after_replay)
    try:
        code, result = check(built_fixture, capsys, "prove_anything")
    finally:
        path.write_bytes(original)
    assert code == 1 and result["status"] == "unresolved", result
    assert result["reason"] == "compiled-module-stale"
    assert result["replay"]["status"] == "failed"


def test_text_names_advisory_and_replay(built_fixture, capsys):
    code = theorem_main(
        [
            "feasibility",
            "«unicode.name»",
            "--repo-root",
            str(built_fixture),
            "--module",
            MODULE,
            "--format",
            "text",
        ]
    )
    output = capsys.readouterr().out
    assert code == 0, output
    assert "inconsistent" in output
    assert "Independent replay: accepted" in output
    assert "Trust: accepted" in output
