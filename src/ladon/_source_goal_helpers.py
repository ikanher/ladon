"""Compose private standalone Lean helpers with their shared expression codec."""
from __future__ import annotations

from importlib import resources
from pathlib import Path

from ladon.source_association_io import _AssociationError, _digest, _read_regular

_MARKER = b'-- LADON_EXPR_GRAPH\n'
_LIMIT = 1024 * 1024


def helper_source(path: Path) -> bytes:
    source = _read_regular(path, _LIMIT)
    if _MARKER not in source:
        return source
    if source.count(_MARKER) != 1:
        raise _AssociationError('unavailable', 'helper-composition', 'helper codec marker is ambiguous')
    codec = Path(str(resources.files('ladon').joinpath('lean', 'ladon_expr_graph.lean')))
    return source.replace(_MARKER, _read_regular(codec, _LIMIT) + b'\n')


def stage_helper(original: Path, directory: Path) -> tuple[Path, str]:
    source = helper_source(original)
    path = directory / original.name
    path.write_bytes(source)
    return path, _digest(source)


def verify_helper(original: Path, digest: str) -> None:
    if _digest(helper_source(original)) != digest:
        raise _AssociationError('stale', 'helper-changed', 'helper or shared codec changed during operation')
