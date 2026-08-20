from __future__ import annotations

import json
import sys
from pathlib import Path

from ladon.process_supervisor import ProcessResult
from ladon.semantic_candidate_batch_worker import check_semantic_candidates
from ladon.semantic_candidate_worker import SEMANTIC_BATCH_PROTOCOL, SemanticCandidateRequest


def test_batch_worker_uses_one_framed_process_and_preserves_row_order(tmp_path: Path) -> None:
    observed: dict[str, object] = {}
    olean = tmp_path / "Main.olean"
    olean.write_bytes(b"compiled")

    def runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        observed["command"] = command
        request_id = command[-3]
        probe_name = command[-4]
        payload = {
            "protocol": SEMANTIC_BATCH_PROTOCOL,
            "frameVersion": 1,
            "sequence": 0,
            "terminal": True,
            "requestId": request_id,
            "universePolicy": "lean-level-mvar-succ-zero/v1",
            "leanVersion": "4.fixture",
            "leanCommit": "fixture",
            "executablePath": sys.executable,
            "module": "Main",
            "probe": {"name": probe_name, "typeDisplay": "Nat", "typeStructural": "Nat"},
            "importedModules": [{"module": "Main", "oleanPath": str(olean)}],
            "localContext": [],
            "rows": [
                {
                    "candidate": "Main.good",
                    "status": "accepted",
                    "candidateSubject": {
                        "name": "Main.good",
                        "typeDisplay": "Nat",
                        "typeStructural": "Nat",
                    },
                    "applicationTerm": "Main.good",
                    "substitutions": [],
                    "residualPremises": [],
                    "diagnostic": "",
                },
                {
                    "candidate": "Main.bad",
                    "status": "rejected",
                    "candidateSubject": None,
                    "applicationTerm": "",
                    "substitutions": [],
                    "residualPremises": [],
                    "diagnostic": "unknown declaration",
                },
            ],
        }
        return ProcessResult(command, 0, "LADON_FRAME " + json.dumps(payload), "", 0.1)

    result = check_semantic_candidates(
        SemanticCandidateRequest(tmp_path, "Main", "Nat", "Main.good"),
        ["Main.good", "Main.bad"],
        runner=runner,
    )
    assert result.status == "available"
    assert [row["candidate"] for row in result.rows] == ["Main.good", "Main.bad"]
    assert all(row["evidenceReceipt"]["checkRunRef"] == row["checkRunRef"] for row in result.rows)
    assert [artifact["artifactKind"] for artifact in result.rows[0]["artifacts"]] == [
        "proofir.environment",
        "proofir.check-run",
        "proofir.derivation",
    ]
    assert "--batch" in observed["command"]  # type: ignore[operator]


def test_batch_worker_rejects_malformed_accepted_row_fields(tmp_path: Path) -> None:
    def runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        payload = {
            "protocol": SEMANTIC_BATCH_PROTOCOL,
            "frameVersion": 1,
            "sequence": 0,
            "terminal": True,
            "requestId": command[-2],
            "universePolicy": "lean-level-mvar-succ-zero/v1",
            "leanVersion": "4.fixture",
            "leanCommit": "fixture",
            "executablePath": sys.executable,
            "module": "Main",
            "probe": {"name": command[-3], "typeDisplay": "Nat", "typeStructural": "Nat"},
            "importedModules": [{"module": "Main", "oleanPath": str(tmp_path / "Main.olean")}],
            "localContext": [],
            "rows": [
                {
                    "candidate": "Main.good",
                    "status": "accepted",
                    "candidateSubject": 7,
                    "substitutions": "bad",
                    "residualPremises": [{}],
                    "diagnostic": [],
                }
            ],
        }
        return ProcessResult(command, 0, "LADON_FRAME " + json.dumps(payload), "", 0.1)

    result = check_semantic_candidates(
        SemanticCandidateRequest(tmp_path, "Main", "Nat", "Main.good"),
        ["Main.good"],
        runner=runner,
    )
    assert result.status == "invalid-worker-output"
