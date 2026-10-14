"""Root-selected independent false extraction authority regression."""
import hashlib

import pytest


def test_fake_dependency_graph_keeps_both_premises_and_missing_branch_open():
    from ladon.correspondence_check import prepare_correspondence

    # Two-premise formal step: one provider is observed, one is absent. A graph
    # path to the conclusion must not erase the unprovided AND branch.
    interpretation_record = {
        "id": "two-premise-control",
        "source": {"path": "claim.txt", "startLine": 1, "endLine": 1,
                   "quote": "A controls the argument.", "sha256": hashlib.sha256(
                       b"A controls the argument.\n").hexdigest()},
        "formula": {"tag": "implies", "premise": {"tag": "and", "items": [
            {"tag": "var", "id": "p"}, {"tag": "var", "id": "q"}
        ]}, "conclusion": {"tag": "var", "id": "r"}},
        "symbols": {},
    }
    # The declared source bytes make the input structurally plausible; the
    # manually authored slice below still must not become observed evidence.
    proof_slice = {
        "complete": True,
        "nodes": [
            {"id": "app-1", "kind": "application", "declaration": "step",
             "type": "p → q → r", "premises": [
                 {"occurrence": 0, "proposition": "p", "provider": "hP"},
                 {"occurrence": 1, "proposition": "q", "provider": None},
             ]},
            {"id": "hP", "kind": "assumption", "proposition": "p"},
        ],
        "edges": [["hP", "app-1"]],
    }
    with pytest.raises((ValueError, RuntimeError)):
        prepare_correspondence(interpretation_record, proof_slice,
                              {"p": "p", "q": "q", "r": "r"})

