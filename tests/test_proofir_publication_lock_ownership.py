from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ladon.proofir_sqlite_v3 import _acquire_v3_lock, _release_v3_lock


def test_lock_release_does_not_remove_a_replacement_owner(tmp_path: Path) -> None:
    destination = tmp_path / "proofir.sqlite"
    lock = _acquire_v3_lock(destination)
    replacement = lock.path.with_suffix(".replacement")
    replacement.write_text(
        json.dumps({"pid": os.getpid(), "destination": str(destination), "nonce": "new-owner"}),
        encoding="utf-8",
    )
    os.replace(replacement, lock.path)
    _release_v3_lock(lock)
    assert lock.path.exists()
    assert json.loads(lock.path.read_text(encoding="utf-8"))["nonce"] == "new-owner"
    lock.path.unlink()


def test_second_builder_fails_fast_while_first_descriptor_is_held(tmp_path: Path) -> None:
    destination = tmp_path / "proofir.sqlite"
    owner = _acquire_v3_lock(destination)
    try:
        with pytest.raises(RuntimeError, match="already active"):
            _acquire_v3_lock(destination)
    finally:
        _release_v3_lock(owner)


def test_release_keeps_metadata_path_but_allows_same_inode_reacquisition(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "proofir.sqlite"
    first = _acquire_v3_lock(destination)
    inode = first.inode
    _release_v3_lock(first)
    assert first.path.exists()
    second = _acquire_v3_lock(destination)
    try:
        assert second.inode == inode
        assert second.path.exists()
    finally:
        _release_v3_lock(second)
