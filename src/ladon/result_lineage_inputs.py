"""Validate explicit revision-bound selections using the packaged shape owner."""
from __future__ import annotations

import json
from importlib.resources import files

from ladon._result_manifest_shape import validate_document_shape
from ladon.result_manifest_io import MAX_MANIFEST_BYTES, ResultManifestError, canonical_json


def validate_lineage_inputs(value, manifest):
    """Detach a bounded selection document; historical revisions remain legal."""
    encoded = canonical_json(value)
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise ResultManifestError('lineage inputs exceed the 16 MiB input limit')
    schema = json.loads(files('ladon.schemas').joinpath('ladon-result-lineage-inputs-v1.schema.json').read_text())
    validate_document_shape(value, schema)
    if value['resultId'] != manifest['resultId']:
        raise ResultManifestError('lineage inputs result ID does not match manifest')
    ids = [r['id'] for r in value['entries']]
    if len(ids) != len(set(ids)):
        raise ResultManifestError('duplicate lineage entry ID')
    targets = {r['id'] for r in manifest['targets']}
    if any(r['targetId'] not in targets for r in value['entries']):
        raise ResultManifestError('lineage inputs reference an unknown target')
    return json.loads(encoded)
