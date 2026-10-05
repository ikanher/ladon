"""Proposed regression for retrying row overflow through public exposition."""
from __future__ import annotations

import copy

import pytest
from support.result_guide import guide_inputs, reseal
from test_result_resolution import seal

from ladon.result_guides import guide_result_manifest
from ladon.result_inspection_page import inspect_page, text_projection
from ladon.result_manifest_io import ResultManifestError, canonical_json, content_revision


def _multi_target_case():
    manifest, artifacts, guide = guide_inputs()
    original = copy.deepcopy(manifest['targets'][0])
    targets = []
    # Three additional valid targets push the un-compacted exposition over
    # the 24 KiB row budget while a smaller compaction level remains usable.
    for index in range(3):
        target = copy.deepcopy(original)
        target['id'] = f'overflow-target-{index}'
        target['name'] = f'Demo.overflow_target_{index}'
        target['typeText'] = 'T' * 80
        target['revision'] = content_revision('target', target)
        targets.append(target)
    manifest['targets'].extend(targets)
    manifest['links'][0]['targetIds'].extend(target['id'] for target in targets)
    seal(manifest)

    step = guide['steps'][0]
    additions = [{'targetId': target['id'], 'revision': target['revision']}
                 for target in targets]
    step['targetRevisions'].extend(copy.deepcopy(additions))
    guide['reviews'][0]['targetRevisions'].extend(copy.deepcopy(additions))
    guide['manifestRevision'] = manifest['revision']
    reseal(guide)
    return manifest, artifacts, guide


def _inspect(manifest, artifacts, guide):
    return guide_result_manifest(
        manifest, artifacts, guide_inputs=guide, section='exposition',
        claim_id='paper-theorem-1', component_id='implication',
    )


def test_public_exposition_retries_smaller_row_compaction():
    manifest, artifacts, guide = _multi_target_case()

    result = _inspect(manifest, artifacts, guide)

    assert result['section'] == 'exposition'
    assert result['pagination']['total'] == 1
    assert result['pagination']['returned'] == 1
    row = result['rows'][0]
    assert row['paragraph']['stepId'] == 'condition'
    assert row['paragraph']['authority'] == 'attributed-annotation'
    assert row['selectedComponent']['componentId'] == 'implication'
    assert row['paragraph']['targetBindings']
    assert len(canonical_json(row)) < 24 * 1024
    assert len(canonical_json(result)) + 1 <= 32 * 1024
    assert len(text_projection(result).encode()) + 1 <= 32 * 1024
    assert row['fieldOmissions']


def test_public_exposition_still_propagates_guide_reference_errors():
    manifest, artifacts, guide = guide_inputs()
    broken = copy.deepcopy(guide)
    broken['steps'][0]['targetRevisions'][0]['targetId'] = 'missing-reference-target'
    reseal(broken)

    with pytest.raises(ResultManifestError, match='duplicate or unknown ID'):
        _inspect(manifest, artifacts, broken)


def test_page_compaction_does_not_mask_missing_omission_reference():
    row = {'paragraph': {'targetBindings': [{'typeText': 'a formal type'}]}}
    with pytest.raises(ResultManifestError, match='exposition omission lacks an input reference'):
        inspect_page({'section': 'exposition'}, [row], 'binding', 1, None)
