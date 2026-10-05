"""Packaged bundle schema and runtime shape checks agree on scalar bounds."""
import copy
import json
from importlib.resources import files

import jsonschema
import pytest
from test_result_bundles import _export, _index

from ladon.result_bundle_contract import validate_bundle_index
from ladon.result_manifest_io import ResultManifestError


@pytest.mark.parametrize('size', [True, -1, 2**63, 1.5, '1'])
def test_inventory_sizes_reject_noninteger_or_unbounded_values(tmp_path, size):
    index = _index(_export(tmp_path))
    index['inventory'][0]['bytes'] = size
    schema = json.loads(files('ladon.schemas').joinpath('ladon-result-bundle-v1.schema.json').read_text())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(index, schema)
    with pytest.raises(ResultManifestError):
        validate_bundle_index(index)


def test_current_bundle_and_selection_schemas_are_packaged(tmp_path):
    index = _index(_export(tmp_path))
    selection = json.loads((tmp_path / 'selection.json').read_text())
    for document, filename in [(index, 'ladon-result-bundle-v1.schema.json'),
                               (selection, 'ladon-result-bundle-selection-v1.schema.json')]:
        schema = json.loads(files('ladon.schemas').joinpath(filename).read_text())
        jsonschema.validate(document, schema)
    changed = copy.deepcopy(index)
    changed['inventory'][0]['unexpected'] = 'not silently accepted'
    with pytest.raises(ResultManifestError):
        validate_bundle_index(changed)
