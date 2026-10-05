"""Lazy paragraph projection with explicit component context and scoped reviews."""
from __future__ import annotations

from collections.abc import Sequence

from ladon.result_component_scope import apply_component_scope, formal_statement
from ladon.result_guide_cards import GuideCards
from ladon.result_inspection_cards import input_reference
from ladon.result_inspection_page import inspection_digest


class ExpositionCards(Sequence):
    """Materialize only the current bounded page of authored paragraph rows."""

    def __init__(self, manifest, inputs, companion, currencies, claim_id, component_id, target_id):
        self.manifest = manifest
        self.inputs = inputs
        self.companion = companion
        self.currencies = currencies
        self.claim_id = claim_id
        self.component_id = component_id
        self.guide_digest = inspection_digest(companion)
        self.steps, self.step_indexes = _step_indexes(companion)
        self.reviews_by_step, self.review_indexes = _review_indexes(companion, self.steps)
        self.step_cards = GuideCards(companion, currencies, manifest, inputs.resolutions,
                                     'steps', claim_id, target_id)
        self.selected_component = _selected_component(manifest, inputs, claim_id, component_id)
        self.targets = {row['id']: (index, row) for index, row in enumerate(manifest['targets'])}
        self.selected = _selected_steps(companion, claim_id, target_id)

    def __len__(self):
        return len(self.selected)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [self[index] for index in range(*key.indices(len(self)))]
        source_index = self.selected[key]
        source = self.companion['steps'][source_index]
        step = self._step_card(source['id'])
        current = self.currencies['steps'][source['id']] == 'current'
        component = self._component_context(current)
        if not current:
            step['targetBindings'] = [self._historical_binding(binding)
                                      for binding in step['targetBindings']]
        supports = self._supporting_statements(step) if current else []
        reviews = self._reviews_for(source['id'])
        notices = _recheck_notices(source, source_index, reviews, current,
                                   self.guide_digest, self.review_indexes)
        return _paragraph_row(source, source_index, step, component, supports, reviews,
                              notices, current, self.guide_digest)

    def _component_context(self, current):
        component = dict(self.selected_component)
        component['associationBasis'] = 'caller-selected-component-not-correspondence-review'
        if not current:
            component['formalStatements'] = []
            component['references'] = {path: ref for path, ref in component['references'].items()
                                       if not path.startswith('/formalStatements')}
        return component

    def _reviews_for(self, step_id):
        rows = self.reviews_by_step.get(step_id, [])
        return [self._review_card(row, index) for index, row in enumerate(rows)]

    def _step_card(self, step_id):
        position = self.step_cards.selected.index(self.step_indexes[step_id])
        return dict(self.step_cards[position])

    def _historical_binding(self, binding):
        row = {key: value for key, value in binding.items()
               if key not in {'typeText', 'source', 'resolution', 'sourceFreshness', 'references'}}
        row.update(status='historical', statementAvailability='unavailable',
                   sourceFreshness='not-assessed')
        return row

    def _supporting_statements(self, step):
        rows = []
        for ordinal, binding in enumerate(step['targetBindings']):
            if binding['status'] != 'current' or binding['statementAvailability'] != 'supplied':
                continue
            target_index, target = self.targets[binding['targetId']]
            source = input_reference('manifest', self.manifest['revision'], f'/targets/{target_index}')
            resolution = self.inputs.resolutions[target['id']]
            statement = formal_statement(target, resolution)
            statement.update(source=target['source'],
                             relationship='guide-support-not-component-correspondence')
            if ordinal < 10:
                statement['references'] = {
                    '': source,
                    '/targetId': {**source, 'pointer': source['pointer'] + '/id'},
                    '/targetRevision': {**source, 'pointer': source['pointer'] + '/revision'},
                    '/name': {**source, 'pointer': source['pointer'] + '/name'},
                    '/typeText': {**source, 'pointer': source['pointer'] + '/typeText'},
                    '/source': {**source, 'pointer': source['pointer'] + '/source'},
                    '/resolution': {**source, 'appendPath': False},
                }
            rows.append(statement)
        return rows

    def _review_card(self, source, ordinal):
        index = self.review_indexes[source['id']]
        card = {**source, 'currency': self.currencies['reviews'][source['id']],
                'authority': 'attributed-review', 'identityAuthentication': 'not-assessed'}
        if ordinal < 10:
            card['references'] = {'': input_reference('guide-inputs', self.guide_digest,
                                                      f'/reviews/{index}')}
        return card



def _step_indexes(companion):
    rows = companion['steps']
    return ({row['id']: row for row in rows},
            {row['id']: index for index, row in enumerate(rows)})


def _review_indexes(companion, steps):
    by_step, indexes = {}, {}
    for index, row in enumerate(companion['reviews']):
        if row['scope'] == 'explanation' and row['stepId'] in steps:
            indexes[row['id']] = index
            by_step.setdefault(row['stepId'], []).append(row)
    return by_step, indexes


def _selected_component(manifest, inputs, claim_id, component_id):
    cards = {'components': inputs.sections['components'], 'targets': inputs.sections['targets']}
    rows = apply_component_scope(manifest, cards, inputs.sections['assessments'])['components']
    return next(row for row in rows
                if row['claimId'] == claim_id and row['componentId'] == component_id)


def _selected_steps(companion, claim_id, target_id):
    return [index for index, row in enumerate(companion['steps'])
            if row['claimId'] == claim_id and _has_target(row, target_id)]


def _has_target(step, target_id):
    return target_id is None or any(row['targetId'] == target_id for row in step['targetRevisions'])


def _paragraph_row(source, source_index, step, component, supports, reviews, notices, current, digest):
    source_reference = input_reference('guide-inputs', digest,
                                       f"/steps/{source_index}/targetRevisions")
    return {
        'paragraph': step,
        'references': {
            '/supportingStatements': {**source_reference, 'appendPath': False},
            '/reviews': {**input_reference('guide-inputs', digest, '/reviews'), 'appendPath': False},
            '/recheckNotices': {**input_reference('guide-inputs', digest, ''), 'appendPath': False},
        },
        'selectedComponent': component,
        'supportingStatements': supports,
        'reviews': reviews,
        'reviewStatus': 'current-attributed-reviews' if any(
            row['currency'] == 'current' for row in reviews
        ) else 'not-reviewed',
        'recheckNotices': notices,
        'checkingScope': 'explicit-application-operation-required',
        'reuseApplicability': 'not-checked',
        'mathematicalVerdict': 'not-inferred',
    }


def _recheck_notices(step, source_index, reviews, current, digest, review_indexes):
    notices = []
    if not current:
        notices.append({
            'reason': 'historical-paragraph-binding', 'stepId': step['id'],
            'references': {'': input_reference('guide-inputs', digest,
                                               f'/steps/{source_index}')},
        })
    for row in reviews:
        if row['currency'] == 'historical':
            notice = {'reason': 'historical-explanation-review', 'stepId': step['id'],
                      'reviewId': row['id']}
            if len(notices) < 10:
                index = review_indexes[row['id']]
                notice['references'] = {'': input_reference('guide-inputs', digest,
                                                             f'/reviews/{index}')}
            notices.append(notice)
    return notices


def unavailable_exposition():
    """One explicit placeholder when no guide input was supplied."""
    return [{'status': 'unavailable', 'reason': 'no-guide-inputs-supplied',
             'authority': 'not-assessed', 'supportingStatements': [], 'reviews': []}]
