"""Bundled views prepare their complete dossier once per request."""
from __future__ import annotations

import json

import pytest
from test_result_bundle_views import _fixture

from ladon.entrypoint import main


@pytest.mark.parametrize('operation', ['inspect', 'guide'])
def test_bundle_view_prepares_once_and_matches_explicit_view(tmp_path, capsys, monkeypatch, operation):
    from ladon import result_bundle_inputs, result_dossier, result_guides, result_inspection
    from ladon.result_bundles import export_result_bundle, open_result_bundle

    manifest_path, selection, _, _ = _fixture(tmp_path)
    bundle = tmp_path / 'result.zip'
    export_result_bundle(manifest_path, selection, bundle)

    calls = []
    prepare = result_dossier.prepare_dossier

    def counted_prepare(*args, **kwargs):
        calls.append(kwargs.get('target_ids'))
        return prepare(*args, **kwargs)

    monkeypatch.setattr(result_bundle_inputs, 'prepare_dossier', counted_prepare)
    monkeypatch.setattr(result_inspection, 'prepare_dossier', counted_prepare)
    monkeypatch.setattr(result_guides, 'prepare_dossier', counted_prepare)

    args = ['result', operation, str(bundle), '--section', 'assumptions', '--limit', '1']
    code = main(args)
    output = capsys.readouterr()
    assert code == 0, output.err
    bundled_view = json.loads(output.out)
    bundle_call_count = len(calls)
    calls.clear()

    # The ordinary manifest view remains the output contract for selected rows.
    with open_result_bundle(bundle) as inputs:
        options = {
            'section': 'assumptions', 'limit': 1,
            'lineage_inputs': inputs.lineage,
            'lineage_base': inputs.root,
            'lineage_reference_base': 'bundle:' + inputs.identity,
            'bundle_identity': inputs.identity,
        }
        if operation == 'guide':
            from ladon.result_guides import guide_result_manifest
            expected = guide_result_manifest(
                inputs.manifest, inputs.artifacts, guide_inputs=inputs.guide,
                assessments=inputs.assessments, **options)
        else:
            from ladon.result_inspection import inspect_result_manifest
            expected = inspect_result_manifest(
                inputs.manifest, inputs.artifacts, assessments=inputs.assessments,
                **options)
    assert bundled_view == expected
    assert bundle_call_count == 1


def _checking_bundle(tmp_path):
    from test_result_bundle_views import _entry, _write
    from test_result_checking import check_inputs, manifest, target_owned_by_check

    from ladon.result_bundles import export_result_bundle

    value = manifest()
    artifacts = check_inputs('selected')
    target_owned_by_check(value, artifacts)
    other = check_inputs('unselected', candidate='Unrelated.theorem')
    artifacts.extend(other)
    paths = [_write(tmp_path / f'check-{number}.json', row)
             for number, row in enumerate(artifacts)]
    entries = [_entry(f'check-{number}', 'artifact', path)
               for number, path in enumerate(paths)]
    selection = {'schema': 'ladon-result-bundle-selection-v1',
                 'supplier': {'identity': 'test-supplier', 'kind': 'tool'},
                 'entries': entries, 'lineageBindings': [],
                 'identifiers': [], 'externalDependencies': []}
    bundle = tmp_path / 'checks.zip'
    export_result_bundle(_write(tmp_path / 'manifest.json', value),
                         _write(tmp_path / 'selection.json', selection), bundle)
    return bundle, value, artifacts


@pytest.mark.parametrize('operation', ['inspect', 'guide'])
def test_selected_bundle_checking_matches_explicit_owner(tmp_path, capsys, operation):
    from ladon.result_bundles import open_result_bundle
    from ladon.result_guides import guide_result_manifest
    from ladon.result_inspection import inspect_result_manifest

    bundle, value, _ = _checking_bundle(tmp_path)
    target_id = value['targets'][0]['id']
    code = main(['result', operation, str(bundle), '--section', 'checking',
                 '--target', target_id])
    output = capsys.readouterr()
    assert code == 0, output.err
    result = json.loads(output.out)
    with open_result_bundle(bundle) as inputs:
        options = {'section': 'checking', 'target_id': target_id,
                   'assessments': inputs.assessments, 'lineage_inputs': inputs.lineage,
                   'lineage_base': inputs.root,
                   'lineage_reference_base': 'bundle:' + inputs.identity,
                   'bundle_identity': inputs.identity}
        if operation == 'guide':
            expected = guide_result_manifest(inputs.manifest, inputs.artifacts,
                                             guide_inputs=inputs.guide, **options)
        else:
            expected = inspect_result_manifest(inputs.manifest, inputs.artifacts, **options)
    assert result == expected
    assert result['rows']
    assert all(binding['targetId'] == target_id
               for row in result['rows'] for binding in row['targetBindings'])


@pytest.mark.parametrize('operation', ['inspect', 'guide'])
def test_bundle_view_rejects_invalid_unselected_check(tmp_path, capsys, monkeypatch, operation):
    from ladon import result_bundle_inputs
    from ladon.proofir_v3 import detached_content_id

    bundle, value, artifacts = _checking_bundle(tmp_path)
    invalid = artifacts[-1]
    invalid['extensions']['ladon.process-observation/v1']['evidenceReceipt']['checkRunRef'] = 'check:wrong-owner'
    invalid['artifactId'] = detached_content_id(invalid)
    # Inject at the artifact owner boundary after archive integrity has passed.
    # The invalid receipt belongs to an unrelated target outside this selection.
    monkeypatch.setattr(result_bundle_inputs, 'load_result_artifacts', lambda _paths: artifacts)
    code = main(['result', operation, str(bundle), '--section', 'checking',
                 '--target', value['targets'][0]['id']])
    output = capsys.readouterr()
    assert code == 2
    assert not output.out
    assert 'receipt' in output.err or 'owner' in output.err
