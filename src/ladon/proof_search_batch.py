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
_TYPE = {'--pattern', '--module', '--namespace', '--package', '--diagnostic-limit'}


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
        requests.append(request)
    if len(json.dumps(queries, ensure_ascii=False).encode()) > 65536:
        raise ProofSearchIndexError('batch queries exceed 65536 bytes')
    return requests


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
        return query_type_shortlist(connection, TypeSearchRequest(
            args.pattern, module=args.module, namespace=args.namespace, package=args.package,
            scope=args.scope, roots=tuple(args.root), limit=args.limit,
            diagnostic_limit=args.diagnostic_limit))
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


def run_search_batch(repo_root, queries, *, index_path=None, max_output_bytes=1024**2):
    from ladon.proof_search_index import capture_repository_snapshot

    requests = _requests(queries)
    if type(max_output_bytes) is not int or not 1024**2 <= max_output_bytes <= 16 * 1024**2:
        raise ProofSearchIndexError('batch output allowance must be 1..16 MiB')
    root = repo_root.resolve()
    path = _resolved_index_path(root, index_path)
    started = time.monotonic()
    try:
        with closing(_open_readonly(path)) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute('BEGIN')
            metadata = _metadata(connection)
            _require_query_schema(metadata)
            from ladon.proof_search_history_schema import require_supported_layout

            require_supported_layout(connection, verify_integrity=False)
            if metadata.get('repository') != str(root):
                raise ProofSearchIndexError('batch index belongs to another repository')
            before = capture_repository_snapshot(root)
            freshness, _ = _freshness_from_snapshot(before, metadata)
            return _run_window(connection, requests, root, path, metadata, before,
                               freshness, started, max_output_bytes)
    except sqlite3.Error as error:
        raise ProofSearchIndexError(f'batch index unavailable: {error}', exit_class='operational') from error
    except ValueError as error:
        raise ProofSearchIndexError(str(error)) from error


def _run_window(connection, requests, root, path, metadata, before, freshness, started, max_bytes):
    from ladon.proof_search_index import _stored_sources, capture_repository_snapshot

    result = _result(path, metadata, before, freshness, started)
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


def dispatch_search_batch(args, repo_root, index_path):
    from ladon.investigation import load_plan

    try:
        return run_search_batch(repo_root, load_plan(args.queries, max_bytes=65536),
                                index_path=index_path, max_output_bytes=args.max_output_mib * 1024**2)
    except (ValueError, TypeError) as error:
        raise ProofSearchIndexError(str(error)) from error


def _identity_changes(after, before):
    fields = ('source_fingerprint', 'configuration_fingerprint', 'toolchain_identity')
    return [field for field in fields if getattr(after, field) != getattr(before, field)]
