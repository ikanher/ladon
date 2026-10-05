"""Real source compilation, emitted anchors, and stale sibling rejection."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ladon.lean_toolchain import resolve_toolchain_context
from ladon.proofir_v3 import validate_envelope_batch
from ladon.result_manifest_io import content_revision
from ladon.result_resolution import resolve_result_manifest
from ladon.semantic_candidate_worker import SemanticCandidateRequest, check_semantic_candidate
from ladon.semantic_evidence_registry import SemanticEvidenceRegistry

FIXTURE = Path(__file__).parent / 'fixtures/lean_integration'
MANIFEST = Path(__file__).parent / 'fixtures/result_manifest/finite-map.json'


@pytest.mark.skipif(shutil.which('lean') is None, reason='Lean toolchain unavailable')
def test_real_source_capture_resolves_and_rejects_unrebuilt_sibling(tmp_path):
    from ladon.source_association import SourceAssociationRequest, capture_source_association

    repo, source, original, compiled, checked, artifacts, owner, subject, request = _prepare_case(
        tmp_path, SourceAssociationRequest,
    )
    result = capture_source_association(request, artifacts)
    assert result['status'] == 'associated', result
    assert len(result['artifacts']) == 1
    emitted = _assert_registered_capture(result, original, artifacts, tmp_path)
    _assert_resolved_capture(repo, owner, subject, artifacts, emitted)
    original_compiled = compiled.read_bytes()
    source.write_bytes(original.replace(b'sibling : Nat := 1', b'sibling : Nat := 2'))
    stale = capture_source_association(request, artifacts)
    assert stale['status'] == 'stale', stale
    assert stale['artifacts'] == []
    assert compiled.read_bytes() == original_compiled
    assert checked['status'] == 'accepted'


def _assert_registered_capture(result, original, artifacts, tmp_path):
    emitted = result['artifacts'][0]
    anchor = emitted['payload']['anchors'][0]
    assert anchor['contentDigest'] == 'sha256:' + hashlib.sha256(original).hexdigest()
    assert b'theorem target' in original[anchor['start']['byte']:anchor['end']['byte']]
    validate_envelope_batch([*artifacts, emitted])
    registry = SemanticEvidenceRegistry(tmp_path / 'evidence.sqlite')
    registry.register_bundle([*artifacts, emitted])
    assert registry.resolve_artifact(emitted['artifactId']) == emitted
    return emitted


def _assert_resolved_capture(repo, owner, subject, artifacts, emitted):
    anchor = emitted['payload']['anchors'][0]
    manifest = json.loads(MANIFEST.read_text())
    target = manifest['targets'][0]
    target.update(name='Owner.target', typeText=subject['searchShape']['renderedType'],
                  source={'path': 'Owner.lean', 'digest': anchor['contentDigest'],
                          'projectRevision': 'source-capture-fixture'},
                  environment={'digest': owner['environmentRef'],
                               'toolchain': (repo / 'lean-toolchain').read_text().strip()},
                  subjectRef={'artifactId': owner['artifactId'], 'subjectId': subject['localId']})
    target['revision'] = content_revision('target', target)
    manifest['revision'] = content_revision('manifest', manifest)
    resolved = resolve_result_manifest(manifest, [*artifacts, emitted])
    row = next(r for r in resolved['targetResolutions'] if r['targetId'] == target['id'])
    assert row['status'] == 'resolved'
    assert row['checking'] == row['sourceFreshness'] == 'not-assessed'


def _prepare_case(tmp_path, request_type):
    prefix = subprocess.run(['lean', '--print-prefix'], cwd=FIXTURE, capture_output=True,
                            text=True, check=True, timeout=30).stdout.strip()
    lean = Path(prefix) / 'bin/lean'
    repo = tmp_path / 'repository'
    repo.mkdir()
    shutil.copy2(FIXTURE / 'lean-toolchain', repo / 'lean-toolchain')
    source = repo / 'Owner.lean'
    original = ('namespace Owner\n\ndef sibling : Nat := 1\n'
                '/-- Unicode documentation: α 😀. -/\n'
                'theorem target : True := True.intro\nend Owner\n').encode()
    source.write_bytes(original)
    compiled = repo / '.lake/build/lib/lean/Owner.olean'
    compiled.parent.mkdir(parents=True)
    subprocess.run([str(lean), '--root=' + str(repo), '-o', str(compiled), str(source)],
                   cwd=repo, capture_output=True, check=True, timeout=30)
    context = resolve_toolchain_context(repo, lake_path=lean.with_name('lake'), lean_path=lean)
    checked = check_semantic_candidate(SemanticCandidateRequest(
        repo, 'Owner', 'True', 'Owner.target', toolchain=context,
        timeout_seconds=30, max_rss_bytes=4 * 1024**3,
    )).to_dict()
    assert checked['status'] == 'accepted', checked
    artifacts = checked['artifacts']
    owner = next(a for a in artifacts if a['artifactKind'] == 'proofir.check-run')
    subject = next(s for s in owner['subjectRefs'] if s['kind'] == 'declaration')
    request = request_type(
        repo_root=repo, module='Owner', source_path='Owner.lean', candidate='Owner.target',
        subject_artifact_id=owner['artifactId'], toolchain=context,
        timeout_seconds=30, max_rss_bytes=4 * 1024**3,
    )
    return repo, source, original, compiled, checked, artifacts, owner, subject, request
