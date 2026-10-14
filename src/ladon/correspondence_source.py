"""Exact Unicode line spans and UTF-8 byte positions for prose anchors."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.investigation import SourceReader


def source_positions(
    record: Mapping[str, Any], source_root: Path
) -> tuple[dict[str, Any], dict[str, Any], str]:
    source = record["source"]
    reader = SourceReader(source_root)
    quote = reader.span(source, "quote")
    root = reader.root
    path = (root / source["path"]).resolve(strict=True)
    if not path.is_relative_to(root):
        raise ValueError("source escapes explicit root")
    from ladon.source_association_io import _read_regular

    raw = _read_regular(path, 8 * 1024**2)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != source["sha256"]:
        raise ValueError("source changed while native source-map anchor was prepared")
    lines = raw.decode("utf-8").splitlines(keepends=True)
    start_line = source["startLine"]
    end_line = source["endLine"]
    start_byte = sum(len(row.encode("utf-8")) for row in lines[: start_line - 1])
    final_line = lines[end_line - 1].splitlines()[0]
    end_byte = sum(len(row.encode("utf-8")) for row in lines[: end_line - 1]) + len(
        final_line.encode("utf-8")
    )
    return (
        {"byte": start_byte, "line": start_line, "column": 1},
        {"byte": end_byte, "line": end_line, "column": len(final_line) + 1},
        quote,
    )
