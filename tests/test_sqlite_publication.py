from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ladon.sqlite_publication import (
    PublicationLockBusy,
    acquire_publication_lock,
    publication_lock_status,
    release_publication_lock,
)


def test_kernel_lock_is_authoritative_and_reacquirable(tmp_path: Path) -> None:
    destination = tmp_path / "index.sqlite"
    first = acquire_publication_lock(destination)
    try:
        status = publication_lock_status(destination)
        assert status["status"] == "active"
        assert status["pid"] == os.getpid()
        assert status["ownerToken"] == first.nonce
        with pytest.raises(PublicationLockBusy, match="publication already active"):
            acquire_publication_lock(destination)
    finally:
        release_publication_lock(first)

    assert publication_lock_status(destination)["status"] == "inactive"
    second = acquire_publication_lock(destination)
    release_publication_lock(second)


def test_release_never_deletes_replacement_owner_path(tmp_path: Path) -> None:
    destination = tmp_path / "index.sqlite"
    owner = acquire_publication_lock(destination)
    replacement = tmp_path / "replacement.lock"
    replacement.write_text(
        json.dumps({"pid": os.getpid(), "nonce": "replacement"}),
        encoding="utf-8",
    )
    os.replace(replacement, owner.path)

    release_publication_lock(owner)

    assert owner.path.exists()
    assert json.loads(owner.path.read_text(encoding="utf-8"))["nonce"] == "replacement"
