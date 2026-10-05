"""Compose an offline result dossier without running or upgrading evidence."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from ladon.result_component_scope import apply_component_scope
from ladon.result_dossier import prepare_dossier
from ladon.result_inspection_cards import select_rows
from ladon.result_inspection_page import compact_row, inspect_page, inspection_digest
from ladon.result_manifest import validate_result_manifest
from ladon.result_manifest_io import ResultManifestError

SECTIONS = ('components', 'claims', 'targets', 'reviews', 'assessments', 'checking', 'assumptions', 'lineage', 'evidence')


def inspect_result_manifest(manifest, artifacts, *, assessments=None, section='components',
                            claim_id=None, component_id=None, target_id=None, limit=20, cursor=None,
                            lineage_inputs=None, lineage_base=Path('.'),
                            lineage_reference_base=None, bundle_identity=None):
    """Validate complete inputs, then select and bound one attributable view."""
    manifest = validate_result_manifest(manifest)
    _selection(manifest, section, claim_id, component_id, target_id, limit)
    selected = _selected_targets(manifest, claim_id, component_id, target_id)
    inputs = prepare_dossier(manifest, artifacts, assessments=assessments,
                             lineage_inputs=lineage_inputs, lineage_base=lineage_base,
                             target_ids=selected, lineage_reference_base=lineage_reference_base)
    return _inspect_prepared(manifest, inputs, section=section, claim_id=claim_id,
                             component_id=component_id, target_id=target_id, limit=limit,
                             cursor=cursor, bundle_identity=bundle_identity)


def _inspect_prepared(manifest, inputs, *, section, claim_id=None, component_id=None,
                      target_id=None, limit=20, cursor=None, bundle_identity=None):
    _selection(manifest, section, claim_id, component_id, target_id, limit)
    selected = _selected_targets(manifest, claim_id, component_id, target_id)
    query = _query(section, claim_id, component_id, target_id, limit)
    binding = inspection_digest({'revision': manifest['revision'], 'assessments': inputs.assessments,
                                 'artifacts': sorted(inputs.catalog), 'query': query,
                                 'lineageInputs': inputs.lineage, 'lineageObservations': inputs.stored})
    if bundle_identity is not None:
        binding = inspection_digest({'inputs': binding, 'bundle': bundle_identity})
    result = compact_row(_header(manifest, inputs.resolved, section, binding, query))
    if section == 'evidence':
        from ladon.result_subject_evidence import subject_evidence_cards
        with subject_evidence_cards(manifest, inputs.catalog, inputs.resolutions, selected) as rows:
            return inspect_page(result, rows, binding, limit, cursor)
    else:
        rows = inputs.sections[section]
        if section == 'components':
            cards = {'components': rows, 'targets': inputs.sections['targets']}
            rows = apply_component_scope(
                manifest, cards, inputs.sections['assessments'],
            )['components']
        if section != 'checking':
            rows = select_rows(rows, manifest, claim_id, target_id)
        if component_id is not None:
            rows = [row for row in rows if row['componentId'] == component_id and row['claimId'] == claim_id]
    return inspect_page(result, rows, binding, limit, cursor)


def _selection(manifest, section, claim_id, component_id, target_id, limit):
    if section not in SECTIONS:
        raise ResultManifestError('unknown inspection section')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ResultManifestError('inspection limit must be 1..100')
    for identifier, collection in ((claim_id, 'claims'), (target_id, 'targets')):
        if identifier is not None and not any(row['id'] == identifier for row in manifest[collection]):
            raise ResultManifestError(f'unknown {collection} selector')
    _component_selection(manifest, section, claim_id, component_id)


def _component_selection(manifest, section, claim_id, component_id):
    if component_id is None:
        return
    if section != 'components' or claim_id is None:
        raise ResultManifestError('component selection requires components section and exact claim')
    claim = next(row for row in manifest['claims'] if row['id'] == claim_id)
    if component_id not in claim['components']:
        raise ResultManifestError('unknown component selector for claim')


def _query(section, claim_id, component_id, target_id, limit):
    query = {'section': section, 'claim': claim_id, 'target': target_id, 'limit': limit}
    if section == 'components':
        query = {'projectionVersion': 2, **query, 'component': component_id}
    return query


def _header(manifest, resolutions, section, binding, query):
    return {
        'schema': 'ladon-result-inspection-v1', 'operation': 'inspect', 'status': 'inspected',
        'inspectionScope': 'offline-supplied-evidence', 'resultId': manifest['resultId'],
        'revision': manifest['revision'], 'inputBinding': binding, 'section': section, 'query': query,
        'coverage': {'claimInventory': manifest['claimInventory'], 'proofCoverage': 'unknown',
                     'canonicalResolution': dict(Counter(row['status'] for row in resolutions)),
                     'transitiveTrust': 'unknown'},
        'axes': {'checking': 'stored-operations-only', 'sourceFreshness': 'not-assessed',
                 'environment': 'per-target-and-check', 'correspondence': 'attributed-reviews-only',
                 'exposition': 'not-assessed', 'attribution': 'not-assessed'},
        'limitations': ['inspection-does-not-run-checks', 'mapping-does-not-establish-equivalence',
                       'integrity-does-not-authenticate-producer', 'unknown-trust-is-not-absence'],
        'availableSections': list(SECTIONS),
        'references': {'/coverage/claimInventory': {'input': 'manifest', 'revision': manifest['revision'],
                                                   'pointer': '/claimInventory'}},
    }


def _selected_targets(manifest, claim_id, component_id, target_id):
    if claim_id is None and component_id is None and target_id is None:
        return None
    selected = {row['id'] for row in manifest['targets']}
    if claim_id is not None:
        selected &= _claim_targets(manifest, claim_id)
    if component_id is not None:
        selected &= _component_targets(manifest, claim_id, component_id)
    if target_id is not None:
        selected &= {target_id}
    return selected


def _claim_targets(manifest, claim_id):
    return {target for link in manifest['links'] if link['claimId'] == claim_id
            for target in link['targetIds']}


def _component_targets(manifest, claim_id, component_id):
    return {target for link in manifest['links']
            if link['claimId'] == claim_id and component_id in link['componentIds']
            for target in link['targetIds']}
