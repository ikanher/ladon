from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

from ladon.proof_search_index import build_proof_search_index


def test_build_payload_exposes_only_implemented_lexical_mode(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    payload = build_proof_search_index(tmp_path).payload
    assert payload["build"] == {"mode": "lexical", "publication": "atomic"}
    assert payload["evidenceStatus"] == "lexical-fallback"
    assert payload["counts"]["declarationDependencies"] == 0
    assert payload["counts"]["structureFields"] == 0


def test_installed_cli_rejects_removed_semantic_mode_without_invoking_lean(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    marker = tmp_path / "lean-invoked"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    lake = fake_bin / "lake"
    lake.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 99\n", encoding="utf-8")
    lake.chmod(lake.stat().st_mode | stat.S_IXUSR)
    environment = dict(os.environ)
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment.get('PATH', '')}"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ladon.entrypoint",
            "proof-search",
            "index",
            "build",
            "--repo-root",
            str(repository),
            "--mode",
            "semantic",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )

    assert completed.returncode == 2
    terminal = json.loads(completed.stderr)
    assert terminal["exitClass"] == "invocation"
    assert terminal["operation"] == "index.build"
    assert not marker.exists()
    assert not (repository / ".ladon/index/proof-search.sqlite").exists()
