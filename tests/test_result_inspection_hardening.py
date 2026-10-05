"""Field and audit regressions for dossier inspection."""
import copy

import pytest
from test_result_assessments import assessment, companion, manifest
from test_result_checking import check_inputs

from ladon.result_assessments import validate_result_assessments
from ladon.result_inspection import inspect_result_manifest
from ladon.result_manifest_io import ResultManifestError, canonical_json, content_revision


def test_field_author_attribution_is_retained_verbatim():
    value = manifest()
    row = assessment(value['claims'][0], 'unrestricted-domain')
    row['author']['id'] = 'OpenAI Codex, implementation agent'
    data = companion(value, [row])
    assert validate_result_assessments(data, value)['assessments'][0]['author'] == row['author']


def test_companion_utf8_bytes_are_bounded_beyond_schema_character_count():
    value = manifest()
    row = assessment(value['claims'][0], 'unrestricted-domain')
    row['scope'] = 'λ' * 32769
    with pytest.raises(ResultManifestError, match='UTF-8'):
        validate_result_assessments(companion(value, [row]), value)


def test_long_inventory_scope_remains_inspectable_with_exact_reference():
    value = manifest()
    value['claimInventory']['scope'] = 'x' * 4096
    value['revision'] = content_revision('manifest', value)
    result = inspect_result_manifest(value, [])
    assert len(canonical_json(result)) < 32768
    assert '/claimInventory/scope' in str(result['fieldOmissions'])


def test_nonchecking_view_validates_receipts_without_constructing_check_cards(monkeypatch):
    import ladon.result_inspection_checks as checks

    def forbidden(*_args, **_kwargs):
        raise AssertionError('unselected check card was constructed')
    monkeypatch.setattr(checks, '_check_card', forbidden)
    result = inspect_result_manifest(manifest(), check_inputs(), section='claims')
    assert len(result['rows']) == 1


def test_checking_builds_only_requested_page(monkeypatch):
    import ladon.result_inspection_checks as checks

    artifacts = []
    for index in range(20):
        batch = check_inputs(str(index))
        artifacts.extend(batch if not artifacts else [batch[1]])
    original = checks._check_card
    calls = []
    def record(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(checks, '_check_card', record)
    page = inspect_result_manifest(manifest(), artifacts, section='checking', limit=1)
    assert page['pagination']['total'] == 20
    assert len(calls) == 1


def test_cursor_binds_supplied_artifact_population():
    value = manifest()
    page = inspect_result_manifest(value, [], limit=1)
    with pytest.raises(ResultManifestError):
        inspect_result_manifest(copy.deepcopy(value), check_inputs(), limit=1,
                                cursor=page['pagination']['nextCursor'])
