"""Keep stored lineage facts and unsupported assumption inventories separate."""
from __future__ import annotations

from collections import defaultdict

from ladon.result_inspection_page import inspection_digest
from ladon.result_lineage_store import read_lineage_selection

CATEGORIES = ('theorem-hypotheses', 'observed-axioms', 'declared-external-assumptions',
              'placeholders', 'obligations', 'external-frontiers')


def lineage_sections(manifest, resolutions, lineage_inputs, base, *, reference_base=None):
    """Validate every supplied selection before applying display selectors."""
    entries = defaultdict(list)
    for entry in (lineage_inputs or {}).get('entries', []):
        entries[entry['targetId']].append(entry)
    result = {'assumptions': [], 'lineage': []}
    budget = {'bytes': 0, 'rows': 0}
    for target in manifest['targets']:
        selected = entries[target['id']]
        if not selected:
            missing = _base(target['id'], None, 'current')
            result['lineage'].append({**missing, 'status': 'unavailable', 'coverage': 'unknown',
                                      'reason': 'no-lineage-input-supplied', 'checking': 'not-run'})
            result['assumptions'].extend(_unknown(missing, kind) for kind in CATEGORIES)
        for entry in selected:
            snapshot = read_lineage_selection(entry, target['name'], base, budget,
                                              reference_base=reference_base)
            rows = _selection(manifest, target, entry, resolutions[target['id']], snapshot,
                              lineage_inputs['manifestRevision'])
            result['lineage'].append(rows['lineage'])
            result['assumptions'].extend(rows['assumptions'])
    return result


def _selection(manifest, target, entry, resolution, snapshot, revision):
    current = revision == manifest['revision'] and entry['targetRevision'] == target['revision']
    base = _base(target['id'], entry['id'], 'current' if current else 'historical')
    status, reason = snapshot['status'], snapshot['reason']
    if not current:
        status, reason = 'historical', 'selection-revision-mismatch'
    elif resolution['status'] != 'resolved':
        status, reason = 'unavailable', 'canonical-target-unresolved'
    query_ref = {'input': 'lineage-selection-query', 'database': snapshot['database'],
                 'closureId': entry['closureId'], 'entryId': entry['id'],
                 'selectionRevision': inspection_digest(entry),
                 'revision': snapshot.get('revision'), 'pointer': ''}
    lineage = {**base, 'status': status, 'reason': reason,
               'ownerSummary': snapshot.get('ownerSummary'),
               'ownerDetails': {k: snapshot[k] for k in ('closure', 'tables') if k in snapshot},
               'references': {'/ownerSummary': {**query_ref, 'pointer': '/ownerSummary'},
                              '/ownerDetails': {**query_ref, 'appendPath': False}}}
    rows = _assumptions(base, snapshot, entry, status)
    return {'lineage': lineage, 'assumptions': rows}


def _base(target_id, entry_id, currency):
    return {'targetId': target_id, 'entryId': entry_id, 'selectionCurrency': currency,
            'associationBasis': 'producer-selected', 'sourceFreshness': 'not-assessed',
            'freshnessBasis': 'supplied-identity-only', 'environmentBinding': 'not-established'}


def _unknown(base, kind, reason='no-supported-extraction-supplied'):
    return {**base, 'kind': kind, 'status': 'unavailable', 'coverage': 'unknown', 'total': None,
            'authority': 'not-assessed', 'reason': reason}


def _assumptions(base, snapshot, entry, status):
    if status not in {'available', 'historical'} or snapshot['status'] != 'available':
        return [_unknown(base, kind, snapshot.get('reason') or 'target-evidence-unavailable')
                for kind in CATEGORIES]
    rows = []
    for table in snapshot['tables']:
        rows.extend(_population_rows(base, snapshot, entry, table, status))
    kinds = {r['kind'] for r in rows}
    rows.extend(_unknown(base, kind) for kind in CATEGORIES if kind not in kinds)
    return rows


def _population_rows(base, snapshot, entry, table, status):
    rows = []
    for index, observation in enumerate(snapshot['tables'][table]['rows']):
        kind = _category(table, observation)
        if kind is not None:
            rows.append(_observation(base, kind, observation, snapshot, entry, table, index, status))
    return rows


def _category(table, row):
    if table == 'lineage_nodes':
        return 'external-frontiers'
    if table != 'lineage_trust':
        return None
    if row['kind'] == 'sorryAx':
        return 'placeholders'
    if row['kind'] in {'axiom_reference', 'declared_axiom'}:
        return 'observed-axioms'
    return None  # Unsafe and unknown trust facts remain raw lineage evidence.


def _observation(base, kind, observation, snapshot, entry, table, index, status):
    observation = dict(observation)
    if table == 'lineage_nodes':
        for key in ('project_owned', 'external_frontier', 'compiler_generated', 'declared_axiom', 'unsafe'):
            observation[key] = bool(observation[key])
    return {**base, 'kind': kind, 'status': 'observed' if status == 'available' else 'historical',
            'observation': observation, 'authority': 'lean_environment', 'coverage': 'partial',
            'total': None, 'transitiveCoverage': 'unknown',
            'acquisition': {k: v for k, v in snapshot['tables'][table].items() if k != 'rows'},
            'references': {'/observation': _reference(snapshot, entry, table, index)}}


def _reference(snapshot, entry, table, index):
    return {'input': 'lineage-database', 'database': snapshot['database'],
            'revision': snapshot['revision'], 'closureId': entry['closureId'],
            'table': table, 'orderBy': snapshot['tables'][table]['orderBy'],
            'rowOffset': index, 'pointer': ''}
