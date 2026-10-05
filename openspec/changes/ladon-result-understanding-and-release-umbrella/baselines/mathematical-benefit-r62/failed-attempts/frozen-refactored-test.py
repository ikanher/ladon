"""r62 presentation contract; assertion-preserving quality refactor of frozen red.

Proposed command:
  PYTHONPATH=src:tests pytest -q tests/test_r62_presentation_contract.py
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from ladon.source_goal_completion_cli import render_completion_text


ROOT = Path(__file__).resolve().parents[1]
R60 = ROOT / 'tests/fixtures/result_manifest/presentation-r62'
R59_CAPTURE = R60 / 'capture.json'


def _local_declarations(text, names):
    alternatives = '|'.join(re.escape(name) for name in sorted(names, key=len, reverse=True))
    return [(match.group(1), match.start()) for match in re.finditer(
        rf'(?m)^\s+({alternatives})\s*:', text
    )]


def _payload(local_context):
    return {
        'status': 'incomplete', 'captureId': 'fixture-capture', 'termDigest': 'fixture-term',
        'application': {'status': 'incomplete', 'originalGoal': {'typeDisplay': 'x = x'},
                        'residualGoals': [{'goalId': 'r0', 'typeDisplay': 'x = x',
                                           'localContext': local_context}]},
        'replay': {'status': 'not-run'},
        'trust': {'coverage': 'unavailable', 'observedAxioms': None}, 'diagnostic': None,
    }


def test_r60_context_declarations_stay_in_capture_order_and_show_their_roles():
    raw = json.loads((R60 / 'completion-b-json.stdout').read_text())
    context = raw['application']['residualGoals'][0]['localContext']
    internal = [x for x in context if x['implementationDetail']]
    usable = [x for x in context if not x['implementationDetail']]
    assert [x['userName'] for x in internal] == ['_example']
    assert [x['userName'] for x in usable] == [
        'point', 'h', 'boundary', 'query', 'hNonFull', 'hh',
        'hBoundaryNonneg', 'hBoundaryQuery',
    ]
    text = render_completion_text(raw)
    names = {x['userName'] for x in context}
    declarations = _local_declarations(text, names)
    assert [name for name, _ in declarations] == [x['userName'] for x in context]
    _assert_roles(text, declarations)
    assert '0 ≤ Mf.DP.fixedEpochCenterGap point h boundary' in text


def _assert_roles(text, declarations):
    lower = text.lower()
    internal_pos = declarations[0][1]
    usable_pos = declarations[1][1]
    internal_markers = [lower.find(label) for label in ('implementation detail', 'internal local')]
    usable_markers = [lower.find(label) for label in ('usable premise', 'usable local')]
    internal_markers = [pos for pos in internal_markers if 0 <= pos < internal_pos]
    usable_markers = [pos for pos in usable_markers if internal_pos < pos < usable_pos]
    assert internal_markers and usable_markers


def test_completion_renders_actual_and_multiline_unicode_values_without_mutating_input():
    r59_context = json.loads(R59_CAPTURE.read_text())['capture']['goal']['localContext']
    actual_definition = copy.deepcopy(next(x for x in r59_context if x['userName'] == 'z'))
    assert actual_definition['valueDisplay'] == 'h'
    multiline_definition = {
        'userName': 'w', 'typeDisplay': 'Nat', 'typeStructural': 'Nat',
        'implementationDetail': False, 'valueDisplay': 'let α := 1\nα + 1',
        'valueStructural': 'fixture-value',
    }
    context = [
        {'userName': '_internal', 'typeDisplay': 'Nat', 'implementationDetail': True,
         'valueDisplay': '', 'valueStructural': ''},
        {'userName': 'h', 'typeDisplay': 'x = x', 'implementationDetail': False,
         'valueDisplay': '', 'valueStructural': ''},
        actual_definition,
        multiline_definition,
    ]
    payload = _payload(context)
    before = copy.deepcopy(payload)
    text = render_completion_text(payload)
    failures = []
    if not re.search(r'(?m)^\s+z\s*:\s*x = x\s*:=\s*h\s*$', text):
        failures.append('retained r59 local definition value is absent at its declaration')
    if 'let α := 1\nα + 1' not in text:
        failures.append('multiline Unicode local definition value is absent')
    if payload != before:
        failures.append('text renderer mutated its input payload')
    if failures:
        raise AssertionError('; '.join(failures))


def test_raw_focused_exposition_projection_prioritizes_reader_content():
    # Root supplies this immutable transport fixture after recording the full raw
    # ExpositionCards row from the real broadened-average guide inputs.
    raw = json.loads((R60 / 'exposition.json').read_text())
    from ladon.result_inspection_page import inspect_page, text_projection

    header = {key: value for key, value in raw['header'].items()
              if key not in {'rows', 'pagination'}}
    page = inspect_page(header, [raw['row']], raw['header']['inputBinding'], 1, None)
    assert len(json.dumps(page, ensure_ascii=False, separators=(',', ':')).encode()) + 1 <= 32768
    text = text_projection(page)
    assert len(text.encode()) + 1 <= 32768
    assert {key: json.loads(value) for key, value in
            (line.split(': ', 1) for line in text.splitlines())} == page

    row = page['rows'][0]
    source = raw['row']
    _assert_focus(row, source)
    _assert_type_excerpt(row, source)


def _assert_focus(row, source):
    failures = []
    # These fields are short in the supplied control and must remain complete.
    if row['paragraph']['explanation'] != source['paragraph']['explanation']:
        failures.append('short paragraph was clipped')
    if row['reviews'][0]['rationale'] != source['reviews'][0]['rationale']:
        failures.append('short review rationale was clipped')
    selected = row['selectedComponent']
    if selected['componentId'] != 'average':
        failures.append('selected component identity was lost')
    coverage = selected['claimComponentCoverage']
    if coverage['unmapped'] != 1:
        failures.append('unmapped sibling count was lost')
    siblings = {x['componentId']: x['mappingStatus']
                for x in coverage['components']}
    if siblings != {'transcript': 'mapped', 'average': 'unmapped'}:
        failures.append(f'sibling coverage identities/statuses were clipped: {siblings}')

    if failures:
        raise AssertionError('; '.join(failures))


def _assert_type_excerpt(row, source):
    failures = []
    # A type that was clipped in this concrete row must be visibly identified as
    # an excerpt and retain a resolvable exact-source pointer. If it fits in full,
    # its exact source text is the sufficient route.
    source_type = source['supportingStatements'][0]['typeText']
    shown_type = row['supportingStatements'][0]['typeText']
    if shown_type != source_type:
        if 'excerpt' not in shown_type.lower():
            failures.append('clipped formal type is not labelled as an excerpt')
        omission = next((item for item in row['fieldOmissions']
                         if item['path'] == '/supportingStatements/0/typeText'), None)
        if (omission is None or omission['reference'].get('input') != 'manifest'
                or not omission['reference'].get('pointer', '').endswith('/typeText')):
            failures.append('clipped formal type has no exact complete-record route')
    if failures:
        raise AssertionError('; '.join(failures))
