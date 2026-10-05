"""Manifest-owned dossier cards; authored assertions never become checks."""
from __future__ import annotations

from collections import Counter, defaultdict

from ladon.result_assessments import assessment_currencies
from ladon.result_manifest import review_currency


def input_reference(kind, revision, pointer):
    return {'input': kind, 'revision': revision, 'pointer': pointer}


def manifest_cards(manifest, resolutions, companion):
    """Preserve all rows before the shared presentation boundary."""
    targets = {r['id']: r for r in manifest['targets']}
    claims = {r['id']: r for r in manifest['claims']}
    links = {r['id']: r for r in manifest['links']}
    assessment_revision = _assessment_revision(companion)
    assessment_rows = _assessments(manifest, companion, assessment_revision)
    by_component = defaultdict(list)
    for row in assessment_rows:
        by_component[(row['claimId'], row['componentId'])].append(row)
    reviews = []
    for i, row in enumerate(manifest['reviews']):
        link = links[row['linkId']]
        reviews.append({**row, 'claimId': link['claimId'], 'targetIds': link['targetIds'],
                        'currency': review_currency(row, link, claims[link['claimId']], targets),
                        'authority': 'attributed-review-assertion',
                        'references': {'': input_reference('manifest', manifest['revision'], f'/reviews/{i}')}})
    components = _components(manifest, resolutions, by_component, reviews, assessment_revision)
    return {'components': components, 'assessments': assessment_rows, 'reviews': reviews,
            'claims': [{**row, 'claimId': row['id'], 'authority': 'producer-supplied-statement',
                        'references': {'': input_reference('manifest', manifest['revision'], f'/claims/{i}')}}
                       for i, row in enumerate(manifest['claims'])],
            'targets': [{**row, 'targetId': row['id'], 'resolution': resolutions[row['id']],
                         'checking': 'inspect-checking-section', 'sourceFreshness': 'not-assessed',
                         'references': {'': input_reference('manifest', manifest['revision'], f'/targets/{i}')}}
                        for i, row in enumerate(manifest['targets'])]}


def _assessment_revision(companion):
    if companion is None:
        return None
    from ladon.result_inspection_page import inspection_digest
    return inspection_digest(companion)


def _assessments(manifest, companion, revision):
    if companion is None:
        return []
    currencies = assessment_currencies(companion, manifest)
    return [{**row, 'currency': currencies[i],
             'authority': 'attributed-component-assessment', 'reviewerAuthentication': 'not-assessed',
             'references': {
                 '': input_reference('assessments', revision, f'/assessments/{i}'),
                 '/scope': input_reference('assessments', revision, f'/assessments/{i}/scope'),
                 '/author': input_reference('assessments', revision, f'/assessments/{i}/author'),
             }}
            for i, row in enumerate(companion['assessments'])]


def _component_links(manifest):
    result = defaultdict(list)
    for link in manifest['links']:
        for part in link['componentIds']:
            result[(link['claimId'], part)].append(link)
    return result


def _components(manifest, resolutions, assessments, reviews, assessment_revision):
    by_component = _component_links(manifest)
    rows = []
    for i, claim in enumerate(manifest['claims']):
        for part in claim['components']:
            key = (claim['id'], part)
            rows.append(_component(manifest, i, claim, part, by_component[key],
                                   assessments[key], reviews, resolutions, assessment_revision))
    return rows


def _component(manifest, i, claim, part, links, attached, reviews, resolutions, assessment_revision):
    targets = sorted({t for link in links for t in link['targetIds']})
    current_reviews = _current_reviews(links, reviews)
    return _component_card(manifest, i, claim, part, targets, attached, current_reviews,
                           resolutions, assessment_revision)


def _current_reviews(links, reviews):
    link_ids = {r['id'] for r in links}
    return [r for r in reviews if r['linkId'] in link_ids and r['currency'] == 'current']


def _component_card(manifest, i, claim, part, targets, attached, current_reviews,
                    resolutions, assessment_revision):
    references = {
        '/statement': input_reference('manifest', manifest['revision'], f'/claims/{i}/statement'),
        '/document': input_reference('manifest', manifest['revision'], f'/claims/{i}/document'),
        '/mapping': {**input_reference('manifest', manifest['revision'], '/links'), 'appendPath': False},
        '/correspondence/reviews': {**input_reference('manifest', manifest['revision'], '/reviews'), 'appendPath': False},
        '': {**input_reference('manifest', manifest['revision'], f'/claims/{i}'), 'appendPath': False},
    }
    assessment_ref = _assessment_population_reference(attached, assessment_revision)
    if assessment_ref is not None:
        references['/assessments'] = assessment_ref
    return {
        'claimId': claim['id'], 'claimRevision': claim['revision'], 'componentId': part,
        'statement': claim['statement'], 'document': claim['document'],
        'mapping': {'status': 'mapped' if targets else 'unmapped', 'targetIds': targets},
        'resolution': {'statuses': dict(Counter(resolutions[t]['status'] for t in targets))},
        'assessmentStatus': 'reported' if any(r['currency'] == 'current' for r in attached) else 'unassessed',
        'assessments': attached,
        'correspondence': {'status': 'attributed-reviews' if current_reviews else 'not-reviewed',
                           'reviews': [{'id': r['id'], 'status': r['status'], 'reviewer': r['reviewer']}
                                       for r in current_reviews]},
        'checking': 'inspect-checking-section', 'expositionReview': 'not-assessed',
        'attributionReview': 'not-assessed',
            'references': references,
    }


def _assessment_population_reference(attached, revision):
    if revision is None:
        return None
    if attached:
        reference = attached[0]['references']['']
    else:
        reference = input_reference('assessments', revision, '/assessments')
    return {**reference, 'pointer': '/assessments', 'appendPath': False}

def select_rows(rows, manifest, claim_id, target_id):
    """Conjoin selectors; rows with no target cannot borrow a target's evidence."""
    target_claims = {r['claimId'] for r in manifest['links'] if target_id in r['targetIds']}
    claim_targets = {t for r in manifest['links'] if r['claimId'] == claim_id for t in r['targetIds']}
    return [row for row in rows if _selected(row, claim_id, target_id, target_claims, claim_targets)]


def _selected(row, claim_id, target_id, target_claims, claim_targets):
    targets = _row_targets(row)
    claim_matches = claim_id is None or _claim_matches(row, claim_id, targets, claim_targets)
    target_matches = target_id is None or _target_matches(row, target_id, targets, target_claims)
    return claim_matches and target_matches


def _row_targets(row):
    targets = set(row.get('targetIds', row.get('mapping', {}).get('targetIds', [])))
    targets.update(r['targetId'] for r in row.get('targetRevisions', []))
    targets.update(r['targetId'] for r in row.get('targetBindings', []))
    if 'targetId' in row:
        targets.add(row['targetId'])
    return targets


def _claim_matches(row, claim_id, targets, claim_targets):
    return row.get('claimId') == claim_id or (row.get('claimId') is None and bool(targets & claim_targets))


def _target_matches(row, target_id, targets, target_claims):
    return target_id in targets or (not targets and row.get('claimId') in target_claims and 'componentId' not in row)
