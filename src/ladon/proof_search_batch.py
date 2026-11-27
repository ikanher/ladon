"""Bounded lexical queries over one SQLite read generation and validation window."""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import closing

from ladon.proof_search_exact_counts import exact_name_counts, match_summary
from ladon.proof_search_freshness import _changed_sources, _freshness_from_snapshot
from ladon.proof_search_index import (
    ProofSearchIndexError,
    _metadata,
    _open_readonly,
    _require_query_schema,
    _resolved_index_path,
)
from ladon.proof_search_query import query_database
from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist

_COMMON = {'--scope', '--root', '--limit'}
_NAME = {'--text', '--query-mode', '--exclude', '--min-matched-segments'}
_TYPE = {'--pattern', '--fragment', '--module', '--namespace', '--package', '--diagnostic-limit'}


def _requests(queries):
    from ladon.proof_search_cli import build_proof_search_parser

    if not isinstance(queries, list) or not 1 <= len(queries) <= 32:
        raise ProofSearchIndexError('batch requires 1..32 query argument lists')
    parser = build_proof_search_parser()
    requests = []
    for argv in queries:
        _validate_arguments(argv)
        request = parser.parse_args(['search', *argv, '--freshness', 'stored'])
        if request.limit > 100:
            raise ProofSearchIndexError('batch per-query limit cannot exceed 100')
        _validate_prepared_request(request)
        requests.append(request)
    if len(json.dumps(queries, ensure_ascii=False).encode()) > 65536:
        raise ProofSearchIndexError('batch queries exceed 65536 bytes')
    return requests


def _validate_prepared_request(request):
    if request.search_operation == 'type-text':
        try:
            request.type_request = TypeSearchRequest(
                request.pattern, fragments=tuple(request.fragment), module=request.module,
                namespace=request.namespace, package=request.package, scope=request.scope,
                roots=tuple(request.root), limit=request.limit, diagnostic_limit=request.diagnostic_limit,
            )
        except ValueError as error:
            raise ProofSearchIndexError(str(error)) from error
    elif request.scope in {'module', 'namespace', 'file', 'imports', 'closure', 'neighborhood'} and not request.root:
        raise ProofSearchIndexError(f"scope {request.scope!r} requires a query root")


def _validate_arguments(argv):
    _validate_query_kind(argv)
    allowed = _COMMON | (_NAME if argv[0] == 'name' else _TYPE)
    if len(argv) % 2 != 1:
        raise ProofSearchIndexError('each batch query option requires one value')
    for flag, value in zip(argv[1::2], argv[2::2], strict=True):
        _validate_option(flag, value, allowed)


def _validate_query_kind(argv):
    if not isinstance(argv, list) or not 1 <= len(argv) <= 65:
        raise ProofSearchIndexError('batch supports bounded query argument lists')
    if not isinstance(argv[0], str) or argv[0] not in {'name', 'type-text'}:
        raise ProofSearchIndexError('batch supports name and type-text queries')


def _validate_option(flag, value, allowed):
    if not isinstance(flag, str) or flag not in allowed:
        raise ProofSearchIndexError('invalid batch option; repository and freshness belong to the batch')
    if not isinstance(value, str) or len(value) > 4096:
        raise ProofSearchIndexError('batch option values must be strings of at most 4096 characters')


def _query(connection, args):
    if args.search_operation == 'type-text':
        return query_type_shortlist(connection, args.type_request)
    rows, truncated, count, omissions = query_database(connection, text=args.text,
        scope=args.scope, roots=tuple(args.root), limit=args.limit, query_mode=args.query_mode,
        exclusions=tuple(args.exclude), min_matched_segments=args.min_matched_segments)
    qualified, basename = exact_name_counts(connection, text=args.text, scope=args.scope,
                                            roots=tuple(args.root), exclusions=tuple(args.exclude))
    return {'schema': 'ladon-proof-search-batch-name-v1', 'operation': 'search-name',
            'query': {'text': args.text, 'scope': args.scope, 'roots': args.root,
                      'limit': args.limit, 'mode': args.query_mode, 'exclude': args.exclude,
                      'minMatchedSegments': args.min_matched_segments},
            'results': rows, 'returned': len(rows), 'truncated': truncated,
            'matchSummary': match_summary(rows, args.text, qualified, basename),
            'scope': {'kind': args.scope, 'roots': args.root, 'includedModules': count,
                      'omissions': omissions}}


def _sources(snapshot):
    return {s.module: (s.relative_path, s.sha256, s.package, s.generated, s.source_bytes)
            for s in snapshot.sources}


def _bounded(payload, max_bytes):
    if len((json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()) > max_bytes:
        raise ProofSearchIndexError('batch output exceeds selected byte allowance; use fewer/smaller queries')
    return payload


def run_search_batch(repo_root, queries, *, index_path=None, freshness='verify', max_output_bytes=1024**2):
    requests = _requests(queries)
    return run_prepared_batch(repo_root, requests, index_path=index_path,
                              freshness=freshness, max_output_bytes=max_output_bytes)


def run_prepared_batch(repo_root, requests, *, index_path=None, freshness='verify',
                       max_output_bytes=1024**2):
    _validate_prepared_batch(requests, freshness, max_output_bytes)
    started = time.monotonic()
    try:
        root, path, connection = _open_batch_index(repo_root, index_path, freshness)
        with closing(connection):
            connection.row_factory = sqlite3.Row
            connection.execute('BEGIN')
            return _run_prepared_snapshot(connection, root, path, requests, freshness,
                                          started, max_output_bytes)
    except sqlite3.Error as error:
        raise ProofSearchIndexError(f'batch index unavailable: {error}', exit_class='operational') from error
    except ValueError as error:
        raise ProofSearchIndexError(str(error)) from error


def _validate_prepared_batch(requests, freshness, max_output_bytes):
    if not isinstance(requests, list) or not 1 <= len(requests) <= 32:
        raise ProofSearchIndexError('batch requires 1..32 prepared queries')
    if freshness not in {'stored', 'verify'}:
        raise ProofSearchIndexError('freshness must be stored or verify')
    if type(max_output_bytes) is not int or not 1024**2 <= max_output_bytes <= 16 * 1024**2:
        raise ProofSearchIndexError('batch output allowance must be 1..16 MiB')


def _open_batch_index(repo_root, index_path, freshness):
    try:
        root = _batch_root(repo_root, index_path, freshness)
        path = index_path.resolve() if root is None else _resolved_index_path(root, index_path)
        connection = _open_readonly(path)
    except (OSError, RuntimeError) as error:
        raise ProofSearchIndexError(f'batch path unavailable: {error}', exit_class='operational') from error
    return root, path, connection


def _batch_root(repo_root, index_path, freshness):
    from pathlib import Path

    root = repo_root.resolve() if repo_root is not None else None
    return Path.cwd().resolve() if root is None and (index_path is None or freshness == 'verify') else root


def _run_prepared_snapshot(connection, root, path, requests, freshness, started, max_bytes):
    from ladon.proof_search_history_schema import require_supported_layout
    from ladon.proof_search_index import capture_repository_snapshot

    metadata = _metadata(connection)
    _require_query_schema(metadata)
    require_supported_layout(connection, verify_integrity=False)
    for key in ('repository', 'generationIdentity'):
        if not metadata.get(key):
            raise ProofSearchIndexError(f'batch index lacks {key} metadata', exit_class='operational')
    origin = metadata['repository']
    if root is not None and origin != str(root):
        raise ProofSearchIndexError('batch index belongs to another repository')
    if freshness == 'stored':
        return _run_stored(connection, requests, path, metadata, origin, started, max_bytes)
    before = capture_repository_snapshot(root)
    observed_freshness, _ = _freshness_from_snapshot(before, metadata)
    return _run_window(connection, requests, root, path, metadata, before,
                        observed_freshness, started, max_bytes)


def _run_stored(connection, requests, path, metadata, origin, started, max_bytes):
    result = {'schema': _batch_schema(requests, stored=True), 'operation': 'search-batch',
              'status': 'available', 'freshness': 'stored', 'freshnessStatus': 'unchecked',
              'indexPath': str(path),
              'generationIdentity': metadata.get('generationIdentity'), 'origin': origin,
              'queries': [], 'returnedQueries': 0, 'elapsedSeconds': time.monotonic() - started,
              'validation': {'authority': 'stored-index-generation', 'captureCount': 0,
                             'repository': origin,
                             'sourceFingerprint': metadata.get('sourceFingerprint'),
                             'configurationFingerprint': metadata.get('configurationFingerprint'),
                             'toolchainIdentity': metadata.get('toolchainIdentity'),
                             'helperIdentity': metadata.get('helperIdentity'),
                             'indexSchema': metadata.get('indexSchema')},
              'nonclaims': ['Lexical discovery is not Lean checking or compiled proof dependency evidence.',
                            'Stored mode does not observe current source files.']}
    for args in requests:
        row = _query(connection, args)
        row.update(generationIdentity=metadata['generationIdentity'], indexPath=str(path),
                   freshnessStatus='unchecked', freshness='stored')
        result['queries'].append(row)
        _bounded(result, max_bytes)
    result['returnedQueries'] = len(result['queries'])
    result['elapsedSeconds'] = time.monotonic() - started
    return _bounded(result, max_bytes)


def _run_window(connection, requests, root, path, metadata, before, freshness, started, max_bytes):
    from ladon.proof_search_index import _stored_sources, capture_repository_snapshot

    result = _result(path, metadata, before, freshness, started)
    result['schema'] = _batch_schema(requests)
    if freshness != 'fresh':
        result['sourceChanges'] = _changed_sources(_sources(before), _stored_sources(connection))
        return _bounded(result, max_bytes)
    for args in requests:
        row = _query(connection, args)
        row.update(generationIdentity=metadata['generationIdentity'], indexPath=str(path),
                   freshnessStatus='pending-batch-validation')
        result['queries'].append(row)
        _bounded(result, max_bytes)
    after = capture_repository_snapshot(root)
    result['validation']['captureCount'] = 2
    if after.generation_identity != before.generation_identity:
        result.update(status='unavailable', freshness='unstable-source', queries=[],
                      sourceChanges=_changed_sources(_sources(after), _sources(before)),
                      identityChanges=_identity_changes(after, before))
    else:
        _finish_validated(result, path)
    result['returnedQueries'] = len(result['queries'])
    result['elapsedSeconds'] = time.monotonic() - started
    return _bounded(result, max_bytes)


def _batch_schema(requests, *, stored=False):
    return ('ladon-proof-search-batch-v2' if stored or any(
        getattr(request, 'search_operation', None) == 'type-text'
        and bool(getattr(request, 'fragment', None)) for request in requests)
        else 'ladon-proof-search-batch-v1')


def _result(path, metadata, before, freshness, started):
    return {'schema': 'ladon-proof-search-batch-v1', 'operation': 'search-batch',
            'status': 'unavailable', 'freshness': freshness,
            'indexPath': str(path), 'generationIdentity': metadata.get('generationIdentity'),
            'queries': [], 'returnedQueries': 0, 'elapsedSeconds': time.monotonic() - started,
            'validation': {'authority': 'observed-source-window', 'captureCount': 1,
                           'repository': str(before.repo_root),
                           'sourceFingerprint': before.source_fingerprint,
                           'configurationFingerprint': before.configuration_fingerprint,
                           'toolchainIdentity': before.toolchain_identity,
                           'helperIdentity': metadata.get('helperIdentity'),
                           'indexSchema': metadata.get('indexSchema')},
            'nonclaims': ['Lexical discovery is not Lean checking or compiled proof dependency evidence.',
                          'Validation describes the batch observation window, not later filesystem state.',
                          'No persistent freshness token or historical database copy is created.']}


def _finish_validated(result, path):
    with closing(_open_readonly(path)) as active:
        generation = _metadata(active).get('generationIdentity')
    result['activeGenerationAtEnd'] = generation
    if generation != result['generationIdentity']:
        result.update(status='unavailable', freshness='index-generation-changed', queries=[])
        return
    result.update(status='available', freshness='verified-fresh')
    for row in result['queries']:
        row.update(freshnessStatus='verified-fresh', freshness='verified-fresh')
        if row.get('matchMode') == 'normalized-type-fragments':
            row['query']['freshness'] = 'verify'


def dispatch_search_batch(args, repo_root, index_path):
    from ladon.investigation import load_plan

    try:
        queries = load_plan(args.queries, max_bytes=65536)
        if getattr(args, 'indexes', None) is not None:
            if args.index_path is not None or args.repo_root is not None:
                raise ProofSearchIndexError("--indexes is mutually exclusive with --index and --repo-root")
            from ladon.proof_search_named_batch import run_named_batch

            return run_named_batch(args.indexes, queries,
                                   freshness=getattr(args, 'freshness', 'verify'),
                                   max_output_bytes=args.max_output_mib * 1024**2)
        return run_search_batch(repo_root, queries, index_path=index_path,
                                freshness=getattr(args, 'freshness', 'verify'),
                                max_output_bytes=args.max_output_mib * 1024**2)
    except (ValueError, TypeError) as error:
        raise ProofSearchIndexError(str(error)) from error


def _identity_changes(after, before):
    fields = ('source_fingerprint', 'configuration_fingerprint', 'toolchain_identity')
    return [field for field in fields if getattr(after, field) != getattr(before, field)]
