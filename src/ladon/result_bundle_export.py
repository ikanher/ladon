"""Assemble explicitly disclosed immutable payloads in a private stage."""
from __future__ import annotations

import os
from pathlib import Path

from ladon.result_bundle_contract import included, validate_bundle_index, validate_bundle_selection
from ladon.result_bundle_files import copy_regular, safe_open
from ladon.result_lineage_inputs import validate_lineage_inputs
from ladon.result_manifest import validate_result_manifest
from ladon.result_manifest_io import (
    MAX_MANIFEST_BYTES,
    ResultManifestError,
    canonical_json,
    parse_result_manifest,
)


def read_document(path):
    """Read bounded metadata without following source symlinks."""
    with safe_open(path) as stream:
        return parse_result_manifest(stream.read(MAX_MANIFEST_BYTES + 1))


def _source(base, value):
    return Path(os.path.abspath(base / value))


def _journal_guard(path):
    for suffix in ('-wal', '-journal'):
        sidecar = Path(str(path) + suffix)
        if sidecar.is_symlink() or (sidecar.exists() and sidecar.stat().st_size):
            raise ResultManifestError('lineage database has pending journal contents')


def _copy(row, source, root, remaining):
    destination = root / row['path']
    destination.parent.mkdir(parents=True, exist_ok=True)
    if row['role'] == 'lineage-database':
        _journal_guard(source)
    with destination.open('xb') as output:
        count, digest = copy_regular(source, output, remaining)
    if row['role'] == 'lineage-database':
        _journal_guard(source)
    return {**row, 'bytes': count, 'sha256': digest}


def _omission(row):
    keys = ('id', 'role', 'disclosure', 'reason', 'review')
    return {key: row[key] for key in keys if key in row}


def _inventory_row(number, row):
    suffix = '.sqlite3' if row['role'] == 'lineage-database' else '.bin'
    if row['role'] in {'artifact', 'guide', 'assessments', 'lineage', 'predecessor'}:
        suffix = '.json'
    return {'id': row['id'], 'role': row['role'], 'path': f'assets/{number:05d}{suffix}',
            **({'review': row['review']} if 'review' in row else {})}


def _binding_sources(selection, sources, root, inventory):
    lineage_rows = [row for row in inventory if row['role'] == 'lineage']
    if not lineage_rows:
        if selection['lineageBindings']:
            raise ResultManifestError('lineage bindings require lineage inputs')
        return
    selected = lineage_rows[0]
    original = validate_lineage_inputs(read_document(root / selected['path']),
                                       validate_result_manifest(read_document(root / 'manifest.json')))
    entries = {row['id']: row for row in original.get('entries', [])}
    for binding in selection['lineageBindings']:
        entry = entries.get(binding['entryId'])
        database = sources.get(binding['databaseId'])
        if entry is None or database is None:
            raise ResultManifestError('unknown lineage binding')
        declared = _source(sources[selected['id']].parent, entry['database'])
        if declared != database:
            raise ResultManifestError('lineage binding does not name the selected source database')


def assemble_bundle(manifest_path, selection_path, root, max_bytes, max_members, output):
    """Do not collect any file solely because another document names it."""
    selection = validate_bundle_selection(read_document(selection_path))
    sources = {'manifest': _source(Path('.'), manifest_path)}
    rows = [{'id': 'manifest', 'role': 'manifest', 'path': 'manifest.json'}]
    omitted = []
    for number, entry in enumerate(sorted(selection['entries'], key=lambda row: row['id'])):
        if included(entry):
            rows.append(_inventory_row(number, entry))
            sources[entry['id']] = _source(Path(selection_path).parent, entry['path'])
        else:
            omitted.append(_omission(entry))
    if len(rows) + 1 > max_members:
        raise ResultManifestError('bundle member count limit exceeded')
    if _source(Path('.'), output) in sources.values():
        raise ResultManifestError('bundle output cannot replace a selected input')
    return _assemble(selection, rows, sources, omitted, root, max_bytes)


def _assemble(selection, rows, sources, omitted, root, max_bytes):
    inventory = []
    used = 0
    for row in rows:
        copied = _copy(row, sources[row['id']], root, max_bytes - used)
        inventory.append(copied)
        used += copied['bytes']
    _binding_sources(selection, sources, root, inventory)
    manifest = validate_result_manifest(read_document(root / 'manifest.json'))
    index = {'schema': 'ladon-result-bundle-v1', 'profile': 'core-v1',
             'resultId': manifest['resultId'], 'revision': manifest['revision'],
             'manifest': 'manifest.json', 'inventory': inventory, 'omissions': omitted}
    for key in ('supplier', 'identifiers', 'externalDependencies', 'lineageBindings'):
        index[key] = selection[key]
    validate_bundle_index(index)
    raw = canonical_json(index)
    if used + len(raw) > max_bytes:
        raise ResultManifestError('expanded bundle byte limit exceeded')
    (root / 'bundle.json').write_bytes(raw)
    return index
