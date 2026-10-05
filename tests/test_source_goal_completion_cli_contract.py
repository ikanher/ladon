"""Portable CLI proposals for the additive captured-goal completion route."""
from __future__ import annotations

import pytest

from ladon.proof_search_cli import build_proof_search_parser
from ladon.proof_search_index import ProofSearchIndexError


def test_goal_complete_accepts_capture_file_and_full_term_without_handwritten_goal():
    parser = build_proof_search_parser()
    try:
        args = parser.parse_args([
            "goal", "complete", "--repo-root", "/tmp/lean-project",
            "--capture-file", "/tmp/capture-result.json", "--term", "Nat.zero",
            "--lean-path", "/toolchain/bin/lean", "--lake-path", "/toolchain/bin/lake",
            "--toolchain-mode", "explicit", "--format", "json",
        ])
    except ProofSearchIndexError as error:
        pytest.fail(f"goal complete is absent or rejects its declared input contract: {error}")

    assert args.proof_search_operation == "goal"
    assert args.goal_operation == "complete"
    assert args.capture_file.as_posix() == "/tmp/capture-result.json"
    assert args.term == "Nat.zero"
    # Goal, local, and candidate flags are not part of this source-owned operation.
    assert not hasattr(args, "goal")
    assert not hasattr(args, "local")
    assert not hasattr(args, "candidate")


def test_historical_capture_route_remains_registered():
    args = build_proof_search_parser().parse_args([
        "goal", "capture", "--repo-root", "/tmp/lean-project", "--source", "Owner.lean",
        "--module", "Owner", "--line", "1", "--column", "0",
        "--lean-path", "/toolchain/bin/lean", "--lake-path", "/toolchain/bin/lake",
    ])
    assert args.goal_operation == "capture"
