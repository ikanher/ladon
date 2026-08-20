from __future__ import annotations

from pathlib import Path

import pytest

from ladon import proof_search_index
from ladon.sqlite_publication import publication_lock_status


def test_interrupted_index_build_preserves_prior_generation_and_cleans_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "Main.lean").write_text(
        "theorem goal : True := by trivial\n", encoding="utf-8"
    )
    completed = proof_search_index.build_proof_search_index(repository)
    destination = completed.index_path
    previous = destination.read_bytes()
    partial: list[Path] = []

    def interrupt(path: Path, *_args: object, **_kwargs: object) -> object:
        partial.append(path)
        path.write_bytes(b"partial-index")
        raise KeyboardInterrupt

    monkeypatch.setattr(proof_search_index, "_write_database", interrupt)

    with pytest.raises(KeyboardInterrupt):
        proof_search_index.build_proof_search_index(repository)

    assert destination.read_bytes() == previous
    assert len(partial) == 1
    assert not partial[0].exists()
    lock = destination.with_name(f"{destination.name}.lock")
    assert lock.exists()
    assert publication_lock_status(destination)["status"] == "inactive"
