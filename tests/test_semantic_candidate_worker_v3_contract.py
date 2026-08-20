from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ladon.lean_toolchain import resolve_toolchain_context
from ladon.process_supervisor import ProcessResult
from ladon.proofir_v3 import validate_envelope_batch
from ladon.semantic_candidate_worker import (
    SEMANTIC_PROTOCOL,
    SemanticCandidateRequest,
    check_semantic_candidate,
)


def _accepted_payload(tmp_path: Path) -> dict[str, Any]:
    olean = tmp_path / "Main.olean"
    olean.write_bytes(b"exact compiled module")
    executable = tmp_path / "lean"
    executable.write_bytes(b"exact lean executable")
    return {
        "protocol": SEMANTIC_PROTOCOL,
        "frameVersion": 1,
        "sequence": 0,
        "terminal": True,
        "universePolicy": "lean-level-mvar-succ-zero/v1",
        "requestId": "fixture-request",
        "leanVersion": "4.32.2",
        "leanCommit": "commit",
        "executablePath": str(executable),
        "module": "Ladon.Semantic.generated",
        "probe": {
            "name": "filled-from-supervisor-command",
            "typeDisplay": "Nat → Nat",
            "typeStructural": "forallE Nat Nat",
        },
        "candidate": {
            "name": "Main.identity",
            "typeDisplay": "Nat → Nat",
            "typeStructural": "forallE Nat Nat",
        },
        "importedModules": [{"module": "Main", "oleanPath": str(olean)}],
        "substitutions": [],
        "residualPremises": [],
        "localContext": [],
    }


def _assert_artifact_family(artifacts: tuple[dict[str, Any], ...]) -> None:
    assert [row["artifactKind"] for row in artifacts] == [
        "proofir.environment",
        "proofir.check-run",
        "proofir.derivation",
    ]
    validate_envelope_batch(list(artifacts))


def _assert_exact_links(artifacts: tuple[dict[str, Any], ...]) -> None:
    environment, check, derivation = artifacts
    assert check["environmentRef"] == environment["environmentRef"]
    assert check["payload"]["inputs"]["artifactRefs"] == [environment["artifactId"]]
    step = derivation["payload"]["steps"][0]
    assert step["checkRunRef"]["artifactRef"] == check["artifactId"]
    assert step["checkRunRef"]["localId"] == check["payload"]["checkRunId"]


def _assert_exact_semantics(artifacts: tuple[dict[str, Any], ...]) -> None:
    check, derivation = artifacts[1:]
    step = derivation["payload"]["steps"][0]
    assert step["substitutions"] == []
    assert step["premiseRefs"] == []
    assert step["localContextRef"]["kind"] == "local-context"
    assert check["payload"]["results"][0]["result"] == "accepted"


def _assert_process_bounds(artifacts: tuple[dict[str, Any], ...]) -> None:
    check = artifacts[1]
    assert check["payload"]["outputs"]["stdoutDigest"].startswith("sha256:")
    assert check["extensions"]["ladon.process-observation/v1"]["bounds"] == {
        "timeoutMs": 120000,
        "maxOutputBytes": 8 * 1024 * 1024,
        "maxRssBytes": 2 * 1024 * 1024 * 1024,
    }


def test_accepted_worker_result_closes_exact_environment_and_check_references(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    repo.joinpath("lean-toolchain").write_text("leanprover/lean4:v4.32.2\n")
    payload = _accepted_payload(tmp_path)

    def accepted_runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        payload["probe"]["name"] = command[-3]
        payload["requestId"] = command[-1]
        return ProcessResult(
            tuple(command), 0, "LADON_FRAME " + json.dumps(payload), "", 0.25, peak_rss_bytes=4096
        )

    result = check_semantic_candidate(
        SemanticCandidateRequest(repo, "Main", "Nat → Nat", "Main.identity"),
        runner=accepted_runner,
    )

    assert result.status == "accepted"
    assert result.to_dict()["authoritySelection"] == "ambient-selected-application-check"
    assert result.to_dict()["analysisCompleteness"] == "complete"
    _assert_artifact_family(result.artifacts)
    _assert_exact_links(result.artifacts)
    _assert_exact_semantics(result.artifacts)
    _assert_process_bounds(result.artifacts)


def test_timeout_never_publishes_accepted_artifacts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    def timeout_runner(*_args: object, **_kwargs: object) -> ProcessResult:
        return ProcessResult(
            ("lake", "env", "lean"), -9, "", "deadline", 1.0, timed_out=True
        )

    result = check_semantic_candidate(
        SemanticCandidateRequest(repo, "Main", "Nat", "Main.value"),
        runner=timeout_runner,
    )

    assert result.status == "timeout"
    assert result.artifacts == ()
    assert result.diagnostic == {"code": "checker-timeout", "message": "deadline"}


def test_explicit_toolchain_ignores_path_shadow_and_sanitizes_worker_environment(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    repo.joinpath("lean-toolchain").write_text("leanprover/lean4:v4.32.2\n")
    lake = repo / "lake"
    lean = repo / "lean"
    for tool in (lake, lean):
        tool.write_text("#!/bin/sh\nprintf 'Lean version 4.32.2\\n'\n")
        tool.chmod(0o755)
    context = resolve_toolchain_context(
        repo,
        lake_path=lake,
        lean_path=lean,
        environment={"PATH": str(tmp_path / "shadow"), "SECRET": "redacted"},
    )
    payload = _accepted_payload(tmp_path)
    observed: dict[str, object] = {}

    def runner(command: tuple[str, ...], **kwargs: object) -> ProcessResult:
        observed["command"] = command
        observed["env"] = kwargs.get("env")
        payload["probe"]["name"] = command[-3]
        payload["requestId"] = command[-1]
        return ProcessResult(tuple(command), 0, "LADON_FRAME " + json.dumps(payload), "", 0.1)

    result = check_semantic_candidate(
        SemanticCandidateRequest(repo, "Main", "Nat → Nat", "Main.identity", toolchain=context),
        runner=runner,
    )
    assert result.status == "accepted"
    assert observed["command"][0:3] == (str(lake), "env", str(lean))  # type: ignore[index]
    assert "SECRET" not in observed["env"]  # type: ignore[operator]


def test_worker_protocol_rejects_foreign_or_unscoped_semantic_rows(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    payload = _accepted_payload(tmp_path)
    payload["candidate"]["name"] = "Other.foreign"

    def foreign_runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        payload["probe"]["name"] = command[-3]
        return ProcessResult(tuple(command), 0, "LADON_FRAME " + json.dumps(payload), "", 0.1)

    result = check_semantic_candidate(
        SemanticCandidateRequest(repo, "Main", "Nat", "Main.identity"),
        runner=foreign_runner,
    )

    assert result.status == "invalid-worker-output"
    assert result.artifacts == ()
    assert result.diagnostic["code"] == "invalid-worker-output"
