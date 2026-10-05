"""Safe local-file primitives shared by result bundle export and archive IO."""
from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO

from ladon.result_manifest_io import ResultManifestError


def _open_directory(path: Path) -> int:
    """Open a directory by walking every component without following symlinks."""
    raw = os.fspath(path)
    absolute = os.path.abspath(raw)
    parts = Path(absolute).parts
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(parts[0], flags)
    try:
        for part in parts[1:]:
            next_fd = os.open(part, flags | nofollow, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            raise ResultManifestError("path component is not a directory")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _open_parent_and_name(path: Path) -> tuple[int, str]:
    absolute = Path(os.path.abspath(os.fspath(path)))
    parent_fd = _open_directory(absolute.parent)
    return parent_fd, absolute.name


def _signature(st: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (st.st_dev, st.st_ino, st.st_mode, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


@contextmanager
def safe_open(path: str | os.PathLike[str]) -> Iterator[BinaryIO]:
    """Open one stable regular file, refusing symlinks in any path component."""
    target = Path(path)
    try:
        parent_fd, name = _open_parent_and_name(target)
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        finally:
            os.close(parent_fd)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            os.close(fd)
            raise ResultManifestError("input is not a regular file")
        stream = os.fdopen(fd, "rb")
        try:
            yield stream
            after = os.fstat(stream.fileno())
            pfd, pname = _open_parent_and_name(target)
            try:
                current = os.stat(pname, dir_fd=pfd, follow_symlinks=False)
            finally:
                os.close(pfd)
            if _signature(before) != _signature(after) or (current.st_dev, current.st_ino) != (before.st_dev, before.st_ino):
                raise ResultManifestError("input changed while it was being read")
        finally:
            stream.close()
    except ResultManifestError:
        raise
    except (OSError, ValueError) as exc:
        raise ResultManifestError("cannot safely open regular input") from exc


def copy_regular(source: str | os.PathLike[str], destination: BinaryIO, remaining: int) -> tuple[int, str]:
    if not isinstance(remaining, int) or isinstance(remaining, bool) or remaining < 0:
        raise ResultManifestError("remaining byte limit must be a non-negative integer")
    total = 0
    digest = hashlib.sha256()
    try:
        with safe_open(source) as stream:
            while True:
                block = stream.read(min(1024 * 1024, remaining - total + 1))
                if not block:
                    break
                total += len(block)
                if total > remaining:
                    raise ResultManifestError("expanded byte limit exceeded")
                digest.update(block)
                destination.write(block)
    except ResultManifestError:
        raise
    except OSError as exc:
        raise ResultManifestError("cannot copy regular file") from exc
    return total, "sha256:" + digest.hexdigest()


def regular_files(root: str | os.PathLike[str], max_members: int) -> list[str]:
    if not isinstance(max_members, int) or isinstance(max_members, bool) or max_members <= 0:
        raise ResultManifestError("max_members must be a positive integer")
    try:
        root_fd = _open_directory(Path(root))
    except ResultManifestError:
        raise
    except OSError as exc:
        raise ResultManifestError("source root is not a safe directory") from exc
    found: list[str] = []

    def walk(fd: int, prefix: str) -> None:
        try:
            with os.scandir(fd) as entries:
                rows = sorted(entries, key=lambda item: item.name)
            for entry in rows:
                name = entry.name
                rel = f"{prefix}/{name}" if prefix else name
                try:
                    info = entry.stat(follow_symlinks=False)
                except OSError as exc:
                    raise ResultManifestError("cannot inspect source entry") from exc
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(name, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0), dir_fd=fd)
                    try:
                        walk(child, rel)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(info.st_mode):
                    found.append(rel)
                    if len(found) > max_members:
                        raise ResultManifestError("member count limit exceeded")
                else:
                    raise ResultManifestError("source tree contains a symlink or non-regular entry")
        except ResultManifestError:
            raise
        except OSError as exc:
            raise ResultManifestError("cannot safely enumerate source tree") from exc

    try:
        walk(root_fd, "")
    finally:
        os.close(root_fd)
    validate_member_paths(found)
    return sorted(found)


def _check_member_spelling(original: str) -> None:
    if not isinstance(original, str) or not original or "\x00" in original or "\\" in original:
        raise ResultManifestError("unsafe archive member path")
    if original.startswith("/") or original.endswith("/") or (len(original) >= 2 and original[1] == ":"):
        raise ResultManifestError("archive member path must be portable and relative")


def _member_parts(original: str) -> list[str]:
    _check_member_spelling(original)
    parts = original.split("/")
    if any(part in ("", ".", "..") or ":" in part for part in parts):
        raise ResultManifestError("archive member path has an unsafe segment")
    return parts


def _normalized_member(original: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFC", original)
    if normalized != original:
        raise ResultManifestError("archive member path is not NFC normalized")
    return normalized.casefold()


def _check_parent_collisions(files: set[str], canonical: dict[str, str]) -> None:
    for name in files:
        segments = name.split("/")
        for index in range(1, len(segments)):
            parent = "/".join(segments[:index])
            if parent in files or parent.casefold() in canonical:
                raise ResultManifestError("archive members contain a file/parent collision")


def validate_member_paths(names: list[str] | tuple[str, ...]) -> None:
    canonical: dict[str, str] = {}
    files: set[str] = set()
    for original in names:
        _member_parts(original)
        key = _normalized_member(original)
        if key in canonical:
            raise ResultManifestError("duplicate or casefold-aliased archive member")
        canonical[key] = original
        files.add(original)
    _check_parent_collisions(files, canonical)
    _check_directory_aliases(files)


def _check_directory_aliases(names):
    spellings = {}
    for name in names:
        parts = name.split('/')
        for index in range(1, len(parts)):
            path = '/'.join(parts[:index])
            key = path.casefold()
            if key in spellings and spellings[key] != path:
                raise ResultManifestError('archive directory components alias each other')
            spellings[key] = path
