"""Red contract for finite aggregate compiled-input hashing budgets.

The fake Path.stat and identity functions report large sparse-input sizes while
keeping fixture files tiny. The tests exercise the producer/inventory decisions
without allocating or hashing multi-gigabyte buffers.
"""
from __future__ import annotations

import stat
from pathlib import Path as RealPath
from types import SimpleNamespace
from typing import ClassVar

import pytest

from ladon import semantic_candidate_worker as candidate
from ladon import source_association_inventory as inventory
from ladon.source_association_io import _AssociationError

MIB = 1024**2
GIB = 1024**3
PER_FILE = 512 * MIB
PRIMARY_LIMIT = 16 * GIB
AUXILIARY_LIMIT = 8 * GIB
DIGEST = "sha256:" + "a" * 64


class SizedPath:
    """Real resolved path whose reported size is supplied by this fixture."""

    sizes: ClassVar[dict[str, int]] = {}

    def __init__(self, value: str | RealPath):
        self.path = RealPath(value)

    def resolve(self, *, strict: bool = False):
        return SizedPath(self.path.resolve(strict=strict))

    def stat(self):
        return SimpleNamespace(st_size=self.sizes[str(self.path)])

    def __str__(self):
        return str(self.path)


def _candidate_payload(rows):
    return {
        "leanVersion": "4.33.0",
        "leanCommit": "fixture-commit",
        "executablePath": "/fixture/lean",
        "universePolicy": "lean-level-mvar-succ-zero/v1",
        "importedModules": rows,
    }


def _write_candidate_inputs(tmp_path, count):
    rows = []
    sizes = {}
    for index in range(count):
        module = f"M{index:02d}"
        path = tmp_path / f"{module}.olean"
        path.write_bytes(b"tiny")
        rows.append({"module": module, "oleanPath": str(path)})
        sizes[str(path.resolve())] = PER_FILE
    return rows, sizes


def test_candidate_accepts_exact_16_gib_primary_total_without_gigabyte_files(tmp_path, monkeypatch):
    rows, sizes = _write_candidate_inputs(tmp_path, 32)
    SizedPath.sizes = sizes
    hashed = []
    monkeypatch.setattr(candidate, "Path", SizedPath)
    monkeypatch.setattr(candidate, "_digest_file", lambda path: hashed.append(str(path)) or DIGEST)

    artifact = candidate._environment_artifact(tmp_path, _candidate_payload(rows))

    assert len(artifact["payload"]["compiledModules"]) == 32
    assert len(hashed) == 34  # 32 modules, Lean executable, producer build identity
    assert "/fixture/lean" in hashed
    assert str(candidate.__file__) in hashed
    assert all(str(tmp_path / f"M{i:02d}.olean") in hashed for i in range(32))


def test_candidate_rejects_primary_total_one_byte_over_without_hashing_later_rows(tmp_path, monkeypatch):
    rows, sizes = _write_candidate_inputs(tmp_path, 34)
    sizes[str((tmp_path / "M32.olean").resolve())] = 1
    sizes[str((tmp_path / "M33.olean").resolve())] = 1
    SizedPath.sizes = sizes
    hashed = []
    monkeypatch.setattr(candidate, "Path", SizedPath)
    monkeypatch.setattr(candidate, "_digest_file", lambda path: hashed.append(str(path)) or DIGEST)

    with pytest.raises(ValueError, match="compiled-byte limit"):
        candidate._environment_artifact(tmp_path, _candidate_payload(rows))

    # The row that crosses the bound is rejected from its reported size before
    # its digest is read; no subsequent imported module or executable is hashed.
    assert str(tmp_path / "M32.olean") not in hashed
    assert str(tmp_path / "M33.olean") not in hashed
    assert str(tmp_path / "lean") not in hashed


def test_candidate_per_file_limit_still_rejects_before_hashing(tmp_path, monkeypatch):
    rows, sizes = _write_candidate_inputs(tmp_path, 1)
    sizes[str((tmp_path / "M00.olean").resolve())] = PER_FILE + 1
    SizedPath.sizes = sizes
    hashed = []
    monkeypatch.setattr(candidate, "Path", SizedPath)
    monkeypatch.setattr(candidate, "_digest_file", lambda path: hashed.append(str(path)) or DIGEST)

    with pytest.raises(ValueError, match="compiled-byte limit"):
        candidate._environment_artifact(tmp_path, _candidate_payload(rows))

    assert not hashed


def _inventory_fixture(tmp_path, count):
    files = {}
    rows = []
    for index in range(count):
        module = f"M{index:02d}"
        path = tmp_path / f"{module}.olean"
        path.write_bytes(b"tiny primary")
        files[module] = path
        rows.append({"module": module, "digest": DIGEST})
    return files, {"payload": {"compiledModules": rows}}


def _report_inventory_sizes(monkeypatch, sizes):
    original_stat = RealPath.stat

    def stat(path, *args, **kwargs):
        reported = sizes.get(str(path))
        if reported is not None:
            actual = original_stat(path, *args, **kwargs)
            return SimpleNamespace(
                st_size=reported,
                st_mode=actual.st_mode,
                st_dev=actual.st_dev,
                st_ino=actual.st_ino,
                st_mtime_ns=actual.st_mtime_ns,
                st_ctime_ns=actual.st_ctime_ns,
            )
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(RealPath, "stat", stat)


def test_source_inventory_accepts_exact_16_gib_primary_total(tmp_path, monkeypatch):
    files, environment = _inventory_fixture(tmp_path, 32)
    sizes = {str(path): PER_FILE for path in files.values()}
    calls = []
    _report_inventory_sizes(monkeypatch, sizes)

    def identity(path):
        calls.append(str(path))
        return DIGEST, sizes[str(path)]

    monkeypatch.setattr(inventory, "_file_identity", identity)
    observed = inventory._inventory(files, environment)

    assert observed["primaryBytes"] == PRIMARY_LIMIT
    assert len(calls) == 32


def test_source_inventory_rejects_primary_one_byte_over_without_hashing_later_rows(tmp_path, monkeypatch):
    files, environment = _inventory_fixture(tmp_path, 34)
    sizes = {str(path): PER_FILE for path in files.values()}
    sizes[str(files["M32"])] = 1
    sizes[str(files["M33"])] = 1
    calls = []
    _report_inventory_sizes(monkeypatch, sizes)

    def identity(path):
        calls.append(str(path))
        return DIGEST, sizes[str(path)]

    monkeypatch.setattr(inventory, "_file_identity", identity)
    with pytest.raises(_AssociationError, match="primary compiled modules exceed"):
        inventory._inventory(files, environment)

    # Inventory must preflight the next path's size before streaming its bytes.
    assert len(calls) == 32
    assert str(files["M32"]) not in calls
    assert str(files["M33"]) not in calls


def test_source_inventory_keeps_8_gib_auxiliary_limit_and_stops_after_crossing(tmp_path, monkeypatch):
    files, environment = _inventory_fixture(tmp_path, 18)
    sizes = {str(path): 1 for path in files.values()}
    sidecars = []
    for index, (module, path) in enumerate(sorted(files.items())):
        sidecar = RealPath(str(path) + ".server")
        sidecar.write_bytes(b"tiny sidecar")
        sidecars.append(sidecar)
        sizes[str(sidecar)] = PER_FILE if index < 16 else 1
    # Sixteen sidecars total exactly 8 GiB; the seventeenth byte crosses the
    # unchanged auxiliary ceiling, and the remaining sidecar must never be read.
    sizes[str(sidecars[16])] = 1
    calls = []

    def identity(path):
        key = str(path)
        calls.append(key)
        return DIGEST, sizes[key]

    monkeypatch.setattr(inventory, "_file_identity", identity)
    with pytest.raises(_AssociationError, match="compiled sidecars exceed"):
        inventory._inventory(files, environment)

    hashed_sidecars = [path for path in calls if path.endswith(".olean.server")]
    assert len(hashed_sidecars) == 17
    assert str(sidecars[17]) not in calls


def test_source_inventory_rejects_per_file_over_512_mib(tmp_path, monkeypatch):
    files, _ = _inventory_fixture(tmp_path, 1)
    calls = []
    from ladon import source_association_io

    assert source_association_io.MAX_EVIDENCE_FILE_BYTES == PER_FILE

    def fstat(_fd):
        calls.append("fstat")
        return SimpleNamespace(st_mode=stat.S_IFREG | 0o644, st_size=PER_FILE + 1)

    monkeypatch.setattr(source_association_io.os, "fstat", fstat)
    actual = files["M00"]
    with pytest.raises(_AssociationError, match="per-file limit"):
        source_association_io._file_identity(actual)
    assert calls == ["fstat"]
