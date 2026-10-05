"""Lazy authored guide cards with exact input references and revision bindings."""
from __future__ import annotations

from collections.abc import Sequence

from ladon.result_inspection_cards import input_reference
from ladon.result_inspection_page import inspection_digest


class GuideCards(Sequence):
    """Build only the selected page, preserving authored population order."""

    def __init__(self, companion, currencies, manifest, resolutions, section, claim_id, target_id):
        self.companion = companion
        self.currencies = currencies
        self.manifest = manifest
        self.resolutions = resolutions
        self.section = section
        self.digest = inspection_digest(companion)
        self.steps = {row['id']: row for row in companion['steps']}
        self.targets = {row['id']: (i, row) for i, row in enumerate(manifest['targets'])}
        self.selected = [i for i, row in enumerate(companion[section])
                         if self._selected(row, claim_id, target_id)]

    def _selected(self, row, claim_id, target_id):
        step = row if self.section == 'steps' else self.steps[row['stepId']]
        claim_matches = claim_id is None or step['claimId'] == claim_id
        target_matches = target_id is None or any(r['targetId'] == target_id for r in step['targetRevisions'])
        return claim_matches and target_matches

    def __len__(self):
        return len(self.selected)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [self[i] for i in range(*key.indices(len(self)))]
        index = self.selected[key]
        row = self.companion[self.section][index]
        reference = input_reference('guide-inputs', self.digest, f'/{self.section}/{index}')
        card = {**row, 'currency': self.currencies[self.section][row['id']],
                'authority': 'attributed-review' if self.section == 'reviews' else 'attributed-annotation',
                'identityAuthentication': 'not-assessed', 'references': {'': reference}}
        if self.section == 'steps':
            card.update(stepId=row['id'], position=index + 1,
                        targetBindings=[self._binding(r) for r in row['targetRevisions']])
            card['references']['/targetBindings'] = {**reference, 'pointer': reference['pointer'] + '/targetRevisions',
                                                      'appendPath': False}
        elif self.section == 'citations':
            card['citationId'] = row['id']
        return card

    def _binding(self, binding):
        index, target = self.targets[binding['targetId']]
        matches = binding['revision'] == target['revision']
        row = {'targetId': target['id'], 'requestedRevision': binding['revision'],
               'currentRevision': target['revision'], 'status': 'current' if matches else 'historical',
               'statementAvailability': 'supplied' if matches else 'unavailable',
               'hypotheses': {'status': 'unavailable', 'reason': 'no-structured-hypotheses-extraction'},
               'reuseApplicability': 'not-checked'}
        if matches:
            reference = input_reference('manifest', self.manifest['revision'], f'/targets/{index}')
            row.update(typeText=target['typeText'], source=target['source'],
                       resolution=self.resolutions[target['id']], sourceFreshness='not-assessed',
                       references={'/typeText': {**reference, 'pointer': reference['pointer'] + '/typeText'},
                                   '/source': {**reference, 'pointer': reference['pointer'] + '/source'},
                                   '/resolution': {**reference, 'appendPath': False}})
        return row


def selected_guide_targets(manifest, companion, currencies, claim_id, target_id):
    """Include current supporting targets without creating correspondence links."""
    if claim_id is None and target_id is None:
        return None
    selected = {row['id'] for row in manifest['targets']}
    if claim_id is not None:
        associated = {t for link in manifest['links'] if link['claimId'] == claim_id for t in link['targetIds']}
        associated.update(_supporting_targets(companion, currencies, claim_id))
        selected &= associated
    if target_id is not None:
        selected &= {target_id}
    return selected


def _supporting_targets(companion, currencies, claim_id):
    if companion is None:
        return set()
    return {ref['targetId'] for step in companion['steps']
            if step['claimId'] == claim_id and currencies['steps'][step['id']] == 'current'
            for ref in step['targetRevisions']}
