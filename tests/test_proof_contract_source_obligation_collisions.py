"""Existing generated artifacts are compared without unbounded file reads."""

import importlib
from pathlib import Path

import pytest


def test_oversized_existing_probe_is_rejected_before_an_unbounded_read(tmp_path, monkeypatch):
    staging = importlib.import_module("ladon._proof_contract_source_obligations_staging")
    target = tmp_path / "Probe.lean"
    target.write_bytes(b"x" * (9 * 1024**2))
    original = Path.read_bytes
    seen = []

    def read(path):
        data = original(path)
        seen.append(len(data))
        return data

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError):
        staging._write_probe(target, b"expected source")
    assert seen == []


def test_exact_existing_probe_is_preserved(tmp_path):
    staging = importlib.import_module("ladon._proof_contract_source_obligations_staging")
    target = tmp_path / "Probe.lean"
    expected = b"expected source"
    target.write_bytes(expected)
    staging._write_probe(target, expected)
    assert target.read_bytes() == expected


def test_symlink_collision_does_not_modify_its_target(tmp_path):
    staging = importlib.import_module("ladon._proof_contract_source_obligations_staging")
    target = tmp_path / "Probe.lean"
    original = tmp_path / "original"
    original.write_bytes(b"original")
    target.symlink_to(original)
    with pytest.raises(ValueError):
        staging._write_probe(target, b"expected source")
    assert original.read_bytes() == b"original"
