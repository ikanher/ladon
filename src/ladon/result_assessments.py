"""Validate attributable assessments attached to a result manifest.

Assessments are retained as attributed,
revision-scoped observations and never change manifest or checker authority.
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from ladon._result_manifest_shape import validate_document_shape
from ladon.result_manifest import validate_result_manifest
from ladon.result_manifest_io import (
    MAX_MANIFEST_BYTES,
    ResultManifestError,
    canonical_json,
)

_MAX_AGGREGATE_ENTRIES = 100_000


def _schema() -> dict[str, Any]:
    try:
        return json.loads(files('ladon.schemas').joinpath('ladon-result-assessments-v1.schema.json').read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("assessment schema is unavailable or invalid") from exc


def validate_result_assessments(value: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate and detach a companion assessment document against a valid manifest."""

    owned_manifest = validate_result_manifest(manifest)
    if not isinstance(value, dict):
        raise ResultManifestError("assessments: expected object")
    encoded = canonical_json(value)
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise ResultManifestError("assessments exceed the 16 MiB input limit")
    schema = _schema()
    validate_document_shape(value, schema)
    _aggregate_limits(value)
    if value["resultId"] != owned_manifest["resultId"]:
        raise ResultManifestError("assessments: result ID does not match manifest")

    _validate_rows(value, owned_manifest)
    return json.loads(encoded)


def _validate_rows(value, manifest):
    claims, targets, mappings = _context(manifest)
    identifiers = [row['id'] for row in value['assessments']]
    if len(set(identifiers)) != len(identifiers):
        raise ResultManifestError('assessments: duplicate ID')
    for row in value['assessments']:
        _validate_row(row, value, manifest, claims, targets, mappings)


def _validate_row(row, companion, manifest, claims, targets, mappings):
    claim = claims.get(row['claimId'])
    if claim is None or row['componentId'] not in claim['components']:
        raise ResultManifestError('assessment: unknown claim or component')
    target_ids = [item['targetId'] for item in row['targetRevisions']]
    if len(set(target_ids)) != len(target_ids):
        raise ResultManifestError('assessment: duplicate target revision')
    if any(identifier not in targets for identifier in target_ids):
        raise ResultManifestError('assessment: unknown target ID')
    current = companion['manifestRevision'] == manifest['revision'] and row['claimRevision'] == claim['revision']
    if current and set(target_ids) != mappings.get((row['claimId'], row['componentId']), set()):
        raise ResultManifestError('assessment: target set contradicts current component mapping')


def assessment_currency(row: dict[str, Any], companion: dict[str, Any], manifest: dict[str, Any]) -> str:
    """Return current only when all supplied claim/target/mapping revisions agree."""

    return _currency(row, companion, manifest, _context(manifest))


def assessment_currencies(companion, manifest):
    """Classify an already validated population without repeated full validation."""
    context = _context(manifest)
    return [_currency(row, companion, manifest, context) for row in companion['assessments']]


def _context(manifest):
    return ({r['id']: r for r in manifest['claims']},
            {r['id']: r for r in manifest['targets']}, _component_target_sets(manifest))


def _currency(row, companion, owned_manifest, context):

    claims, targets, mappings = context
    claim = claims[row['claimId']]
    expected = mappings.get((row['claimId'], row['componentId']), set())
    supplied = {entry['targetId']: entry['revision'] for entry in row['targetRevisions']}
    current = all((companion['resultId'] == owned_manifest['resultId'],
                   companion['manifestRevision'] == owned_manifest['revision'],
                   row['claimRevision'] == claim['revision'], set(supplied) == expected))
    revisions_match = all(supplied.get(identifier) == targets[identifier]['revision'] for identifier in expected)
    return 'current' if current and revisions_match else 'historical'


def _component_target_sets(manifest: dict[str, Any]) -> dict[tuple[str, str], set[str]]:
    result: dict[tuple[str, str], set[str]] = {}
    for link in manifest["links"]:
        for component_id in link["componentIds"]:
            result.setdefault((link["claimId"], component_id), set()).update(link["targetIds"])
    return result


def _aggregate_limits(value: dict[str, Any]) -> None:
    entries = len(value["assessments"])
    for row in value["assessments"]:
        entries += len(row["targetRevisions"])
        entries += len(row["differences"])
        entries += len(row["evidenceRefs"])
    if entries > _MAX_AGGREGATE_ENTRIES:
        raise ResultManifestError("assessments exceed the 100,000 aggregate collection-entry limit")
