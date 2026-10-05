"""Read a selected legacy lineage capture without freshness or authority upgrades."""
from __future__ import annotations

import json
import sqlite3
import stat
from pathlib import Path

from ladon.result_inspection_page import inspection_digest
from ladon.result_manifest_io import ResultManifestError, canonical_json
from ladon.theorem_lineage_store import LineageIdentity, inspect_lineage_closure
from ladon.theorem_lineage_summary import summarize_lineage

ROW_LIMIT = 10_000
MAX_ACQUIRED_BYTES = 32 * 1024 * 1024
_ORDER = {'lineage_trust': 'kind,scope,target', 'lineage_nodes': 'name',
          'lineage_omissions': 'facet,subject,reason'}
_COLUMNS = {
    'lineage_trust': 'closure_id kind scope target',
    'lineage_nodes': 'closure_id name owner_module kind project_owned external_frontier compiler_generated declared_axiom unsafe source_path source_line source_column source_status type_fingerprint value_fingerprint',
    'lineage_omissions': 'closure_id facet subject reason details_json',
    'lineage_closures': 'closure_id theorem_name theorem_module theorem_path plan_identity semantic_closure_fingerprint repository source_fingerprint configuration_fingerprint toolchain_identity helper_identity base_generation_identity schema_generation authority semantic_status active unsupported_facets_json node_count edge_count created_identity',
}


def read_lineage_selection(entry, theorem, base, budget=None, *, reference_base=None):
    """Read a consistent snapshot, preserving both exact selection and owner status."""
    path = (Path(base) / entry['database']).resolve()
    reference = str(path) if reference_base is None else reference_base + '/' + entry['database']
    try:
        metadata = path.stat()
    except FileNotFoundError:
        return {'status': 'unavailable', 'reason': 'database-unavailable', 'database': reference}
    if not stat.S_ISREG(metadata.st_mode):
        raise ResultManifestError('lineage database must be a regular file')
    try:
        connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute('BEGIN')
            snapshot = _snapshot(connection, entry, theorem, budget if budget is not None else {'bytes': 0, 'rows': 0})
        finally:
            connection.close()
    except ResultManifestError:
        raise
    except (sqlite3.Error, ValueError, TypeError, KeyError) as exc:
        raise ResultManifestError('malformed selected lineage database') from exc
    snapshot['database'] = reference
    snapshot['revision'] = inspection_digest(snapshot)
    return snapshot


def _snapshot(connection, entry, theorem, budget):
    closure_id = entry['closureId']
    record = connection.execute(
        f'SELECT {_bounded_columns("lineage_closures")} FROM lineage_closures WHERE closure_id=?',
        (closure_id,),
    ).fetchone()
    closure = dict(record) if record else None
    _charge(closure, budget)
    tables = {table: _rows(connection, table, closure_id, budget) for table in _ORDER}
    if closure is not None:
        closure['unsupported_facets'] = json.loads(closure.pop('unsupported_facets_json'))
        if not isinstance(closure['unsupported_facets'], list):
            raise ValueError('invalid unsupported facets')
    selection = _selected_closure(connection, closure, theorem)
    if selection is not None:
        return {'status': selection[0], 'reason': selection[1], 'ownerSummary': None,
                'closure': closure, 'tables': tables}
    _summary_domains(connection, closure)
    identity = LineageIdentity(**entry['identity'])
    owner = inspect_lineage_closure(connection, theorem, identity)
    summary = summarize_lineage(connection, identity, theorem)
    summary.pop('elapsedSeconds', None)
    _charge(summary, budget)
    status, reason = _status(owner, closure, closure_id)
    snapshot = {'status': status, 'reason': reason, 'ownerSummary': summary,
                'closure': closure, 'tables': tables}
    return snapshot


def _summary_domains(connection, closure):
    """Enforce the existing owner's finite domains on supplied stores."""
    if closure['authority'] != 'lean_environment' or closure['semantic_status'] != 'complete':
        raise ResultManifestError('lineage closure violates owner authority/status contract')
    predicates = {
        'lineage_edges': "kind IS NULL OR kind NOT IN ('type','value')",
        'lineage_trust': "scope IS NULL OR scope NOT IN ('type','value','declaration')",
        'lineage_nodes': ' OR '.join(f'{key} IS NULL OR {key} NOT IN (0,1)' for key in
                                    ('project_owned', 'external_frontier', 'declared_axiom',
                                     'compiler_generated', 'unsafe')),
    }
    for table, predicate in predicates.items():
        invalid = connection.execute(
            f'SELECT 1 FROM {table} WHERE closure_id=? AND ({predicate}) LIMIT 1',
            (closure['closure_id'],),
        ).fetchone()
        if invalid:
            raise ResultManifestError('lineage summary domain violates owner contract')
    count, maximum = connection.execute(
        "SELECT count(*),max(length(CAST(value AS BLOB))) FROM metadata "
        "WHERE key IN ('maxIndexBytes','completeDatabaseMaxBytes','completeDatabaseBudgetPolicy')"
    ).fetchone()
    if count > 3 or (maximum or 0) > 65536:
        raise ResultManifestError('lineage summary metadata exceeds input limit')


def _selected_closure(connection, closure, theorem):
    if closure is None:
        active = connection.execute(
            'SELECT closure_id FROM lineage_closures WHERE theorem_name=? AND active=1',
            (theorem,),
        ).fetchone()
        return ('mismatched', 'closure-mismatch') if active else ('unavailable', 'closure-unavailable')
    if closure['theorem_name'] != theorem or closure['active'] != 1:
        return 'mismatched', 'closure-mismatch'
    return None


def _status(owner, closure, closure_id):
    if owner.get('closureId') and owner['closureId'] != closure_id:
        return 'mismatched', 'closure-mismatch'
    if closure is None:
        return 'unavailable', 'closure-unavailable'
    if owner.get('closureId') != closure_id:
        return 'mismatched', 'closure-mismatch'
    if owner['status'] != 'fresh':
        return 'unavailable', owner.get('reason', owner['status'])
    return 'available', None


def _rows(connection, table, closure_id, budget):
    where = ' AND external_frontier=1' if table == 'lineage_nodes' else ''
    cursor = connection.execute(
        f'SELECT {_bounded_columns(table)} FROM {table} WHERE closure_id=?{where} ORDER BY {_ORDER[table]} LIMIT ?',
        (closure_id, ROW_LIMIT + 1),
    )
    rows, truncated = [], False
    for record in cursor:
        if len(rows) == ROW_LIMIT:
            truncated = True
            break
        row = dict(record)
        _charge(row, budget)
        rows.append(row)
    return {'rows': rows, 'returned': len(rows), 'truncated': truncated,
            'matchedExact': not truncated, 'orderBy': _ORDER[table]}


def _bounded_columns(table):
    # Fixed identifiers only. Bound text/blob values inside SQLite before Python
    # materialization; one excess character suffices to reject oversized fields.
    return ','.join(f"CASE WHEN typeof({c}) IN ('text','blob') THEN substr({c},1,65537) ELSE {c} END AS {c}"
                    for c in _COLUMNS[table].split())


def _charge(row, budget):
    if row is None:
        return
    if any(isinstance(v, str) and len(v.encode()) > 65536 for v in row.values()):
        raise ResultManifestError('lineage field exceeds 64 KiB input limit')
    budget['bytes'] += len(canonical_json(row))
    budget['rows'] += 1
    if budget['bytes'] > MAX_ACQUIRED_BYTES or budget['rows'] > 100_000:
        raise ResultManifestError('lineage aggregate acquisition byte/row limit exceeded')
