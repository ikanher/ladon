from __future__ import annotations

import json

from ladon.proof_search_cli import proof_search_main


def test_invalid_argument_returns_one_versioned_terminal_record(capsys) -> None:
    assert proof_search_main(["index", "query", "--limit", "0"]) == 2
    streams = capsys.readouterr()
    assert streams.out == ""
    assert streams.err.count("\n") == 1
    assert json.loads(streams.err) == {
        "exitClass": "invocation",
        "exitCode": 2,
        "operation": "index.query",
        "schema": "ladon-proof-search-terminal-v1",
        "status": "failed",
    }
