"""Read attributed proof explanations alongside unchanged evidence owners."""
from __future__ import annotations

from pathlib import Path

from ladon.result_dossier import prepare_dossier
from ladon.result_exposition_cards import ExpositionCards, unavailable_exposition
from ladon.result_guide_cards import GuideCards, selected_guide_targets
from ladon.result_guide_inputs import guide_currencies, validate_result_guide
from ladon.result_inspection_cards import select_rows
from ladon.result_inspection_page import compact_row, inspect_page, inspection_digest
from ladon.result_manifest import validate_result_manifest
from ladon.result_manifest_io import ResultManifestError

GUIDE_SECTIONS = ('steps', 'citations', 'reviews', 'correspondence', 'targets',
                  'checking', 'assumptions', 'lineage', 'evidence', 'exposition')


def guide_result_manifest(manifest, artifacts, *, guide_inputs=None, section='steps',
                          claim_id=None, target_id=None, component_id=None, limit=20, cursor=None, assessments=None,
                          lineage_inputs=None, lineage_base=Path('.'),
                          lineage_reference_base=None, bundle_identity=None):
    """Validate all inputs before presenting one bounded, authored-order page."""
    manifest = validate_result_manifest(manifest)
    _selection(manifest, section, claim_id, target_id, component_id, limit)
    companion = validate_result_guide(guide_inputs, manifest) if guide_inputs is not None else None
    currencies = guide_currencies(companion, manifest) if companion is not None else {}
    selected = selected_guide_targets(manifest, companion, currencies, claim_id, target_id)
    inputs = prepare_dossier(manifest, artifacts, assessments=assessments, lineage_inputs=lineage_inputs,
                             lineage_base=lineage_base, target_ids=selected,
                             lineage_reference_base=lineage_reference_base)
    query = {'section': section, 'claim': claim_id, 'target': target_id, 'limit': limit}
    if section == 'exposition':
        query = {'projectionVersion': 3, **query, 'component': component_id}
    binding = inspection_digest({'revision': manifest['revision'], 'guideInputs': companion,
                                 'assessments': inputs.assessments,
                                 'artifacts': sorted(inputs.catalog), 'query': query,
                                 'lineageInputs': inputs.lineage, 'lineageObservations': inputs.stored})
    if bundle_identity is not None:
        binding = inspection_digest({'inputs': binding, 'bundle': bundle_identity})
    result = compact_row(_header(manifest, companion, currencies, binding, query))
    if section == 'evidence':
        from ladon.result_subject_evidence import subject_evidence_cards
        with subject_evidence_cards(manifest, inputs.catalog, inputs.resolutions, selected) as rows:
            return inspect_page(result, rows, binding, limit, cursor)
    if section == 'exposition':
        if companion is None:
            rows = unavailable_exposition()
        else:
            rows = ExpositionCards(manifest, inputs, companion, currencies, claim_id,
                                   component_id, target_id)
    else:
        rows = _rows(manifest, inputs, companion, currencies, selected, query)
    return inspect_page(result, rows, binding, limit, cursor)


def _rows(manifest, inputs, companion, currencies, selected, query):
    section, claim_id, target_id = query['section'], query['claim'], query['target']
    if section in {'steps', 'citations', 'reviews'}:
        if companion is None:
            return [{'status': 'unavailable', 'reason': 'no-guide-inputs-supplied',
                     'authority': 'not-assessed'}] if section == 'steps' else []
        return GuideCards(companion, currencies, manifest, inputs.resolutions, section, claim_id, target_id)
    if section == 'correspondence':
        return select_rows(inputs.sections['reviews'], manifest, claim_id, target_id)
    rows = inputs.sections[section]
    if section == 'checking' or selected is None:
        return rows
    return [row for row in rows if row['targetId'] in selected]


def _selection(manifest, section, claim_id, target_id, component_id, limit):
    _validate_section_limit(section, limit)
    _validate_known_selectors(manifest, claim_id, target_id)
    _validate_component_selector(manifest, section, claim_id, component_id)


def _validate_section_limit(section, limit):
    if section not in GUIDE_SECTIONS:
        raise ResultManifestError('unknown guide section')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ResultManifestError('guide limit must be 1..100')


def _validate_known_selectors(manifest, claim_id, target_id):
    for identifier, collection in ((claim_id, 'claims'), (target_id, 'targets')):
        if identifier is not None and not any(row['id'] == identifier for row in manifest[collection]):
            raise ResultManifestError(f'unknown {collection} selector')


def _validate_component_selector(manifest, section, claim_id, component_id):
    if section != 'exposition':
        if component_id is not None:
            raise ResultManifestError('component selection requires exposition section')
        return
    if claim_id is None or component_id is None:
        raise ResultManifestError('exposition requires exact claim and component selectors')
    claim = next(row for row in manifest['claims'] if row['id'] == claim_id)
    if component_id not in claim['components']:
        raise ResultManifestError('unknown component selector for claim')


def _header(manifest, companion, currencies, binding, query):
    status = 'unavailable'
    if companion is not None:
        stale = companion['manifestRevision'] != manifest['revision'] or 'historical' in currencies['steps'].values()
        status = 'historical' if stale else 'available'
    return {'operation': 'guide', 'schema': 'ladon-result-guide-view-v1', 'status': 'guided',
            'scope': 'offline-supplied-evidence', 'readingOrder': 'authored',
            'reuseApplicability': 'not-checked', 'guideStatus': status,
            'resultId': manifest['resultId'], 'revision': manifest['revision'],
            'section': query['section'], 'query': query, 'inputBinding': binding,
            'availableSections': list(GUIDE_SECTIONS),
            'axes': {'checking': 'stored-operations-only', 'sourceFreshness': 'not-assessed',
                     'correspondence': 'manifest-reviews', 'explanation': 'guide-reviews',
                     'attribution': 'guide-reviews', 'proofCoverage': 'unknown'},
            'limitations': ['authored-order-is-not-a-derivation', 'reviews-are-self-attributed',
                            'declaration-dependencies-are-structural-navigation',
                            'citations-do-not-establish-priority', 'guide-does-not-run-checks']}
