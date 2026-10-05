"""Prioritize a focused exposition by removing referenced duplicate context."""
from __future__ import annotations

import copy

from ladon.result_inspection_page import _escape, _reference
from ladon.result_manifest_io import ResultManifestError, canonical_json


def focused_exposition_row(row):
    """Deduplicate large formal context while preserving exact retrieval routes."""
    value = copy.deepcopy(row)
    references = _all_references(row)
    omissions = []
    paragraph = value.get('paragraph', {})
    component = value.get('selectedComponent', {})
    for index, binding in enumerate(paragraph.get('targetBindings', [])):
        for key in ('typeText', 'resolution', 'source'):
            _omit_field(binding, key, f'/paragraph/targetBindings/{index}/{key}',
                        references, omissions)
    _omit_component_duplicates(component, references, omissions)
    _omit_supporting_statement_duplicates(value, references, omissions)
    coverage = component.get('claimComponentCoverage', {})
    for index, sibling in enumerate(coverage.get('components', [])[:20]):
        _omit_field(sibling, 'targetIds',
                    f'/selectedComponent/claimComponentCoverage/components/{index}/targetIds',
                    references, omissions)
    _bound_sibling_preview(component, coverage, references, omissions)
    if omissions:
        value['fieldOmissions'] = omissions
    return value


def _omit_component_duplicates(component, references, omissions):
    for key in ('wholeClaimStatement', 'formalStatements', 'mappingSources', 'assessments'):
        _omit_field(component, key, '/selectedComponent/' + key, references, omissions)


def _omit_supporting_statement_duplicates(value, references, omissions):
    for index, statement in enumerate(value.get('supportingStatements', [])):
        for key in ('resolution', 'source'):
            path = f'/supportingStatements/{index}/{key}'
            _omit_field(statement, key, path, references, omissions)


def _omit_field(container, key, path, references, omissions):
    if key not in container:
        return
    removed = container[key]
    if removed in ('', [], {}):
        return
    container.pop(key)
    reference = _reference(path, references)
    if reference.get('reason') == 'projection metadata':
        raise ResultManifestError(f'exposition omission lacks an input reference: {path}')
    omissions.append({'path': path, 'omittedBytes': len(canonical_json(removed)),
                      'reference': reference, 'reason': 'repeated-record'})


def _bound_sibling_preview(component, coverage, references, omissions):
    siblings = coverage.get('components', [])
    if len(siblings) <= 20:
        return
    selected_id = component.get('componentId')
    retained = _sibling_priorities(siblings, selected_id)[:20]
    retained.extend(i for i in range(len(siblings)) if i not in retained and len(retained) < 20)
    retained.sort()
    coverage['components'] = [{'componentId': siblings[i]['componentId'],
                               'mappingStatus': siblings[i]['mappingStatus']} for i in retained]
    path = '/selectedComponent/claimComponentCoverage/components'
    omissions.append({'path': path, 'omittedRows': len(siblings) - len(retained),
                      'reference': _reference(path, references), 'reason': 'bounded-sibling-preview'})


def _all_references(value):
    found = {}

    def visit(item, path=''):
        if not isinstance(item, dict):
            if isinstance(item, list):
                for index, child in enumerate(item):
                    visit(child, f'{path}/{index}')
            return
        refs = item.get('references')
        if isinstance(refs, dict):
            for suffix, reference in refs.items():
                if isinstance(reference, dict) and 'input' in reference and 'pointer' in reference:
                    found[path + suffix] = reference
        for key, child in item.items():
            if key != 'references':
                visit(child, f'{path}/{_escape(key)}')

    visit(value)
    return found


def _sibling_priorities(siblings, selected_id):
    selected = [i for i, sibling in enumerate(siblings) if sibling.get('componentId') == selected_id]
    unmapped = [i for i, sibling in enumerate(siblings)
                if sibling.get('mappingStatus') == 'unmapped' and i not in selected]
    return selected + unmapped


