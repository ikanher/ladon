from __future__ import annotations

import json
from pathlib import Path

from ladon.process_supervisor import ProcessResult
from ladon.semantic_candidate_batch_worker import check_semantic_candidates
from ladon.semantic_candidate_worker import SEMANTIC_BATCH_PROTOCOL, SemanticCandidateRequest


def test_batch_worker_uses_one_framed_process_and_preserves_row_order(tmp_path: Path) -> None:
    observed: dict[str, object] = {}

    def runner(command: tuple[str, ...], **_kwargs: object) -> ProcessResult:
        observed["command"] = command
        request_id = command[-3]
        payload = {
            "protocol": SEMANTIC_BATCH_PROTOCOL,
            "frameVersion": 1,
            "terminal": True,
            "requestId": request_id,
            "module": "Main",
            "rows": [
                {"candidate": "Main.good", "status": "accepted"},
                {"candidate": "Main.bad", "status": "rejected"},
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
    assert "--batch" in observed["command"]  # type: ignore[operator]
