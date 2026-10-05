"""Deterministic, bounded ZIP transport for result bundles."""
from __future__ import annotations

import os
import secrets
import stat
import zipfile
from pathlib import Path

from ladon.result_bundle_expansion import copy_zip_member
from ladon.result_bundle_files import (
    _open_directory,
    regular_files,
    safe_open,
    validate_member_paths,
)
from ladon.result_bundle_zip_layout import preflight_zip_directory, validate_zip_layout
from ladon.result_manifest_io import ResultManifestError

_CHUNK = 1024 * 1024


def _positive_limits(max_bytes: int, max_members: int) -> None:
    for value, label in ((max_bytes, "max_bytes"), (max_members, "max_members")):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ResultManifestError(f"{label} must be a positive integer")


def _temp_name(prefix: str) -> str:
    return f".{prefix}.{os.getpid()}.{secrets.token_hex(8)}.tmp"


def _open_output_parent(output: Path) -> tuple[int, str]:
    absolute = Path(os.path.abspath(os.fspath(output)))
    try:
        parent = _open_directory(absolute.parent)
        try:
            existing = os.stat(absolute.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            if not stat.S_ISREG(existing.st_mode):
                os.close(parent)
                raise ResultManifestError("output destination must be a regular file")
        return parent, absolute.name
    except ResultManifestError:
        raise
    except OSError as exc:
        raise ResultManifestError("output parent is not a safe directory") from exc


def _write_member(archive: zipfile.ZipFile, root: Path, name: str, remaining: int) -> int:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.extra = b""
    info.comment = b""
    written = 0
    try:
        with safe_open(root / name) as source, archive.open(info, "w") as target:
            while True:
                block = source.read(min(_CHUNK, remaining - written + 1))
                if not block:
                    break
                written += len(block)
                if written > remaining:
                    raise ResultManifestError("archive expanded byte limit exceeded")
                target.write(block)
    except ResultManifestError:
        raise
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, ValueError) as exc:
        raise ResultManifestError("cannot safely write archive member") from exc
    return written


def write_bundle_archive(root: str | os.PathLike[str], output: str | os.PathLike[str], *, max_bytes: int, max_members: int) -> None:
    _positive_limits(max_bytes, max_members)
    source_root = Path(root)
    names = regular_files(source_root, max_members)
    parent_fd, final_name = _open_output_parent(Path(output))
    temp_name = _temp_name("result-bundle")
    fd = -1
    try:
        fd = os.open(temp_name, os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0), 0o600, dir_fd=parent_fd)
        with os.fdopen(fd, "w+b") as raw:
            fd = -1
            with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
                archive.comment = b""
                total = 0
                for name in names:
                    total += _write_member(archive, source_root, name, max_bytes - total)
            raw.flush()
            os.fsync(raw.fileno())
            if os.fstat(raw.fileno()).st_size > max_bytes:
                raise ResultManifestError("archive output byte limit exceeded")
        os.replace(temp_name, final_name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
    except ResultManifestError:
        raise
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, ValueError) as exc:
        raise ResultManifestError("cannot safely publish ZIP archive") from exc
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(temp_name, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        os.close(parent_fd)


def _mkdirs(destination_fd: int, parts: list[str]) -> tuple[int, str]:
    current = os.dup(destination_fd)
    try:
        for segment in parts[:-1]:
            try:
                os.mkdir(segment, 0o700, dir_fd=current)
            except FileExistsError:
                pass
            next_fd = os.open(segment, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0), dir_fd=current)
            os.close(current)
            current = next_fd
        return current, parts[-1]
    except OSError as exc:
        os.close(current)
        raise ResultManifestError("cannot create safe extraction path") from exc


def _extract_one(archive: zipfile.ZipFile, info: zipfile.ZipInfo, destination_fd: int, remaining: int) -> int:
    parts = info.filename.split("/")
    parent_fd, name = _mkdirs(destination_fd, parts)
    fd = -1
    total = 0
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent_fd)
        with os.fdopen(fd, "wb") as target:
            fd = -1
            total = copy_zip_member(archive, info, target, remaining)
            target.flush()
            os.fsync(target.fileno())
    except ResultManifestError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError, ValueError) as exc:
        raise ResultManifestError("cannot safely extract archive member") from exc
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent_fd)
    return total


def _validate_zip_infos(infos: list[zipfile.ZipInfo], max_members: int) -> None:
    if len(infos) > max_members:
        raise ResultManifestError("archive member count limit exceeded")
    names: list[str] = []
    for info in infos:
        name = getattr(info, "orig_filename", info.filename)
        if name != info.filename or "\x00" in name:
            raise ResultManifestError("archive member name contains invalid encoding or NUL")
        names.append(name)
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode) or info.is_dir() or stat.S_IFMT(mode) not in (0, stat.S_IFREG):
            raise ResultManifestError("archive entry is not a regular file")
        if info.flag_bits & 1:
            raise ResultManifestError("encrypted archive entries are forbidden")
        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise ResultManifestError("unsupported archive compression method")
    validate_member_paths(names)


def _extract_infos(zipped: zipfile.ZipFile, infos: list[zipfile.ZipInfo], dest_fd: int, max_bytes: int) -> None:
    total = 0
    for info in infos:
        total += _extract_one(zipped, info, dest_fd, max_bytes - total)


def extract_bundle_archive(archive: str | os.PathLike[str], destination: str | os.PathLike[str], *, max_bytes: int, max_members: int) -> None:
    _positive_limits(max_bytes, max_members)
    destination_path = Path(destination)
    try:
        dest_fd = _open_directory(destination_path)
        with os.scandir(dest_fd) as entries:
            if next(entries, None) is not None:
                raise ResultManifestError("extraction destination must be empty")
    except ResultManifestError:
        raise
    except OSError as exc:
        raise ResultManifestError("extraction destination must be an existing safe directory") from exc
    try:
        with safe_open(archive) as raw:
            if os.fstat(raw.fileno()).st_size > max_bytes:
                raise ResultManifestError("archive input byte limit exceeded")
            try:
                preflight_zip_directory(raw, max_members)
                with zipfile.ZipFile(raw, "r") as zipped:
                    infos = zipped.infolist()
                    _validate_zip_infos(infos, max_members)
                    validate_zip_layout(raw, infos)
                    _extract_infos(zipped, infos, dest_fd, max_bytes)
            except ResultManifestError:
                raise
            except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, ValueError) as exc:
                raise ResultManifestError("invalid or unsafe ZIP archive") from exc
    finally:
        os.close(dest_fd)
