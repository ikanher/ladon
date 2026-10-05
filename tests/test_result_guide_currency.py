from __future__ import annotations

import copy

import pytest
from support.result_guide import guide_inputs, revision


def _api():
    from ladon.result_guide_inputs import guide_currencies
    return guide_currencies


def test_currency_propagates_historical_prerequisite_edits_to_dependents_and_reviews():
    manifest, _, guide = guide_inputs()
    current = _api()(guide, manifest)
    assert current['steps'] == {'condition': 'current', 'argument': 'current'}
    assert current['citations'] == {'paper-citation': 'current'}
    assert current['reviews'] == {'review-condition': 'current'}

    changed = copy.deepcopy(guide)
    changed['steps'][0]['explanation'] = 'A revised explanation changes its identity.'
    changed['steps'][0]['revision'] = revision('step', changed['steps'][0])
    historical = _api()(changed, manifest)
    assert historical['steps'] == {'condition': 'current', 'argument': 'historical'}
    assert historical['citations']['paper-citation'] == 'historical'
    assert historical['reviews']['review-condition'] == 'historical'


def test_target_change_makes_bound_step_and_its_annotations_historical():
    manifest, _, guide = guide_inputs()
    from ladon.result_manifest_io import content_revision
    changed_manifest = copy.deepcopy(manifest)
    changed_manifest['targets'][0]['typeText'] = 'Changed target statement.'
    changed_manifest['targets'][0]['revision'] = content_revision('target', changed_manifest['targets'][0])
    changed_manifest['revision'] = content_revision('manifest', changed_manifest)
    currencies = _api()(guide, changed_manifest)
    assert currencies['steps'] == {'condition': 'historical', 'argument': 'historical'}
    assert currencies['reviews']['review-condition'] == 'historical'
    assert currencies['citations']['paper-citation'] == 'historical'


def test_old_target_revision_is_valid_historical_binding_not_rewritten():
    manifest, _, guide = guide_inputs()
    changed = copy.deepcopy(manifest)
    from ladon.result_manifest_io import content_revision
    changed['targets'][0]['typeText'] = 'New statement; old text is unavailable.'
    changed['targets'][0]['revision'] = content_revision('target', changed['targets'][0])
    changed['revision'] = content_revision('manifest', changed)
    checked = _api()(guide, changed)
    assert checked['steps']['condition'] == 'historical'
    assert guide['steps'][0]['targetRevisions'][0]['revision'] == manifest['targets'][0]['revision']


def test_currency_rejects_invalid_input_even_when_rows_are_unselected():
    manifest, _, guide = guide_inputs()
    broken = copy.deepcopy(guide)
    broken['citations'][0]['work']['authors'] = ['x'] * 10001
    with pytest.raises((ValueError, TypeError)):
        _api()(broken, manifest)
