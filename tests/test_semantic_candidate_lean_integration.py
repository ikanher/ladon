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
            "2048",
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
            "2048",
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
def test_discovery_elaborates_caller_local_context_and_replays_same_context() -> None:
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
    check = payload["candidates"][0]["check"]
    assert check["status"] == "accepted"
    assert check["evidenceReceipt"]["subject"]["localContext"] == [{"name": "value", "type": "Nat"}]
    assert "example (value : Nat) : value = value" in check["scratch"]["source"]
    assert "exact LadonFixture.fixtureIdentity value" in check["scratch"]["source"]
    assert check["scratch"]["status"] == "compiled"
    assert check["scratch"]["parentCheckRunRef"] == check["checkRunRef"]
    assert check["scratch"]["environmentRef"] == check["environmentRef"]
    assert check["scratch"]["evidenceReceipt"]["checkRunRef"] == check["scratch"]["checkRunRef"]


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
