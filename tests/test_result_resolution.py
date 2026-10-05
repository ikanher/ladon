"""Exact stored targets cannot borrow evidence from matching names or other owners."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from support.proofir_v3_native import envelope, environment_artifact

from ladon.proofir_v3 import detached_content_id
from ladon.result_manifest_io import ResultManifestError, content_revision
from ladon.result_resolution import resolve_result_manifest

FIXTURE = Path(__file__).parent / 'fixtures/result_manifest/finite-map.json'


def inputs():
    manifest = json.loads(FIXTURE.read_text())
    environment = environment_artifact()
    environment['payload']['options'] = {'autoImplicit': 'false'}
    environment['environmentRef'] = 'sha256:' + hashlib.sha256(json.dumps(environment['payload'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    environment['artifactId'] = detached_content_id(environment)
    name = 'Demo.proof'
    structural = 'Lean.Expr.const `True []'
    identity = 'sha256:' + hashlib.sha256(json.dumps({'qualifiedName': name, 'type': structural}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    subject = {'kind': 'declaration', 'localId': 'declaration:' + identity, 'display': name,
               'fingerprint': {'scheme': {'name': 'lean-declaration-identity', 'version': '1'}, 'digest': identity},
               'searchShape': {'renderedType': 'True', 'typeStructural': structural,
                               'typeStatus': 'lean-rendered', 'typeTextTruncated': False}}
    source = envelope('proofir.source-map', {'sourceMapId': 'source-map:target', 'anchors': [{
        'subjectRef': {'kind': 'declaration', 'localId': subject['localId']},
        'sourcePath': 'Demo.lean', 'module': 'Demo', 'declName': name,
        'start': {'byte': 0, 'line': 1, 'column': 1}, 'end': {'byte': 30, 'line': 1, 'column': 31},
        'contentDigest': 'sha256:' + 'c' * 64, 'matchMethod': 'environment-fingerprint',
        'declarationFingerprint': identity}], 'policy': {'version': '1', 'digest': 'sha256:' + '5' * 64}},
        [subject], environment=environment['environmentRef'])
    target = manifest['targets'][0]
    target.update(name=name, typeText='True', source={'path': 'Demo.lean', 'digest': 'sha256:' + 'c' * 64, 'projectRevision': 'declared-archive-r05'},
                  environment={'toolchain': 'leanprover/lean4:v4.20.0', 'digest': environment['environmentRef']},
                  subjectRef={'artifactId': source['artifactId'], 'subjectId': subject['localId']})
    seal(manifest)
    return manifest, [environment, source]


def seal(manifest):
    for target in manifest['targets']: target['revision'] = content_revision('target', target)
    manifest['revision'] = content_revision('manifest', manifest)


def reseal_source(manifest, artifacts):
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    manifest['targets'][0]['subjectRef']['artifactId'] = artifacts[1]['artifactId']
    seal(manifest)


def test_exact_stored_target_resolves_without_claim_or_checker_promotion():
    manifest, artifacts = inputs()
    result = resolve_result_manifest(manifest, artifacts)
    row = result['targetResolutions'][0]
    assert row['status'] == 'resolved'
    assert row['sourceFreshness'] == 'not-assessed'
    assert row['checking'] == 'not-assessed'
    assert row['projectRevisionBasis'] == 'producer-declared'
    assert result['linkResolutions'][0]['status'] == 'resolved'
    assert result['reviewSummary']['historical'] == 1


@pytest.mark.parametrize('mutation,expected', [
    ('no-subject', 'unresolved'), ('missing-artifact', 'unresolved'),
    ('missing-environment', 'unresolved'), ('wrong-subject', 'unresolved'),
    ('wrong-name', 'unresolved'), ('wrong-type', 'stale'), ('wrong-environment', 'stale'),
    ('wrong-toolchain', 'stale'), ('wrong-path', 'stale'), ('wrong-digest', 'stale'),
    ('no-anchor', 'unresolved'), ('duplicate-anchor', 'ambiguous'),
    ('weak-anchor', 'unresolved'), ('wrong-fingerprint', 'unresolved'),
])
def test_missing_ambiguous_and_stale_bindings_remain_visible(mutation, expected):
    manifest, artifacts = inputs()
    target = manifest['targets'][0]
    anchor = artifacts[1]['payload']['anchors'][0]
    actions = {
        'no-subject': lambda: target.pop('subjectRef'),
        'missing-artifact': lambda: target['subjectRef'].update(artifactId='sha256:' + '0' * 64),
        'missing-environment': lambda: artifacts.pop(0),
        'wrong-subject': lambda: target['subjectRef'].update(subjectId='declaration:missing'),
        'wrong-name': lambda: target.update(name='Demo.missing'),
        'wrong-type': lambda: target.update(typeText='False'),
        'wrong-environment': lambda: target['environment'].update(digest='sha256:' + '0' * 64),
        'wrong-toolchain': lambda: target['environment'].update(toolchain='leanprover/lean4:v4.19.0'),
        'wrong-path': lambda: target['source'].update(path='Other.lean'),
        'wrong-digest': lambda: target['source'].update(digest='sha256:' + '0' * 64),
        'no-anchor': lambda: artifacts[1]['payload'].update(anchors=[]),
        'duplicate-anchor': lambda: artifacts[1]['payload']['anchors'].append(copy.deepcopy(anchor)),
        'weak-anchor': lambda: anchor.update(matchMethod='name-only-diagnostic'),
        'wrong-fingerprint': lambda: anchor.update(declarationFingerprint='sha256:' + '0' * 64),
    }
    actions[mutation]()
    if mutation in {'no-anchor', 'duplicate-anchor', 'weak-anchor', 'wrong-fingerprint'}: reseal_source(manifest, artifacts)
    seal(manifest)
    result = resolve_result_manifest(manifest, artifacts)
    assert result['targetResolutions'][0]['status'] == expected
    assert result['linkResolutions'][0]['status'] == expected
    assert result['targetResolutions'][0]['checking'] == 'not-assessed'


def test_structural_type_forgery_is_not_exact_resolution():
    manifest, artifacts = inputs()
    artifacts[1]['subjectRefs'][0]['searchShape']['typeStructural'] = 'Lean.Expr.const `False []'
    reseal_source(manifest, artifacts)
    result = resolve_result_manifest(manifest, artifacts)
    assert result['targetResolutions'][0]['status'] == 'unresolved'


def test_invalid_supplied_artifact_fails_before_resolution():
    manifest, artifacts = inputs()
    artifacts[1]['payload']['anchors'][0]['contentDigest'] = 'tampered'
    with pytest.raises(ResultManifestError, match='canonical'):
        resolve_result_manifest(manifest, artifacts)


def test_frozen_exposition_baseline_remains_unresolved_without_canonical_subjects():
    path = Path(__file__).parents[1] / 'openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/fixed-epoch-v1/manifest.json'
    result = resolve_result_manifest(json.loads(path.read_text()), [])
    assert result['canonicalResolution']['statuses'] == {'unresolved': 20}
    assert all(row['status'] == 'unresolved' for row in result['targetResolutions'])


def write_inputs(tmp_path):
    manifest, artifacts = inputs()
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest))
    argv = ['result', 'resolve', str(path)]
    for index, artifact in enumerate(artifacts):
        file = tmp_path / f'artifact-{index}.json'
        file.write_text(json.dumps(artifact))
        argv.extend(['--artifact', str(file)])
    return argv


def test_resolution_cli_is_offline_and_text_matches_json(monkeypatch, tmp_path, capsys):
    import socket
    import subprocess

    from ladon.entrypoint import main

    def forbidden(*_args, **_kwargs):
        raise AssertionError('canonical resolution attempted external activity')

    argv = write_inputs(tmp_path)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(socket, 'socket', forbidden)
    assert main(argv) == 0
    captured = capsys.readouterr()
    assert not captured.err
    result = json.loads(captured.out)
    assert result['targetResolutions'][0]['status'] == 'resolved'
    assert main(argv + ['--format', 'text']) == 0
    decoded = {k: json.loads(v) for k, v in (line.split(': ', 1) for line in capsys.readouterr().out.splitlines())}
    assert decoded == result


def test_unknown_target_and_invalid_evidence_have_no_success_output(tmp_path, capsys):
    from ladon.entrypoint import main

    argv = write_inputs(tmp_path)
    assert main(argv + ['--target', 'missing']) == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert json.loads(captured.err)['operation'] == 'resolve'
    (tmp_path / 'artifact-1.json').write_text('{"artifactId":"a","artifactId":"b"}')
    assert main(argv) == 2
    assert not capsys.readouterr().out


def test_resolution_ordinary_console_outside_checkout(tmp_path):
    import os
    import subprocess
    import sys

    console = os.environ.get('LADON_CONSOLE', str(Path(sys.executable).with_name('ladon')))
    result = subprocess.run([console, *write_inputs(tmp_path)], cwd=tmp_path,
                            capture_output=True, text=True, check=False, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['targetResolutions'][0]['status'] == 'resolved'


def test_projection_omissions_do_not_skip_population_validation():
    manifest, artifacts = inputs()
    original = manifest['targets'][0]
    manifest['targets'] = [{**copy.deepcopy(original), 'id': f'target-{i}'} for i in range(125)]
    manifest['links'][0]['targetIds'] = ['target-0']
    manifest['reviews'] = []
    seal(manifest)
    result = resolve_result_manifest(manifest, artifacts)
    assert result['canonicalResolution']['statuses'] == {'resolved': 125}
    assert result['omissions']['targetResolutions'] > 0
    assert len(json.dumps(result, separators=(',', ':'), ensure_ascii=False).encode()) < 32 * 1024
    focused = resolve_result_manifest(manifest, artifacts, target_id='target-124')
    assert focused['targetResolutions'][0]['targetId'] == 'target-124'
    assert focused['canonicalResolution']['statuses'] == {'resolved': 125}
    artifacts[1]['payload']['anchors'][0]['sourcePath'] = '../escape.lean'
    with pytest.raises(ResultManifestError, match='canonical'):
        resolve_result_manifest(manifest, artifacts, target_id='target-124')


def test_source_anchor_does_not_cross_artifact_owner_by_local_id():
    manifest, artifacts = inputs()
    other = copy.deepcopy(artifacts[1])
    other['payload']['sourceMapId'] = 'source-map:other-owner'
    other['artifactId'] = detached_content_id(other)
    artifacts[1]['payload']['anchors'] = []
    reseal_source(manifest, artifacts)
    artifacts.append(other)
    result = resolve_result_manifest(manifest, artifacts)
    assert result['targetResolutions'][0]['reason'] == 'canonical-source-anchor-unavailable'


def test_qualified_anchor_can_bind_another_exact_artifact_owner():
    manifest, artifacts = inputs()
    owner = artifacts[1]
    source = copy.deepcopy(owner)
    owner['payload']['anchors'] = []
    reseal_source(manifest, artifacts)
    source['payload']['sourceMapId'] = 'source-map:qualified-owner'
    source['payload']['anchors'][0]['subjectRef']['artifactRef'] = owner['artifactId']
    source['artifactId'] = detached_content_id(source)
    artifacts.append(source)
    result = resolve_result_manifest(manifest, artifacts)
    assert result['targetResolutions'][0]['status'] == 'resolved'
    assert result['targetResolutions'][0]['sourceAnchor']['artifactId'] == source['artifactId']


@pytest.mark.parametrize('field,value', [('declName', 'Other.proof'), ('declarationRef', 'declaration:other')])
def test_contradictory_anchor_metadata_cannot_resolve(field, value):
    manifest, artifacts = inputs()
    artifacts[1]['payload']['anchors'][0][field] = value
    reseal_source(manifest, artifacts)
    assert resolve_result_manifest(manifest, artifacts)['targetResolutions'][0]['status'] == 'unresolved'


def test_evidence_file_limits_and_nonregular_inputs(tmp_path):
    import os

    from ladon.proofir_v3 import MAX_ARTIFACT_BYTES
    from ladon.result_evidence_io import load_result_artifacts

    path = tmp_path / 'oversized.json'
    with path.open('wb') as file: file.truncate(MAX_ARTIFACT_BYTES + 1)
    with pytest.raises(ResultManifestError, match='input limit'):
        load_result_artifacts([path])
    if hasattr(os, 'mkfifo'):
        fifo = tmp_path / 'input.fifo'
        os.mkfifo(fifo)
        with pytest.raises(ResultManifestError, match='regular file'):
            load_result_artifacts([fifo])


def test_multiple_environment_owners_are_ambiguous():
    manifest, artifacts = inputs()
    other = copy.deepcopy(artifacts[0])
    other['producer']['version'] = 'another-producer-version'
    other['artifactId'] = detached_content_id(other)
    artifacts.append(other)
    assert resolve_result_manifest(manifest, artifacts)['targetResolutions'][0]['status'] == 'ambiguous'


def test_nonexistent_name_stays_unresolved_even_with_matching_type_and_environment():
    manifest, artifacts = inputs()
    manifest['targets'][0]['name'] = 'Demo.thereIsNoSuchTheorem'
    seal(manifest)
    result = resolve_result_manifest(manifest, artifacts)
    assert result['targetResolutions'][0]['status'] == 'unresolved'
    assert result['canonicalResolution']['statuses'] == {'unresolved': 1}
