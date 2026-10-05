"""Atomic portable result export and integrity-only bundle verification."""
from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

from ladon.result_bundle_archive import extract_bundle_archive, write_bundle_archive
from ladon.result_bundle_contract import (
    DEFAULT_BUNDLE_BYTES,
    DEFAULT_BUNDLE_MEMBERS,
    bundle_bounds,
    validate_bundle_index,
)
from ladon.result_bundle_export import assemble_bundle, read_document
from ladon.result_bundle_files import _open_directory, copy_regular, regular_files, safe_open
from ladon.result_bundle_inputs import load_bundle_inputs
from ladon.result_manifest_io import MAX_RESULT_BYTES, ResultManifestError, canonical_json


def _file_digest(path):
    count, digest = 0, hashlib.sha256()
    with safe_open(path) as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            count += len(block)
            digest.update(block)
    return count, 'sha256:' + digest.hexdigest()


def _validate_root(root, max_bytes, max_members):
    names = regular_files(root, max_members)
    index = validate_bundle_index(read_document(root / 'bundle.json'))
    expected = {'bundle.json', *(row['path'] for row in index['inventory'])}
    if set(names) != expected:
        raise ResultManifestError('bundle inventory does not match all payload files')
    total, identity = _file_digest(root / 'bundle.json')
    for row in index['inventory']:
        count, digest = _file_digest(root / row['path'])
        if (count, digest) != (row['bytes'], row['sha256']):
            raise ResultManifestError('bundle payload size or hash mismatch')
        total += count
        if total > max_bytes:
            raise ResultManifestError('expanded bundle byte limit exceeded')
    return load_bundle_inputs(root, index, identity)


def _copy_directory(source, root, max_bytes, max_members):
    total = 0
    for name in regular_files(source, max_members):
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as target:
            count, _ = copy_regular(source / name, target, max_bytes - total)
        total += count


@contextmanager
def open_result_bundle(path, *, max_bytes=DEFAULT_BUNDLE_BYTES,
                       max_members=DEFAULT_BUNDLE_MEMBERS, staging_parent=None):
    """Inspect an isolated snapshot, never mutable original paths or cache state."""
    bundle_bounds(max_bytes, max_members)
    with tempfile.TemporaryDirectory(prefix='ladon-result-bundle-', dir=staging_parent) as temporary:
        root = Path(temporary) / 'contents'
        root.mkdir()
        if Path(path).is_dir():
            _copy_directory(Path(path), root, max_bytes, max_members)
        else:
            extract_bundle_archive(path, root, max_bytes=max_bytes, max_members=max_members)
        yield _validate_root(root, max_bytes, max_members)


def is_result_bundle(path):
    """Recognize an explicit directory/ZIP input without reading references."""
    if Path(path).is_dir():
        return True
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ResultManifestError('result input must be a regular file')
        return stream.read(4) in (b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08')


def _summary(inputs, operation):
    index = inputs.index
    result = {'schema': 'ladon-result-bundle-report-v1', 'operation': operation,
              'status': 'exported' if operation == 'export' else 'verified',
              'profile': index['profile'], 'integrity': 'passed',
              'resultId': index['resultId'], 'revision': index['revision'],
              'bundleIndexDigest': inputs.identity, 'checking': 'not-assessed',
              'correspondence': 'not-assessed', 'authenticity': 'not-assessed',
              'replay': 'not-run', 'replayCoverage': 'unknown',
              'payloadCount': len(index['inventory']),
              'payloadBytes': sum(row['bytes'] for row in index['inventory']),
              'omissionCount': len(index['omissions']), 'supplier': index['supplier']}
    populations = {'externalDependencies': index['externalDependencies'],
                   'missingPredecessors': inputs.missing_history, 'missingLineage': inputs.missing_lineage,
                   'identifiers': index['identifiers'], 'omissions': index['omissions']}
    result['references'] = {}
    for key, rows in populations.items():
        result[key] = {'count': len(rows), 'rows': rows[:10], 'omitted': max(0, len(rows) - 10)}
        result['references'][key] = {'input': 'bundle.json', 'revision': inputs.identity,
                                      'pointer': '/' + key if key in index else '/inventory'}
    _fit(result, populations)
    return result


def _fit(result, populations):
    while len(canonical_json(result)) >= MAX_RESULT_BYTES:
        for key in populations:
            if result[key]['rows']:
                result[key]['rows'].pop()
                result[key]['omitted'] += 1
                break
        else:
            raise ResultManifestError('bundle summary exceeds compact byte limit')


def export_result_bundle(manifest_path, selection_path, output, *, max_bytes=DEFAULT_BUNDLE_BYTES,
                         max_members=DEFAULT_BUNDLE_MEMBERS):
    """Publish one immutable local ZIP only after complete input validation."""
    bundle_bounds(max_bytes, max_members)
    output = Path(output)
    parent = _open_directory(output.absolute().parent)
    os.close(parent)
    with tempfile.TemporaryDirectory(prefix='.ladon-result-stage-', dir=output.absolute().parent) as temporary:
        root = Path(temporary)
        assemble_bundle(Path(manifest_path), Path(selection_path), root, max_bytes, max_members, output)
        result = _summary(_validate_root(root, max_bytes, max_members), 'export')
        write_bundle_archive(root, output, max_bytes=max_bytes, max_members=max_members)
        return result


def _extraction_destination(path):
    destination = Path(path).absolute()
    parent = _open_directory(destination.parent)
    try:
        if os.path.lexists(destination):
            raise ResultManifestError('extraction destination already exists')
    except BaseException:
        os.close(parent)
        raise
    return destination, parent


def verify_result_bundle(bundle_path, *, extract_to=None, max_bytes=DEFAULT_BUNDLE_BYTES,
                         max_members=DEFAULT_BUNDLE_MEMBERS):
    """Verify transport integrity; optional extraction never performs replay."""
    if extract_to is None:
        with open_result_bundle(bundle_path, max_bytes=max_bytes, max_members=max_members) as inputs:
            return _summary(inputs, 'verify')
    destination, parent = _extraction_destination(extract_to)
    try:
        with open_result_bundle(bundle_path, max_bytes=max_bytes, max_members=max_members,
                                staging_parent=destination.parent) as inputs:
            result = _summary(inputs, 'verify')
            if os.path.lexists(destination):
                raise ResultManifestError('extraction destination already exists')
            os.rename(inputs.root, destination.name, dst_dir_fd=parent)
            return result
    finally:
        os.close(parent)
