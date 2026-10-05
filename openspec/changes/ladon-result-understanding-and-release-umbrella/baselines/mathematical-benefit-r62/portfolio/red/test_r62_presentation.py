"""Independent red proposals for r62 presentation defects.

Run from the repository with:
  PYTHONPATH=src:tests pytest -q .codex/state/benefit-readers-r62/red/test_r62_presentation.py
The field reproduction uses retained r60/r61 artifacts; assertions concern reader
information and stable input identity, not internal compactor thresholds.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from ladon.source_goal_completion_cli import render_completion_text
from ladon.result_guides import guide_result_manifest
from ladon.result_inspection_page import text_projection
from support.result_guide import clone, guide_inputs, reseal, revision


ROOT = Path(__file__).resolve().parents[4]
R60 = ROOT / 'openspec/changes/ladon-goal-capture-and-application-probes/evidence/application-handoff-r60/field'
R59_CAPTURE = ROOT / 'openspec/changes/ladon-goal-capture-and-application-probes/evidence/application-completion-r59/field/capture.json'


def test_recorded_completion_text_keeps_context_classes_and_local_values():
    raw = json.loads((R60 / 'completion-b-json.stdout').read_text())
    before = copy.deepcopy(raw)
    text = render_completion_text(raw)
    residual = raw['application']['residualGoals'][0]
    implementation = next(x for x in residual['localContext'] if x['implementationDetail'])
    usable = [x for x in residual['localContext'] if not x['implementationDetail']]
    assert implementation['typeDisplay'] in text
    assert 'implementation detail' in text.lower() or 'internal local' in text.lower()
    assert 'usable premises' in text.lower() or 'proof context' in text.lower()
    assert [x['userName'] for x in usable] == [
        '_example', 'point', 'h', 'boundary', 'query', 'hNonFull', 'hh',
        'hBoundaryNonneg', 'hBoundaryQuery',
    ]
    # R60 has no local definition in this particular residual; pair it with a
    # value-bearing maintained fixture below so the regression covers rendering.
    assert raw == before
    assert '0 ≤ Mf.DP.fixedEpochCenterGap point h boundary' in text
    assert 'transitive trust coverage: unavailable' in text


def test_completion_renderer_shows_definition_value_and_keeps_payload_untouched():
    captured = json.loads(R59_CAPTURE.read_text())['capture']['goal']['localContext']
    local_definition = next(x for x in captured if x['userName'] == 'z')
    assert local_definition['valueDisplay'] == 'h'
    payload = {
        'status': 'incomplete', 'captureId': 'fixture-capture', 'termDigest': 'fixture-term',
        'application': {'status': 'incomplete', 'originalGoal': {'typeDisplay': 'x = x'},
                        'residualGoals': [{'typeDisplay': 'x = x', 'localContext': [
                            {'userName': '_internal', 'typeDisplay': 'Nat', 'implementationDetail': True,
                             'valueDisplay': 'let α := 1\nα + 1', 'valueStructural': 'expr'},
                            {'userName': 'h', 'typeDisplay': 'x = x', 'implementationDetail': False,
                             'valueDisplay': '', 'valueStructural': ''},
                            local_definition,
                        ]}]},
        'replay': {'status': 'not-run'},
        'trust': {'coverage': 'unavailable', 'observedAxioms': None}, 'diagnostic': None,
    }
    before = copy.deepcopy(payload)
    text = render_completion_text(payload)
    assert 'let α := 1\nα + 1' in text
    assert text.index('_internal') < text.index('h : x = x') < text.index('z : x = x := h')
    assert payload == before


def test_completion_json_and_text_field_records_agree_on_local_names():
    payload = json.loads((R60 / 'completion-b-json.stdout').read_text())
    text = (R60 / 'completion-b-text.stdout').read_text()
    expected = [x['userName'] for x in payload['application']['residualGoals'][0]['localContext']]
    positions = [text.index(name) for name in expected]
    assert positions == sorted(positions)
    assert '0 ≤ Mf.DP.fixedEpochCenterGap point h boundary' in text


def test_recorded_broadened_average_page_prioritizes_paragraph_reviews_and_uncovered_sibling():
    path = ROOT / 'openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/exposition-scope-r61/field/broadened-average.stdout'
    page = json.loads(path.read_text())
    assert len(json.dumps(page, ensure_ascii=False).encode()) + 1 <= 32768
    assert len(text_projection(page).encode()) + 1 <= 32768
    row = page['rows'][0]
    assert 'sufficient condition' in row['paragraph']['explanation']
    assert 'bindings an otherwise useful explanation' in row['reviews'][0]['rationale']
    coverage = row['selectedComponent']['claimComponentCoverage']
    assert coverage['unmapped'] == 1
    assert {x['componentId']: x['mappingStatus'] for x in coverage['components']}['average'] == 'unmapped'
    assert row['selectedComponent']['componentId'] == 'average'
    assert 'hSensitivity' in row['supportingStatements'][0]['typeText']
    type_omission = next(x for x in row['fieldOmissions']
                         if x['path'] == '/supportingStatements/0/typeText')
    assert type_omission['reference']['input'] == 'manifest'
    assert type_omission['reference']['pointer'].endswith('/typeText')
    assert 'excerpt' in row['supportingStatements'][0]['typeText'].lower()
    # The selected and uncovered sibling are both visible without following a
    # cursor; the latter is the named average component from this exact control.
    siblings = {x['componentId']: x['mappingStatus'] for x in coverage['components']}
    assert siblings['transcript'] == 'mapped' and siblings['average'] == 'unmapped'
    assert any(x.get('reference') for x in row.get('fieldOmissions', []))


def test_compact_page_marks_clipped_formal_text_and_points_to_complete_record():
    manifest, artifacts, guide = guide_inputs()  # noqa: F405
    # Add a very large, realistic authored argument; source references must still
    # identify the complete input when the bounded view clips it.
    guide = clone(guide)  # noqa: F405
    guide['steps'][0]['explanation'] = 'A short passage with the sufficient condition. ' + 'λ' * 20000
    guide['steps'][0]['revision'] = revision('step', guide['steps'][0])  # noqa: F405
    guide = reseal(guide)  # noqa: F405
    page = guide_result_manifest(manifest, artifacts, guide_inputs=guide,
                                 section='steps', claim_id=manifest['claims'][0]['id'], limit=1)
    assert len(json.dumps(page, ensure_ascii=False).encode()) + 1 <= 32768
    omissions = page['rows'][0].get('fieldOmissions', [])
    assert all(x.get('reference', {}).get('input') for x in omissions)
    # Any clipped decision text must say at its point of use that it is an excerpt.
    clipped = page['rows'][0]['explanation']
    assert 'excerpt' in clipped.lower() or not omissions
    explanation_omission = next(x for x in omissions if x['path'] == '/explanation')
    assert explanation_omission['reference']['input'] == 'guide-inputs'
    assert explanation_omission['reference']['pointer'].endswith('/explanation')
