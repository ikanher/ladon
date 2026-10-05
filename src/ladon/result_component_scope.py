"""Add a bounded attribution and formal-statement projection to component cards."""
from __future__ import annotations

from collections import defaultdict

_REFERENCE_PREVIEW_LIMIT = 10


def apply_component_scope(manifest, cards, assessment_rows):
    """Enrich component cards with one shared coverage population per claim."""
    claim_indexes = {row['id']: index for index, row in enumerate(manifest['claims'])}
    target_cards = {row['targetId']: row for row in cards['targets']}
    targets = {row['id']: (index, row, target_cards[row['id']]['resolution'])
               for index, row in enumerate(manifest['targets'])}
    links = _component_links(manifest)
    assessments = _assessments_by_component(assessment_rows)
    coverage = _coverage_by_claim(manifest, cards['components'], links)
    statements = {identifier: formal_statement(target, resolution)
                  for identifier, (_, target, resolution) in targets.items()}
    for card in cards['components']:
        _apply_card(card, manifest, claim_indexes, targets, links, assessments, coverage, statements)
    return cards


def _component_links(manifest):
    links = defaultdict(list)
    for index, link in enumerate(manifest['links']):
        for component_id in link['componentIds']:
            links[(link['claimId'], component_id)].append((index, link))
    return links


def _assessments_by_component(rows):
    result = defaultdict(list)
    for row in rows:
        result[(row['claimId'], row['componentId'])].append(row)
    return result


def _coverage_by_claim(manifest, cards, links):
    rows_by_claim = defaultdict(dict)
    for card in cards:
        rows_by_claim[card['claimId']][card['componentId']] = card
    coverage = {}
    for index, claim in enumerate(manifest['claims']):
        component_rows = []
        refs = {
            '/components': _reference(manifest, f'/claims/{index}/components', append=False),
            '/mappingSources': _reference(manifest, '/links', append=False),
        }
        mapped = 0
        for ordinal, component_id in enumerate(claim['components']):
            card = rows_by_claim[claim['id']][component_id]
            targets = card['mapping']['targetIds']
            status = 'mapped' if targets else 'unmapped'
            mapped += bool(targets)
            component_rows.append({
                'componentId': component_id,
                'mappingStatus': status,
                'targetIds': targets,
            })
            if ordinal < _REFERENCE_PREVIEW_LIMIT:
                refs[f'/components/{ordinal}/targetIds'] = _reference(manifest, '/links', append=False)
        coverage[claim['id']] = {
            'mapped': mapped,
            'unmapped': len(claim['components']) - mapped,
            'components': component_rows,
            'references': refs,
        }
    return coverage


def _apply_card(card, manifest, claim_indexes, targets, links, assessments, coverage, statements):
    claim_index = claim_indexes[card['claimId']]
    component_id = card['componentId']
    claim = manifest['claims'][claim_index]
    attached = assessments[(card['claimId'], component_id)]
    current = [row for row in attached if row['currency'] == 'current']
    card['wholeClaimStatement'] = claim['statement']
    card['statementScope'] = 'whole-claim-context'
    component_scope = {
        'status': 'reported' if current else 'unavailable',
        'basis': 'attributed-assessment-scopes-not-extracted-statements',
        'descriptions': [_scope_description(row) for row in attached],
    }
    if attached:
        component_scope['references'] = _scope_references(attached)
    card['componentScope'] = component_scope
    card['claimComponentCoverage'] = coverage[card['claimId']]
    card['formalStatements'] = [statements[identifier] for identifier in card['mapping']['targetIds']]
    references = card.setdefault('references', {})
    references['/wholeClaimStatement'] = _reference(manifest, f'/claims/{claim_index}/statement')
    _component_link_reference(manifest, card, links, references)
    _formal_statement_references(manifest, card, targets, references)


def _scope_description(row):
    return {
        'assessmentId': row['id'],
        'scope': row['scope'],
        'author': row['author'],
        'currency': row['currency'],
    }


def _scope_references(rows):
    first = rows[0]['references']['']
    references = {'/descriptions': {**first, 'pointer': '/assessments', 'appendPath': False}}
    for index, row in enumerate(rows[:_REFERENCE_PREVIEW_LIMIT]):
        source = row['references']['']
        pointer = source['pointer']
        references[f'/descriptions/{index}'] = source
        references[f'/descriptions/{index}/assessmentId'] = {**source, 'pointer': pointer + '/id'}
        references[f'/descriptions/{index}/scope'] = {**source, 'pointer': pointer + '/scope'}
        references[f'/descriptions/{index}/author'] = {**source, 'pointer': pointer + '/author'}
    return references


def _component_link_reference(manifest, card, links, references):
    sources = links[(card['claimId'], card['componentId'])]
    card['mappingSources'] = [
        {**link, 'references': {
            '': _reference(manifest, f'/links/{index}'),
            '/componentIds': _reference(manifest, f'/links/{index}/componentIds'),
        }} for index, link in sources]
    references['/mappingSources'] = _reference(manifest, '/links', append=False)


def _formal_statement_references(manifest, card, targets, references):
    if not card['formalStatements']:
        return
    references['/formalStatements'] = _reference(manifest, '/targets', append=False)
    for ordinal, statement in enumerate(card['formalStatements'][:_REFERENCE_PREVIEW_LIMIT]):
        target_index, _target, _resolution = targets[statement['targetId']]
        references[f'/formalStatements/{ordinal}'] = _reference(manifest, f'/targets/{target_index}')
        references[f'/formalStatements/{ordinal}/resolution'] = _reference(
            manifest, f'/targets/{target_index}', append=False,
        )
        for key, source_key in (('targetId', 'id'), ('targetRevision', 'revision'), ('name', 'name'), ('typeText', 'typeText')):
            references[f'/formalStatements/{ordinal}/{key}'] = _reference(
                manifest, f'/targets/{target_index}/{source_key}',
            )


def formal_statement(target, resolution):
    """Project one exact target using its existing resolution, without checking."""
    return {
            'targetId': target['id'],
            'targetRevision': target['revision'],
            'name': target['name'],
            'typeText': target['typeText'],
            'statementAuthority': 'stored-canonical-type-text' if resolution['status'] == 'resolved' else 'manifest-supplied',
            'resolution': resolution,
            'parameters': {'status': 'unavailable', 'reason': 'no-bound-structured-declaration-observation'},
            'checkingScope': 'inspect-checking-section',
            'reuseApplicability': 'not-checked',
        }


def _reference(manifest, pointer, *, append=True):
    result = {'input': 'manifest', 'revision': manifest['revision'], 'pointer': pointer}
    if not append:
        result['appendPath'] = False
    return result
