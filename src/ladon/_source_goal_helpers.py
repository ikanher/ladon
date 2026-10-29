"""Compose private standalone Lean helpers with their shared expression codec."""
from __future__ import annotations

from importlib import resources
from pathlib import Path

from ladon.source_association_io import _AssociationError, _digest, _read_regular

_MATERIALS = (
    (b'-- LADON_EXPR_GRAPH\n', 'ladon_expr_graph.lean'),
    (b'-- LADON_ROUNDTRIP_PRINT\n', 'ladon_roundtrip_print.lean'),
)
_LIMIT = 1024 * 1024


def helper_source(path: Path) -> bytes:
    source = _read_regular(path, _LIMIT)
    for marker, name in _MATERIALS:
        if marker not in source:
            continue
        if source.count(marker) != 1:
            raise _AssociationError('unavailable', 'helper-composition', 'helper material marker is ambiguous')
        material = Path(str(resources.files('ladon').joinpath('lean', name)))
        source = source.replace(marker, _read_regular(material, _LIMIT) + b'\n')
    return source


def stage_helper(original: Path, directory: Path) -> tuple[Path, str]:
    source = helper_source(original)
    path = directory / original.name
    path.write_bytes(source)
    return path, _digest(source)


def verify_helper(original: Path, digest: str) -> None:
    if _digest(helper_source(original)) != digest:
        raise _AssociationError('stale', 'helper-changed', 'helper or shared codec changed during operation')
