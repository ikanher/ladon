"""Compose the existing dossier owner over explicitly supplied canonical inputs."""
from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from contextlib import contextmanager

from ladon.proofir_sqlite_v3 import project_envelopes
from ladon.proofir_v3_queries import query_v3_subject_evidence
from ladon.result_inspection_page import inspection_digest


@contextmanager
def subject_evidence_cards(manifest, catalog, resolutions, target_ids=None):
    """Keep persistent stores untouched; never discover evidence by theorem name."""
    connection = sqlite3.connect(':memory:')
    try:
        project_envelopes(connection, list(catalog.values()))
        revision = inspection_digest(sorted(catalog))
        targets = [target for target in manifest['targets']
                   if target_ids is None or target['id'] in target_ids]
        yield SubjectEvidenceCards(targets, resolutions, connection, revision)
    finally:
        connection.close()


class SubjectEvidenceCards(Sequence):
    """Materialize only cards visited by the requested output page."""

    def __init__(self, targets, resolutions, connection, revision):
        self.targets = targets
        self.resolutions = resolutions
        self.connection = connection
        self.revision = revision

    def __len__(self):
        return len(self.targets)

    def __getitem__(self, index):
        target = self.targets[index]
        return _card(target, self.resolutions[target['id']], self.connection, self.revision)


def _card(target, resolution, connection, revision):
    row = {'targetId': target['id'], 'resolution': resolution,
           'status': 'unavailable', 'authority': 'stored-evidence',
           'sourceFreshness': 'not-assessed', 'checking': 'stored-operations-only'}
    if resolution['status'] != 'resolved':
        return {**row, 'reason': 'target-not-resolved'}
    ref = target['subjectRef']
    subject = {'ownerArtifactId': ref['artifactId'], 'kind': 'declaration',
               'localId': ref['subjectId']}
    evidence = query_v3_subject_evidence(connection, subject, limit=100)
    reference = {'input': 'supplied-artifact-dossier', 'revision': revision,
                 'query': {'subject': subject, 'limit': 100}, 'pointer': ''}
    return {**row, 'status': 'available', 'evidence': evidence,
            'references': {'/evidence': reference}}
