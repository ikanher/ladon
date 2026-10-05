"""Guide population and stored-selection continuation cannot omit or mix inputs."""
from __future__ import annotations

import copy
import json
import sqlite3

import pytest
from support.result_guide import guide_inputs, revision
from test_result_lineage import _lineage_fixture

from ladon.result_guides import guide_result_manifest
from ladon.result_inspection_page import text_projection


@pytest.mark.parametrize('section', ['citations', 'reviews'])
def test_all_long_citations_and_reviews_remain_reachable(section):
    manifest, artifacts, guide = guide_inputs()
    row = guide[section][0]
    field = 'assertion' if section == 'citations' else 'rationale'
    population = []
    for i in range(107):
        item = copy.deepcopy(row)
        item.update(id=f'annotation-{i}')
        item[field] = 'λ' * 12000
        if section == 'citations':
            item['revision'] = revision('citation', item)
        population.append(item)
    guide[section] = population
    observed, omissions, cursor = [], [], None
    while True:
        page = guide_result_manifest(manifest, artifacts, guide_inputs=guide,
                                     section=section, limit=100, cursor=cursor)
        _assert_bounds_and_parity(page)
        observed.extend(r['id'] for r in page['rows'])
        omissions.extend(r['fieldOmissions'] for r in page['rows'])
        cursor = page['pagination']['nextCursor']
        if cursor is None:
            break
    _assert_annotations(observed, omissions, population, section, field)


def _assert_annotations(observed, omissions, population, section, field):
    assert observed == [r['id'] for r in population]
    for index, omitted in enumerate(omissions):
        ref = next(item['reference'] for item in omitted if item['path'] == '/' + field)
        assert ref['input'] == 'guide-inputs'
        assert ref['pointer'] == f'/{section}/{index}/{field}'


def _assert_bounds_and_parity(page):
    text = text_projection(page)
    assert len(text.encode()) + 1 <= 32768
    assert len(json.dumps(page, ensure_ascii=False, separators=(',', ':')).encode()) + 1 <= 32768
    assert {k: json.loads(v) for k, v in (line.split(': ', 1) for line in text.splitlines())} == page


def test_changed_lineage_observation_invalidates_guide_cursor(tmp_path):
    manifest, artifacts, lineage, db, inserted = _lineage_fixture(tmp_path)
    first = guide_result_manifest(manifest, artifacts, section='assumptions', limit=1,
                                  lineage_inputs=lineage, lineage_base=tmp_path)
    assert first['pagination']['nextCursor']
    with sqlite3.connect(db) as connection:
        connection.execute('INSERT INTO lineage_trust VALUES (?,?,?,?)',
                           (inserted['closureId'], 'axiom_reference', 'value', 'New.axiom'))
    with pytest.raises(ValueError, match='cursor'):
        guide_result_manifest(manifest, artifacts, section='assumptions', limit=1,
                              lineage_inputs=lineage, lineage_base=tmp_path,
                              cursor=first['pagination']['nextCursor'])
