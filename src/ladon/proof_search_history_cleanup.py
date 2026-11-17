"""Explicit preview-bound cleanup of registered legacy index archives."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from contextlib import closing
from pathlib import Path

from ladon.proof_search_history_store import history_directory, read_history
from ladon.proof_search_index import ProofSearchIndexError, _open_readonly, _resolved_index_path
from ladon.sqlite_publication import acquire_publication_lock, release_publication_lock


def _identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _file(index, entry):
    root = history_directory(index)
    if root.is_symlink() or root.resolve() != root:
        raise ProofSearchIndexError('history directory must be a direct regular directory')
    path = root / entry['path']
    if not path.exists() and not path.is_symlink():
        return path, None
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ProofSearchIndexError('cleanup refuses symlinked, hardlinked or nonregular archives')
    return path, {'device': info.st_dev, 'inode': info.st_ino,
                  'bytes': info.st_size, 'mtimeNs': info.st_mtime_ns}


def preview_history_cleanup(repo_root, *, index_path=None, snapshots=(), all_registered=False):
    index = _resolved_index_path(Path(repo_root).resolve(), index_path)
    if bool(snapshots) == bool(all_registered):
        raise ProofSearchIndexError('select --all-registered or one or more --snapshot IDs')
    with closing(_open_readonly(index)) as connection:
        connection.execute('BEGIN')
        entries = read_history(connection)
        generation = dict(connection.execute('SELECT key,value FROM metadata')).get('generationIdentity')
    requested = set(snapshots)
    if requested - {e['snapshotId'] for e in entries}:
        raise ProofSearchIndexError('cleanup selection contains an unregistered snapshot')
    rows = []
    for entry in entries:
        if all_registered or entry['snapshotId'] in requested:
            path, observed = _file(index, entry)
            rows.append({'entry': entry, 'path': str(path), 'observed': observed})
    result = {'schema': 'ladon-history-cleanup-preview-v1', 'operation': 'history-cleanup',
              'status': 'preview', 'indexPath': str(index), 'generationIdentity': generation,
              'selected': rows, 'selectedBytes': sum(r['observed']['bytes'] for r in rows if r['observed']),
              'consequence': 'Selected historical lookups will become unavailable. Active index and separately saved artifacts are retained.'}
    result['previewId'] = _identity(result)
    return result


def _validate_preview(preview, index):
    keys = {'schema', 'operation', 'status', 'indexPath', 'generationIdentity', 'selected',
            'selectedBytes', 'consequence', 'previewId'}
    if not isinstance(preview, dict) or set(preview) != keys:
        raise ProofSearchIndexError('invalid history cleanup preview')
    body = {k: v for k, v in preview.items() if k != 'previewId'}
    if (preview['schema'] != 'ladon-history-cleanup-preview-v1'
            or preview['status'] != 'preview' or preview['indexPath'] != str(index)
            or preview['previewId'] != _identity(body)):
        raise ProofSearchIndexError('history cleanup preview identity or owner mismatch')


def apply_history_cleanup(repo_root, preview, *, index_path=None):
    index = _resolved_index_path(Path(repo_root).resolve(), index_path)
    _validate_preview(preview, index)
    lock = acquire_publication_lock(index)
    try:
        return _apply_locked(index, preview)
    finally:
        release_publication_lock(lock)


def _apply_locked(index, preview):
    import sqlite3

    with closing(sqlite3.connect(f'file:{index}?mode=rw', uri=True)) as connection:
        connection.execute('PRAGMA synchronous=FULL')
        connection.execute('BEGIN IMMEDIATE')
        current = {e['snapshotId']: e for e in read_history(connection)}
        _validate_selection(index, preview['selected'], current)
        # Catalog removal commits before unlink: interruption can leave only a
        # disclosed orphan. The same preview can finish those unlinks on retry.
        for row in preview['selected']:
            connection.execute('DELETE FROM index_history WHERE snapshot_id=?',
                               (row['entry']['snapshotId'],))
        connection.commit()
    removed = 0
    for row in preview['selected']:
        path, observed = _file(index, row['entry'])
        if observed is not None:
            if observed != row['observed']:
                raise ProofSearchIndexError('archive changed after catalog removal; retain preview for recovery')
            path.unlink()
            removed += observed['bytes']
    root = history_directory(index)
    if root.is_dir():
        descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return {'schema': 'ladon-history-cleanup-result-v1', 'operation': 'history-cleanup',
            'status': 'complete', 'indexPath': str(index), 'previewId': preview['previewId'],
            'selectedCount': len(preview['selected']), 'removedBytes': removed}


def _validate_selection(index, rows, current):
    from ladon.proof_search_history_store import _validate_entry

    identities = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'entry', 'path', 'observed'}:
            raise ProofSearchIndexError('invalid cleanup selection row')
        entry = row['entry']
        identity = entry.get('snapshotId')
        _validate_entry(entry, identity)
        if identity in identities:
            raise ProofSearchIndexError('duplicate cleanup selection')
        identities.add(identity)
        if identity in current and current[identity] != entry:
            raise ProofSearchIndexError('history catalog changed since preview')
        path, observed = _file(index, entry)
        if str(path) != row['path'] or (observed is not None and observed != row['observed']):
            raise ProofSearchIndexError('history file changed since preview')
