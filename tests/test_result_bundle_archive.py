from __future__ import annotations

import stat
import zipfile
from pathlib import Path

import pytest

from ladon.result_bundle_archive import (
    extract_bundle_archive,
    write_bundle_archive,
)
from ladon.result_manifest_io import ResultManifestError


def _write_zip(path: Path, entries: list[tuple[str, bytes]], *, compression: int = zipfile.ZIP_STORED) -> None:
    with zipfile.ZipFile(path, "w", compression=compression) as archive:
        for name, data in entries:
            archive.writestr(name, data)


def _extract(path: Path, destination: Path, *, max_bytes: int = 1024, max_members: int = 10) -> None:
    destination.mkdir()
    extract_bundle_archive(path, destination, max_bytes=max_bytes, max_members=max_members)


def test_writer_is_deterministic_sorted_and_stored(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "z.txt").write_bytes(b"last")
    (source / "a.txt").write_bytes(b"first")
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    write_bundle_archive(source, first, max_bytes=1024, max_members=10)
    write_bundle_archive(source, second, max_bytes=1024, max_members=10)

    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        rows = archive.infolist()
        assert archive.namelist() == ["a.txt", "z.txt"]
        assert all(row.compress_type == zipfile.ZIP_STORED for row in rows)
        assert all(stat.S_ISREG(row.external_attr >> 16) for row in rows)
        assert len({row.date_time for row in rows}) == 1
        assert len({row.external_attr for row in rows}) == 1
        assert archive.comment == b""


@pytest.mark.parametrize("kind", ["file", "parent"])
def test_writer_rejects_source_symlinks(tmp_path: Path, kind: str) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret").write_text("private")
    source = tmp_path / "source"
    source.mkdir()
    if kind == "file":
        (source / "secret").symlink_to(outside / "secret")
    else:
        alias = tmp_path / "alias"
        alias.symlink_to(outside, target_is_directory=True)
        (source / "link").symlink_to(alias, target_is_directory=True)
        (source / "link" / "secret").resolve()
    with pytest.raises(ResultManifestError):
        write_bundle_archive(source, tmp_path / "out.zip", max_bytes=1024, max_members=10)


def test_writer_rejects_symlinked_root_component(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "file").write_text("safe")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(ResultManifestError):
        write_bundle_archive(alias, tmp_path / "out.zip", max_bytes=1024, max_members=10)


def test_writer_rejects_nonregular_source_entries(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    fifo = source / "pipe"
    try:
        fifo_path = fifo
        fifo_path.parent.mkdir(exist_ok=True)
        import os

        os.mkfifo(fifo_path)
    except (AttributeError, NotImplementedError, OSError):
        pytest.skip("FIFO creation is unavailable")
    assert not stat.S_ISREG(fifo.lstat().st_mode)
    with pytest.raises(ResultManifestError):
        write_bundle_archive(source, tmp_path / "out.zip", max_bytes=1024, max_members=10)


@pytest.mark.parametrize("limit", ["members", "bytes"])
def test_writer_enforces_member_and_output_byte_bounds(tmp_path: Path, limit: str) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "one").write_bytes(b"a" * 100)
    (source / "two").write_bytes(b"b" * 100)
    kwargs = {"max_bytes": 64 if limit == "bytes" else 1024, "max_members": 1 if limit == "members" else 10}
    with pytest.raises(ResultManifestError):
        write_bundle_archive(source, tmp_path / "out.zip", **kwargs)
    assert not (tmp_path / "out.zip").exists()


@pytest.mark.parametrize("compression", [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
def test_extractor_accepts_stored_and_deflated_files(tmp_path: Path, compression: int) -> None:
    archive = tmp_path / "input.zip"
    _write_zip(archive, [("assets/evidence.bin", b"evidence"), ("manifest.json", b"{}")], compression=compression)
    destination = tmp_path / "stage"

    _extract(archive, destination)

    assert (destination / "assets/evidence.bin").read_bytes() == b"evidence"
    assert (destination / "manifest.json").read_bytes() == b"{}"


@pytest.mark.parametrize("name", [
    "../escape", "a/../../escape", "/absolute", "C:/drive", "C:\\drive",
    "a\\b", "a//b", "./dot", "a/./b", "nul\x00name",
])
def test_extractor_rejects_unsafe_member_names(tmp_path: Path, name: str) -> None:
    archive = tmp_path / "input.zip"
    _write_zip(archive, [(name.replace("\x00", "_"), b"x")])
    if "\x00" in name:
        archive.write_bytes(archive.read_bytes().replace(b"nul_name", b"nul\x00name"))
    with pytest.raises(ResultManifestError):
        _extract(archive, tmp_path / "stage")


@pytest.mark.parametrize("names", [
    ["A/file", "a/file"],
    ["é.txt", "e\u0301.txt"],
    ["node", "node/child"],
    ["node/child", "node"],
])
def test_extractor_rejects_normalized_aliases_and_file_parent_collisions(tmp_path: Path, names: list[str]) -> None:
    archive = tmp_path / "input.zip"
    _write_zip(archive, [(name, b"x") for name in names])
    with pytest.raises(ResultManifestError):
        _extract(archive, tmp_path / "stage")


def test_extractor_rejects_expansion_and_member_limits(tmp_path: Path) -> None:
    archive = tmp_path / "input.zip"
    _write_zip(archive, [("a", b"a" * 30), ("b", b"b" * 30)], compression=zipfile.ZIP_DEFLATED)
    with pytest.raises(ResultManifestError):
        _extract(archive, tmp_path / "large", max_bytes=40)
    with pytest.raises(ResultManifestError):
        _extract(archive, tmp_path / "many", max_bytes=1024, max_members=1)


def test_extractor_rejects_unsupported_compression_and_archive_symlinks(tmp_path: Path) -> None:
    compressed = tmp_path / "bzip.zip"
    _write_zip(compressed, [("item", b"data")], compression=zipfile.ZIP_BZIP2)
    with pytest.raises(ResultManifestError):
        _extract(compressed, tmp_path / "bzip-stage")

    symlink_zip = tmp_path / "symlink.zip"
    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(symlink_zip, "w") as archive:
        archive.writestr(info, b"../../outside")
    with pytest.raises(ResultManifestError):
        _extract(symlink_zip, tmp_path / "symlink-stage")


def test_extractor_rejects_encrypted_entries(tmp_path: Path) -> None:
    archive = tmp_path / "encrypted-flag.zip"
    _write_zip(archive, [("item", b"data")])
    raw = bytearray(archive.read_bytes())
    local = raw.index(b"PK\x03\x04")
    raw[local + 6] |= 1
    central = raw.index(b"PK\x01\x02")
    raw[central + 8] |= 1
    archive.write_bytes(raw)
    with pytest.raises(ResultManifestError):
        _extract(archive, tmp_path / "encrypted-stage")


def test_extractor_rejects_archive_and_destination_symlinks(tmp_path: Path) -> None:
    source = tmp_path / "real.zip"
    _write_zip(source, [("file", b"ok")])
    alias = tmp_path / "alias.zip"
    alias.symlink_to(source)
    with pytest.raises(ResultManifestError):
        extract_bundle_archive(alias, tmp_path / "stage", max_bytes=1024, max_members=10)

    destination = tmp_path / "target"
    destination.mkdir()
    parent_alias = tmp_path / "parent-link"
    parent_alias.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ResultManifestError):
        extract_bundle_archive(source, parent_alias / "target", max_bytes=1024, max_members=10)
