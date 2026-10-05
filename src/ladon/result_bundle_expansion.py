"""Account actual ZIP expansion independently of untrusted declared lengths."""
from __future__ import annotations

import zipfile
import zlib

from ladon.result_manifest_io import ResultManifestError

_CHUNK = 64 * 1024


class _Sink:
    def __init__(self, target, limit):
        self.target, self.limit = target, limit
        self.count, self.crc = 0, 0

    def write(self, data):
        self.count += len(data)
        if self.count > self.limit:
            raise ResultManifestError('expanded archive byte limit exceeded')
        self.crc = zlib.crc32(data, self.crc)
        self.target.write(data)


def _inflate(decoder, block, sink):
    while block:
        data = decoder.decompress(block, min(_CHUNK, sink.limit - sink.count + 1))
        sink.write(data)
        if decoder.unused_data:
            raise ResultManifestError('ZIP member contains trailing compressed data')
        block = decoder.unconsumed_tail


def copy_zip_member(archive, info, target, remaining):
    """Use ZipFile header/overlap checks, but distrust its expanded-size cap."""
    # Opening validates the local name/header and overlapping member ranges.
    # No ZipExtFile.read(): it truncates expansion at the supplied file_size.
    with archive.open(info, 'r'):
        offset = archive.fp.tell()
    archive.fp.seek(offset)
    sink = _Sink(target, remaining)
    decoder = zlib.decompressobj(-15) if info.compress_type == zipfile.ZIP_DEFLATED else None
    left = info.compress_size
    try:
        while left:
            block = archive.fp.read(min(_CHUNK, left))
            if not block:
                raise ResultManifestError('truncated compressed ZIP member')
            left -= len(block)
            if decoder is None:
                sink.write(block)
            else:
                _inflate(decoder, block, sink)
    except zlib.error as exc:
        raise ResultManifestError('invalid compressed ZIP member') from exc
    if decoder is not None and not decoder.eof:
        raise ResultManifestError('incomplete compressed ZIP member')
    if sink.count != info.file_size or sink.crc != info.CRC:
        raise ResultManifestError('ZIP member expanded size or CRC mismatch')
    return sink.count
