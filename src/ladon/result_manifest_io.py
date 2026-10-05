"""Bounded artifact input and domain-separated revisions for result manifests."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_RESULT_BYTES = 32 * 1024
REVISION_KINDS = frozenset({"manifest", "claim", "target", "link"})


class ResultManifestError(ValueError):
    """The supplied artifact violates the experimental result contract."""


def canonical_json(value: Any) -> bytes:
    """Encode portable JSON without normalizing user-supplied mathematical text."""

    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ResultManifestError("value is not bounded portable JSON") from exc


def content_revision(kind: str, value: dict[str, Any]) -> str:
    """Hash one object, excluding only its own revision, in a named domain."""

    if kind not in REVISION_KINDS:
        raise ResultManifestError("unsupported revision kind")
    body = {key: item for key, item in value.items() if key != "revision"}
    prefix = f"ladon-result-manifest-v1/{kind}\0".encode()
    return "sha256:" + hashlib.sha256(prefix + canonical_json(body)).hexdigest()


def load_result_manifest(path: Path) -> dict[str, Any]:
    """Read one bounded regular file; never dereference artifact references."""

    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode):
            raise ResultManifestError("manifest input must be a regular file")
        if metadata.st_size > MAX_MANIFEST_BYTES:
            raise ResultManifestError("manifest exceeds the 16 MiB input limit")
        raw = stream.read(MAX_MANIFEST_BYTES + 1)
    return parse_result_manifest(raw)


def parse_result_manifest(raw: bytes) -> dict[str, Any]:
    """Reject ambiguous or excessively nested JSON before computing identities."""

    if len(raw) > MAX_MANIFEST_BYTES:
        raise ResultManifestError("manifest exceeds the 16 MiB input limit")
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ResultManifestError("manifest requires strict UTF-8 JSON with unique keys") from exc
    if not isinstance(value, dict):
        raise ResultManifestError("manifest must be a JSON object")
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ResultManifestError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise ResultManifestError("non-finite JSON value")
