"""Closed portable bundle selection and inventory contracts."""
from __future__ import annotations

import json
from importlib.resources import files

from ladon._result_manifest_shape import validate_document_shape
from ladon.result_manifest_io import MAX_MANIFEST_BYTES, ResultManifestError, canonical_json

DEFAULT_BUNDLE_BYTES = 256 * 1024 * 1024
DEFAULT_BUNDLE_MEMBERS = 10_000
SINGLETON_ROLES = frozenset({'manifest', 'guide', 'assessments', 'lineage'})


def bundle_bounds(max_bytes, max_members):
    """Reject bool, infinity and unbounded archive configurations."""
    for value in (max_bytes, max_members):
        if type(value) is not int or not 1 <= value <= 2**63 - 1:
            raise ResultManifestError('bundle limits must be positive finite integers')


def _shape(value, name):
    encoded = canonical_json(value)
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise ResultManifestError('bundle metadata exceeds 16 MiB limit')
    schema = json.loads(files('ladon.schemas').joinpath(name).read_text())
    validate_document_shape(value, schema)
    return json.loads(encoded)


def included(entry):
    """Both disclosure and permission are required before opening a source."""
    return entry['disclosure'] == 'supplied' and entry['permission'] == 'include'


def _unique(rows, key, label):
    values = [row[key] for row in rows]
    if len(values) != len(set(values)):
        raise ResultManifestError(f'duplicate bundle {label}')


def _roles(rows):
    for role in SINGLETON_ROLES:
        if sum(row['role'] == role for row in rows) > 1:
            raise ResultManifestError(f'duplicate bundle role: {role}')
    for row in rows:
        if row['role'] == 'review' and 'review' not in row:
            raise ResultManifestError('review attachment requires author, revision and scope')


def _shared(value):
    _unique(value['lineageBindings'], 'entryId', 'lineage binding')
    _unique(value['externalDependencies'], 'id', 'external dependency')


def validate_bundle_selection(value):
    """Validate disclosure before looking at any selected filesystem paths."""
    value = _shape(value, 'ladon-result-bundle-selection-v1.schema.json')
    _unique(value['entries'], 'id', 'selection ID')
    _shared(value)
    for row in value['entries']:
        if row['id'] == 'manifest':
            raise ResultManifestError('manifest is a reserved selection ID')
        required = 'path' if included(row) else 'reason'
        if required not in row:
            raise ResultManifestError(f'bundle selection requires {required}')
    _roles([row for row in value['entries'] if included(row)])
    return value


def validate_bundle_index(value):
    """The inventory is exact; omitted content has no path or content hash."""
    value = _shape(value, 'ladon-result-bundle-v1.schema.json')
    rows = value['inventory']
    _unique(rows + value['omissions'], 'id', 'member ID')
    _unique(rows, 'path', 'member path')
    _roles(rows)
    _shared(value)
    manifest = [row for row in rows if row['role'] == 'manifest']
    if len(manifest) != 1 or manifest[0]['path'] != 'manifest.json' or manifest[0]['id'] != 'manifest':
        raise ResultManifestError('bundle must inventory exactly one manifest.json')
    if any(row['path'] == 'bundle.json' or row['path'].startswith('missing/') for row in rows):
        raise ResultManifestError('bundle inventory uses a reserved path')
    return value
