from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ladon.proofir_v3 import validate_envelope_batch

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "lean_integration"


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_installed_cli_emits_batch_closed_semantic_evidence() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "proof-search",
            "check",
            "candidate",
            "--repo-root",
            str(FIXTURE),
            "--module",
            "LadonFixture",
            "--goal",
            "∀ value : Nat, value = value",
            "--candidate",
            "LadonFixture.fixtureIdentity",
            "--timeout-seconds",
            "30",
            "--max-rss-mib",
            "4096",
            "--projection",
            "audit",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert payload["schema"] == "ladon-semantic-candidate-check-result-v1"
    assert payload["status"] == "accepted"
    assert [row["artifactKind"] for row in payload["artifacts"]] == [
        "proofir.environment",
        "proofir.check-run",
        "proofir.derivation",
    ]
    validate_envelope_batch(payload["artifacts"])


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_installed_cli_default_projection_is_compact_and_expandable(tmp_path: Path) -> None:
    evidence_store = tmp_path / "semantic-evidence.sqlite"
    command = [
        sys.executable,
        "-m",
        "ladon.entrypoint",
        "proof-search",
        "check",
        "candidate",
        "--repo-root",
        str(FIXTURE),
        "--module",
        "LadonFixture",
        "--goal",
        "∀ value : Nat, value = value",
        "--candidate",
        "LadonFixture.fixtureIdentity",
        "--timeout-seconds",
        "30",
        "--max-rss-mib",
        "4096",
        "--evidence-store",
        str(evidence_store),
        "--format",
        "json",
    ]

    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert len(completed.stdout.encode("utf-8")) <= 8 * 1024
    payload = json.loads(completed.stdout)
    assert payload["schema"] == "ladon-semantic-candidate-projection-v1"
    reference = payload["candidate"]["check"]["checkRunRef"]
    assert reference["kind"] == "check-run"
    assert "artifacts" not in completed.stdout

    expanded = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "proof-search",
            "evidence",
            "semantic-check",
            reference["artifactRef"],
            "--local-id",
            reference["localId"],
            "--repo-root",
            str(FIXTURE),
            "--evidence-store",
            str(evidence_store),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert expanded.returncode == 0, expanded.stderr
    expanded_payload = json.loads(expanded.stdout)
    assert expanded_payload["artifact"]["artifactKind"] == "proofir.check-run"
    assert expanded_payload["reference"] == reference


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_discovery_batches_candidates_and_replays_selected_scratch() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "proof-search",
            "discover",
            "--repo-root",
            str(FIXTURE),
            "--module",
            "LadonFixture",
            "--goal",
            "∀ value : Nat, value = value",
            "--candidate",
            "LadonFixture.fixtureIdentity",
            "--candidate",
            "LadonFixture.noSuch",
            "--timeout-seconds",
            "30",
            "--max-rss-mib",
            "4096",
            "--scratch-mode",
            "advisory",
            "--projection",
            "audit",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["batch"]["protocol"] == "ladon-verified-discovery-v1"
    assert [row["check"]["status"] for row in payload["candidates"]] == [
        "accepted",
        "rejected",
    ]
    assert payload["candidates"][0]["check"]["scratch"]["status"] == "compiled"


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_discovery_default_is_compact_and_does_not_replay_scratch(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "proof-search",
            "discover",
            "--repo-root",
            str(FIXTURE),
            "--module",
            "LadonFixture",
            "--goal",
            "∀ value : Nat, value = value",
            "--candidate",
            "LadonFixture.fixtureIdentity",
            "--timeout-seconds",
            "30",
            "--max-rss-mib",
            "4096",
            "--evidence-store",
            str(tmp_path / "semantic-evidence.sqlite"),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert len(completed.stdout.encode("utf-8")) <= 32 * 1024
    payload = json.loads(completed.stdout)
    assert payload["schema"] == "ladon-verified-discovery-projection-v1"
    assert payload["request"]["scratchMode"] == "none"
    assert payload["candidates"][0]["check"]["scratch"] is None


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_testing_profile_rejects_caller_local_context() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "proof-search",
            "discover",
            "--repo-root",
            str(FIXTURE),
            "--module",
            "LadonFixture",
            "--goal",
            "value = value",
            "--local",
            "value:Nat",
            "--candidate",
            "LadonFixture.fixtureIdentity",
            "--timeout-seconds",
            "30",
            "--max-rss-mib",
            "4096",
            "--projection",
            "audit",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    assert completed.stdout == ""
    payload = json.loads(completed.stderr)
    assert payload["exitClass"] == "invocation"
    assert payload["status"] == "failed"


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_lean_owned_name_parser_accepts_unicode_declaration_name() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "proof-search",
            "check",
            "candidate",
            "--repo-root",
            str(FIXTURE),
            "--module",
            "LadonFixture",
            "--goal",
            "∀ value : Nat, value = value",
            "--candidate",
            "LadonFixture.identité",
            "--timeout-seconds",
            "30",
            "--max-rss-mib",
            "4096",
            "--projection",
            "audit",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "accepted"


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_worker_preserves_complete_introduced_local_context() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "proof-search",
            "check",
            "candidate",
            "--repo-root",
            str(FIXTURE),
            "--module",
            "LadonFixture",
            "--goal",
            "∀ x y : Nat, x = x",
            "--candidate",
            "LadonFixture.twoIdentity",
            "--timeout-seconds",
            "30",
            "--max-rss-mib",
            "4096",
            "--projection",
            "audit",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] in {"accepted", "applicable-with-residuals"}
    derivation = payload["artifacts"][2]
    contexts = [row for row in derivation["subjectRefs"] if row["kind"] == "local-context"]
    assert len(contexts) == 1
    assert len(contexts[0]["searchShape"]["orderedLocals"]) == 2
    assert [row["userName"] for row in contexts[0]["searchShape"]["orderedLocals"]] == [
        "x",
        "y",
    ]


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_theorem_query_accepts_worker_candidate_declaration_name() -> None:
    import sqlite3

    from ladon.proofir_sqlite_v3 import project_envelopes
    from ladon.proofir_v3_queries import query_v3_theorem_evidence
    from ladon.semantic_candidate_worker import SemanticCandidateRequest, check_semantic_candidate

    result = check_semantic_candidate(
        SemanticCandidateRequest(
            FIXTURE,
            "LadonFixture",
            "∀ value : Nat, value = value",
            "LadonFixture.fixtureIdentity",
        )
    )
    assert result.status == "accepted"
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, list(result.artifacts))
    dossier = query_v3_theorem_evidence(connection, "LadonFixture.fixtureIdentity", limit=20)
    assert dossier["status"] == "observed"
    assert dossier["subjects"]["returned"] >= 1


def _explicit_fixture_toolchain() -> object:
    from ladon.lean_toolchain import resolve_toolchain_context

    lean_path = Path(
        subprocess.check_output(
            ["elan", "which", "lean"], cwd=FIXTURE, text=True
        ).strip()
    )
    return resolve_toolchain_context(
        FIXTURE,
        lake_path=lean_path.with_name("lake"),
        lean_path=lean_path,
        selection_mode="explicit",
    )


def _assert_terminal_outcome_parity(toolchain: object) -> None:
    from ladon.semantic_candidate_batch_worker import check_semantic_candidates
    from ladon.semantic_candidate_worker import SemanticCandidateRequest, check_semantic_candidate

    candidates = (
        "LadonFixture.fixtureTrue",
        "id",
        "And.intro+True",
        "LadonFixture.noSuch",
        "LadonFixture.fixtureIdentity",
    )
    expected = (
        "accepted",
        "applicable-with-residuals",
        "rejected",
        "rejected",
        "rejected",
    )
    direct = [
        check_semantic_candidate(
            SemanticCandidateRequest(
                FIXTURE,
                "LadonFixture",
                "True",
                candidate,
                timeout_seconds=30,
                toolchain=toolchain,
            )
        )
        for candidate in candidates
    ]
    assert tuple(row.status for row in direct) == expected
    assert [row.diagnostic["code"] if row.diagnostic else None for row in direct[2:]] == [
        "candidate-name-invalid",
        "candidate-not-found",
        "application-rejected",
    ]
    assert all(row.artifacts for row in direct)

    batch = check_semantic_candidates(
        SemanticCandidateRequest(
            FIXTURE,
            "LadonFixture",
            "True",
            "batch-placeholder",
            timeout_seconds=30,
            toolchain=toolchain,
        ),
        candidates,
    )
    assert batch.terminal is True
    assert tuple(row["status"] for row in batch.rows) == expected
    assert all(row["artifacts"] for row in batch.rows)


def _assert_discharge_and_ascii_binding(toolchain: object) -> None:
    from ladon.semantic_candidate_worker import SemanticCandidateRequest, check_semantic_candidate

    discharged = check_semantic_candidate(
        SemanticCandidateRequest(
            FIXTURE,
            "LadonFixture",
            "∀ h : True, True",
            "id",
            timeout_seconds=30,
            toolchain=toolchain,
        )
    )
    assert discharged.status == "accepted"
    assert discharged.application_term == "id h"
    assert discharged.discharged_hypotheses == (
        {
            "premiseOrdinal": 0,
            "premiseTypeDisplay": "True",
            "dischargedByLocalRef": "local:0",
            "method": "assumption-definitional-equality",
        },
    )

    ascii_goal = check_semantic_candidate(
        SemanticCandidateRequest(
            FIXTURE,
            "LadonFixture",
            "True -> True",
            "id",
            timeout_seconds=30,
            toolchain=toolchain,
        )
    )
    assert ascii_goal.status == "accepted"

    exact_constant_equality = check_semantic_candidate(
        SemanticCandidateRequest(
            FIXTURE,
            "LadonFixture",
            "LadonFixture.Core.value = LadonFixture.Helper.identity LadonFixture.Core.value",
            "LadonFixture.fixtureUsesCore",
            timeout_seconds=30,
            toolchain=toolchain,
        )
    )
    assert exact_constant_equality.status == "accepted"


def _assert_post_discharge_scratch(toolchain: object) -> None:
    lean_path = toolchain.lean_path
    lake_path = toolchain.lake_path
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "proof-search",
            "discover",
            "--repo-root",
            str(FIXTURE),
            "--module",
            "LadonFixture",
            "--goal",
            "∀ h : True, True",
            "--candidate",
            "id",
            "--timeout-seconds",
            "30",
            "--max-rss-mib",
            "4096",
            "--toolchain-mode",
            "explicit",
            "--lake-path",
            str(lake_path),
            "--lean-path",
            str(lean_path),
            "--scratch-mode",
            "advisory",
            "--projection",
            "audit",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    discovery = json.loads(completed.stdout)
    checked = discovery["candidates"][0]["check"]
    assert checked["applicationTerm"] == "id h"
    assert checked["scratch"]["status"] == "compiled"
    assert checked["scratch"]["evidenceReceipt"]["authorityBasis"] == "process-observation"


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain unavailable")
def test_real_lean_closing_profile_covers_terminal_outcomes_and_replay() -> None:
    toolchain = _explicit_fixture_toolchain()
    _assert_terminal_outcome_parity(toolchain)
    _assert_discharge_and_ascii_binding(toolchain)
    _assert_post_discharge_scratch(toolchain)
