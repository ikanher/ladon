"""Validate declared result identities without loading canonical Lean evidence.

Successful validation establishes only shape, content revisions, and internal
reference integrity. Target identities and reviews are supplied assertions;
canonical evidence resolution belongs to a separately gated integration.
"""

from __future__ import annotations

from typing import Any

from ladon._result_manifest_shape import validate_shape
from ladon.result_manifest_io import (
    MAX_MANIFEST_BYTES,
    ResultManifestError,
    canonical_json,
    content_revision,
)
from ladon.runset_validation import require_portable_relative_path


def validate_result_manifest(value: dict[str, Any]) -> dict[str, Any]:
    """Validate and detach a bounded manifest; never inspect referenced files."""

    validate_shape(value)
    if len(canonical_json(value)) > MAX_MANIFEST_BYTES:
        raise ResultManifestError("manifest exceeds the 16 MiB input limit")
    _aggregate_limits(value)
    _revision("manifest", value)
    tables = {key: _table(value[key], key) for key in ("claims", "targets", "links", "reviews")}
    _subjects(tables)
    for link in tables["links"].values():
        _link(link, tables)
    for review in tables["reviews"].values():
        _review(review, tables)
    # Own the returned snapshot so subsequent caller edits cannot change validation.
    import json

    return json.loads(canonical_json(value))


def _aggregate_limits(value: dict) -> None:
    entries = sum(len(value[key]) for key in ("claims", "targets", "links", "reviews"))
    entries += sum(len(row["components"]) for row in value["claims"])
    entries += sum(len(row["componentIds"]) + len(row["targetIds"]) for row in value["links"])
    entries += sum(len(row["targetRevisions"]) + len(row["differences"]) for row in value["reviews"])
    if entries > 100_000:
        raise ResultManifestError("manifest exceeds the 100,000 aggregate collection-entry limit")


def _table(rows: list[dict], label: str) -> dict[str, dict]:
    table = {row["id"]: row for row in rows}
    if len(table) != len(rows):
        raise ResultManifestError(f"{label}: duplicate ID")
    return table


def _revision(kind: str, row: dict) -> None:
    if row["revision"] != content_revision(kind, row):
        raise ResultManifestError(f"{kind}: content revision mismatch")


def _subjects(tables: dict[str, dict]) -> None:
    for claim in tables["claims"].values():
        _revision("claim", claim)
    observed: dict[tuple, str] = {}
    for target in tables["targets"].values():
        _revision("target", target)
        _target_path(target)
        key = (target["name"], canonical_json(target["source"]), canonical_json(target["environment"]))
        previous = observed.setdefault(key, target["typeText"])
        if previous != target["typeText"]:
            raise ResultManifestError("targets: contradictory type text for the same source/environment")


def _target_path(target: dict) -> None:
    try:
        require_portable_relative_path(target["source"]["path"], "target source")
    except ValueError as exc:
        raise ResultManifestError("target source path must be portable and non-escaping") from exc


def _require_reference(identifier: str, table: dict, label: str) -> dict:
    if identifier not in table:
        raise ResultManifestError(f"{label}: dangling internal reference")
    return table[identifier]


def _link(link: dict, tables: dict[str, dict]) -> None:
    claim = _require_reference(link["claimId"], tables["claims"], "link claim")
    if not set(link["componentIds"]) <= set(claim["components"]):
        raise ResultManifestError("link: unknown claim component")
    for identifier in link["targetIds"]:
        _require_reference(identifier, tables["targets"], "link target")


def _review(review: dict, tables: dict[str, dict]) -> None:
    link = _require_reference(review["linkId"], tables["links"], "review link")
    revisions = review["targetRevisions"]
    identifiers = {row["targetId"] for row in revisions}
    if len(identifiers) != len(revisions):
        raise ResultManifestError("review: duplicate target revision")
    if (
        review["linkDigest"] == content_revision("link", link)
        and identifiers != set(link["targetIds"])
    ):
        raise ResultManifestError("review: target set contradicts bound link")
    if review["status"] == "reviewed-with-differences" and not review["differences"]:
        raise ResultManifestError("review: differences status requires anchored differences")


def review_currency(review: dict, link: dict, claim: dict, targets: dict) -> str:
    """Compare declared revisions; this does not authenticate the review itself."""

    expected = {identifier: targets[identifier]["revision"] for identifier in link["targetIds"]}
    supplied = {row["targetId"]: row["revision"] for row in review["targetRevisions"]}
    matches = (
        review["linkDigest"] == content_revision("link", link)
        and review["claimRevision"] == claim["revision"]
        and supplied == expected
    )
    return "current" if matches else "historical"
