"""The packaged shape and semantic review boundaries agree for guide inputs."""
from __future__ import annotations

import copy
import json
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from support.result_guide import guide_inputs, reseal, revision


@pytest.mark.parametrize('bad', [None, 'unknown', 'actor', 'unicode', 'timestamp', 'authors'])
def test_packaged_schema_and_runtime_shape_parity(bad):
    from ladon.result_guide_inputs import validate_result_guide
    manifest, _, guide = guide_inputs()
    if bad == 'unknown':
        guide['citations'][0]['work']['extra'] = True
    elif bad == 'actor':
        guide['steps'][0]['author']['kind'] = 'trusted'
    elif bad == 'unicode':
        guide['steps'][0]['explanation'] = 'λ' * 65537
    elif bad == 'timestamp':
        guide['reviews'][0]['timestamp'] = '2026-10-03T12:00:00'
    elif bad == 'authors':
        guide['citations'][0]['work']['authors'] = ['A'] * 10001
    reseal(guide)
    schema = json.loads(files('ladon.schemas').joinpath('ladon-result-guide-v1.schema.json').read_text())
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(guide))
    assert bool(errors) == (bad is not None)
    if bad is None:
        assert validate_result_guide(guide, manifest) == guide
    else:
        with pytest.raises(ValueError):
            validate_result_guide(guide, manifest)


def test_disputed_attribution_and_explanation_reviews_have_independent_currency():
    from ladon.result_guide_inputs import guide_currencies, validate_result_guide
    manifest, _, guide = guide_inputs()
    citation = guide['citations'][0]
    review = copy.deepcopy(guide['reviews'][0])
    review.update(id='disputed-origin', scope='attribution', status='disputed',
                  citationId=citation['id'], citationRevision=citation['revision'])
    guide['reviews'].append(review)
    assert guide_currencies(validate_result_guide(guide, manifest), manifest)['reviews'] == {
        'review-condition': 'current', 'disputed-origin': 'current'}
    citation['locator'] = 'A different passage'
    citation['revision'] = revision('citation', citation)
    assert guide_currencies(validate_result_guide(guide, manifest), manifest)['reviews'] == {
        'review-condition': 'current', 'disputed-origin': 'historical'}
    assert guide['reviews'][1]['status'] == 'disputed'


@pytest.mark.parametrize('bad', ['forward', 'wrong-targets', 'duplicate-prerequisite', 'scope'])
def test_semantic_contradictions_fail_before_projection(bad):
    from ladon.result_guide_inputs import validate_result_guide
    manifest, _, guide = guide_inputs()
    if bad == 'forward':
        guide['steps'][0]['prerequisites'] = [{'stepId': 'argument', 'revision': guide['steps'][1]['revision']}]
    elif bad == 'wrong-targets':
        guide['reviews'][0]['targetRevisions'] = []
    elif bad == 'duplicate-prerequisite':
        guide['steps'][1]['prerequisites'] *= 2
    else:
        guide['reviews'][0].update(citationId='paper-citation', citationRevision=guide['citations'][0]['revision'])
    reseal(guide)
    with pytest.raises(ValueError):
        validate_result_guide(guide, manifest)
