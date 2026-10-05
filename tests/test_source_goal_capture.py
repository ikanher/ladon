"""Contract tests for source-position goal capture."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from ladon.lean_toolchain import resolve_toolchain_context


def _api():
    from ladon.source_goal_capture import (
        SourceGoalCaptureRequest,
        capture_source_goal,
    )

    return SourceGoalCaptureRequest, capture_source_goal


def _request(root: Path, context: Any, **overrides: Any):
    request_type, _ = _api()
    fields = {
        "repo_root": root,
        "source_path": "Owner.lean",
        "module": "Owner",
        "line": 1,
        "column": 0,
        "toolchain": context,
        "timeout_seconds": 45,
        "max_rss_bytes": 8 * 1024**3,
    }
    fields.update(overrides)
    return request_type(**fields)


def _context(root: Path, lean: Path):
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.32.1\n")
    return resolve_toolchain_context(
        root,
        lake_path=lean.with_name("lake"),
        lean_path=lean,
        selection_mode="explicit",
        environment={"PATH": os.defpath, "LANG": "C"},
    )


@pytest.mark.skipif(shutil.which("lean") is None, reason="Lean toolchain unavailable")
def test_request_validation_and_expected_source_digest_are_explicit(tmp_path: Path):
    fixture = next(
        parent / "tests" / "fixtures" / "lean_integration"
        for parent in Path(__file__).resolve().parents
        if (parent / "tests" / "fixtures" / "lean_integration" / "lean-toolchain").is_file()
    )
    prefix = subprocess.run(
        ["lean", "--print-prefix"],
        cwd=fixture,
        capture_output=True, text=True, check=True, timeout=15,
    ).stdout.strip()
    lean = Path(prefix) / "bin" / "lean"
    root = tmp_path / "repo"
    root.mkdir()
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.32.1\n")
    source = root / "Owner.lean"
    source.write_text("theorem t : True := by trivial\n")
    context = _context(root, lean)
    _, capture = _api()

    with pytest.raises(ValueError):
        _request(root, context, line=0)

    mismatch = capture(_request(root, context, expected_source_digest="sha256:" + "0" * 64))
    assert mismatch["status"] == "stale"
    assert mismatch["capture"] is None
    assert mismatch["diagnostic"]["code"]
    assert source.exists()
