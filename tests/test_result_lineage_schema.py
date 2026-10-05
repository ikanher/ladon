"""Lineage selections are explicit bounded assertions, not manifest extensions."""
from __future__ import annotations

import copy
import json
from dataclasses import asdict
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator
from test_result_resolution import inputs
from test_theorem_lineage_store import _test_identity

from ladon.result_manifest_io import ResultManifestError


def companion(manifest):
    target = manifest['targets'][0]
    return {'schema': 'ladon-result-lineage-inputs-v1', 'resultId': manifest['resultId'],
            'manifestRevision': manifest['revision'], 'entries': [
                {'id': 'capture-1', 'targetId': target['id'], 'targetRevision': target['revision'],
                 'database': 'index.sqlite', 'closureId': 'closure-1',
                 'identity': asdict(_test_identity())}]}


def test_packaged_lineage_schema_and_runtime_agree_on_closed_input():
    from ladon.result_lineage_inputs import validate_lineage_inputs

    manifest, _ = inputs()
    value = companion(manifest)
    schema = json.loads(files('ladon.schemas').joinpath('ladon-result-lineage-inputs-v1.schema.json').read_text())
    validator = Draft202012Validator(schema)
    validator.validate(value)
    assert validate_lineage_inputs(value, manifest) == value
    for path in [('unknown',), ('entries', 0, 'unknown'), ('entries', 0, 'identity', 'unknown')]:
        bad = copy.deepcopy(value)
        cursor = bad
        for part in path[:-1]:
            cursor = cursor[part]
        cursor[path[-1]] = 'unexpected'
        assert list(validator.iter_errors(bad))
        with pytest.raises(ResultManifestError):
            validate_lineage_inputs(bad, manifest)


@pytest.mark.parametrize('mutation', ['duplicate', 'unknown-target', 'wrong-result', 'too-many'])
def test_invalid_lineage_bindings_are_rejected(mutation):
    from ladon.result_lineage_inputs import validate_lineage_inputs

    manifest, _ = inputs()
    value = companion(manifest)
    if mutation == 'duplicate':
        value['entries'] *= 2
    elif mutation == 'unknown-target':
        value['entries'][0]['targetId'] = 'absent'
    elif mutation == 'wrong-result':
        value['resultId'] = 'another-result'
    else:
        value['entries'] *= 1001
    with pytest.raises(ResultManifestError):
        validate_lineage_inputs(value, manifest)


def test_historical_revisions_remain_valid_input_without_becoming_current():
    from ladon.result_lineage_inputs import validate_lineage_inputs

    manifest, _ = inputs()
    value = companion(manifest)
    value['manifestRevision'] = 'sha256:' + 'a' * 64
    value['entries'][0]['targetRevision'] = 'sha256:' + 'b' * 64
    assert validate_lineage_inputs(value, manifest) == value
