"""Load verified transport members through existing result evidence owners."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from ladon.result_assessments import validate_result_assessments
from ladon.result_dossier import DossierInputs, prepare_dossier
from ladon.result_evidence_io import load_result_artifacts
from ladon.result_guide_inputs import validate_result_guide
from ladon.result_lineage_inputs import validate_lineage_inputs
from ladon.result_manifest import validate_result_manifest
from ladon.result_manifest_io import ResultManifestError, load_result_manifest


@dataclass
class BundleInputs:
    """A private verified snapshot and original identity-preserving documents."""

    root: Path
    index: dict
    identity: str
    manifest: dict
    artifacts: list
    guide: dict | None
    assessments: dict | None
    lineage: dict | None
    missing_history: list
    missing_lineage: list
    dossier: DossierInputs


def role_rows(index, role):
    return [row for row in index['inventory'] if row['role'] == role]


def _companion(root, index, role, validator, manifest):
    rows = role_rows(index, role)
    if not rows:
        return None
    return validator(load_result_manifest(root / rows[0]['path']), manifest)


def transport_lineage(index, original):
    """Never follow original database paths, including for omitted stores."""
    bindings = {row['entryId']: row['databaseId'] for row in index['lineageBindings']}
    entries = (original or {}).get('entries', [])
    if set(bindings) - {row['id'] for row in entries}:
        raise ResultManifestError('unknown lineage entry binding')
    stores = {row['id']: row for row in role_rows(index, 'lineage-database')}
    if set(bindings.values()) != set(stores):
        raise ResultManifestError('lineage binding requires exact selected database IDs')
    return _mapped_lineage(original, bindings, stores)


def _mapped_lineage(original, bindings, stores):
    portable = deepcopy(original)
    missing = []
    for number, entry in enumerate((portable or {}).get('entries', [])):
        store = stores.get(bindings.get(entry['id']))
        entry['database'] = store['path'] if store else f'missing/{number:05d}.sqlite3'
        if store is None:
            missing.append(entry['id'])
    return portable, missing


def _history(root, index, manifest):
    predecessors = {}
    for row in role_rows(index, 'predecessor'):
        previous = validate_result_manifest(load_result_manifest(root / row['path']))
        if previous['resultId'] != manifest['resultId'] or previous['revision'] in predecessors:
            raise ResultManifestError('conflicting predecessor result or revision')
        predecessors[previous['revision']] = previous
    visited = set()
    revision = manifest.get('previousRevision')
    while revision in predecessors and revision not in visited:
        visited.add(revision)
        revision = predecessors[revision].get('previousRevision')
    if visited != set(predecessors) or revision in visited:
        raise ResultManifestError('predecessor is outside the selected revision chain')
    return [revision] if revision else []


def load_bundle_inputs(root, index, identity):
    """Use owner validators on the complete inventory before any view selection."""
    manifest = validate_result_manifest(load_result_manifest(root / index['manifest']))
    if any(index[k] != manifest[k] for k in ('resultId', 'revision')):
        raise ResultManifestError('bundle and manifest identities disagree')
    artifacts = load_result_artifacts([root / row['path'] for row in role_rows(index, 'artifact')])
    guide = _companion(root, index, 'guide', validate_result_guide, manifest)
    assessments = _companion(root, index, 'assessments', validate_result_assessments, manifest)
    original = _companion(root, index, 'lineage', validate_lineage_inputs, manifest)
    lineage, missing = transport_lineage(index, original)
    history = _history(root, index, manifest)
    dossier = prepare_dossier(manifest, artifacts, assessments=assessments, lineage_inputs=lineage,
                              lineage_base=root, lineage_reference_base='bundle:' + identity)
    return BundleInputs(root, index, identity, manifest, artifacts, guide, assessments,
                        lineage, history, missing, dossier)
