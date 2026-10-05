"""Require every physical ZIP record to belong to the declared member set."""
from __future__ import annotations

import os
import struct

from ladon.result_manifest_io import ResultManifestError


def _read(raw, length):
    data = raw.read(length)
    if len(data) != length:
        raise ResultManifestError('truncated ZIP layout')
    return data


def _end_record(raw, count=None):
    size = os.fstat(raw.fileno()).st_size
    start = max(0, size - 65557)
    raw.seek(start)
    tail = raw.read()
    offset = tail.rfind(b'PK\x05\x06')
    if offset < 0 or len(tail) - offset < 22:
        raise ResultManifestError('missing ZIP end record')
    fields = struct.unpack('<4s4H2IH', tail[offset:offset + 22])
    _, disk, directory_disk, disk_count, total, length, position, comment = fields
    if disk or directory_disk or disk_count != total or (count is not None and total != count):
        raise ResultManifestError('unsupported split or ZIP64 archive')
    if offset + 22 + comment != len(tail) or position + length != start + offset:
        raise ResultManifestError('unindexed ZIP bytes outside the directory')
    return position, length, total


def _central_directory(raw, offset, length, count):
    raw.seek(offset)
    for _ in range(count):
        header = _read(raw, 46)
        if header[:4] != b'PK\x01\x02':
            raise ResultManifestError('invalid ZIP central directory')
        if struct.unpack_from('<H', header, 34)[0]:
            raise ResultManifestError('split-volume ZIP member is unsupported')
        name, extra, comment = struct.unpack_from('<3H', header, 28)
        _read(raw, name + extra + comment)
    if raw.tell() != offset + length:
        raise ResultManifestError('unindexed ZIP directory records')


def _descriptor(raw, info, boundary):
    length = boundary - raw.tell()
    if length not in (12, 16):
        raise ResultManifestError('invalid ZIP descriptor extent')
    data = _read(raw, length)
    if length == 16:
        if data[:4] != b'PK\x07\x08':
            raise ResultManifestError('invalid ZIP descriptor signature')
        data = data[4:]
    values = struct.unpack('<3I', data)
    if values != (info.CRC, info.compress_size, info.file_size):
        raise ResultManifestError('ZIP descriptor disagrees with member')
    return raw.tell()


def _local_end(raw, info, offset, central):
    if info.header_offset != offset:
        raise ResultManifestError('unindexed ZIP local records or padding')
    raw.seek(offset)
    header = _read(raw, 30)
    if header[:4] != b'PK\x03\x04':
        raise ResultManifestError('invalid ZIP local header')
    flags, method = struct.unpack_from('<2H', header, 6)
    crc, compressed, expanded, name, extra = struct.unpack_from('<3I2H', header, 14)
    if flags != info.flag_bits or method != info.compress_type:
        raise ResultManifestError('ZIP local and central flags disagree')
    if not flags & 8 and (crc, compressed, expanded) != (info.CRC, info.compress_size, info.file_size):
        raise ResultManifestError('ZIP local and central sizes disagree')
    end = offset + 30 + name + extra + info.compress_size
    if end > central:
        raise ResultManifestError('ZIP member overlaps its directory')
    raw.seek(end)
    return _descriptor(raw, info, central) if flags & 8 else end


def validate_zip_layout(raw, infos):
    """Reject self-extracting, split, ZIP64 and unindexed record layouts."""
    central, length, _ = _end_record(raw, len(infos))
    _central_directory(raw, central, length, len(infos))
    offset = 0
    ordered = sorted(infos, key=lambda item: item.header_offset)
    for index, info in enumerate(ordered):
        boundary = ordered[index + 1].header_offset if index + 1 < len(ordered) else central
        offset = _local_end(raw, info, offset, boundary)
    if offset != central:
        raise ResultManifestError('unindexed bytes before ZIP directory')


def preflight_zip_directory(raw, max_members):
    """Bound the actual central records before ZipFile allocates member objects."""
    central, length, count = _end_record(raw)
    if count > max_members:
        raise ResultManifestError('archive member count limit exceeded')
    _central_directory(raw, central, length, count)
