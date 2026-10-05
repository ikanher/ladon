"""Result dossier joins reuse exact canonical subject ownership."""
from __future__ import annotations

import json

from test_result_resolution import inputs, seal

from ladon.result_inspection import inspect_result_manifest
from ladon.result_inspection_page import text_projection


def test_evidence_section_retains_exact_declaration_owner_and_unknown_coverage():
    manifest, artifacts = inputs()
    result = inspect_result_manifest(manifest, artifacts, section='evidence')
    row = result['rows'][0]
    assert row['status'] == 'available'
    assert row['evidence']['subjects']['rows'][0]['ownerArtifactId'] == artifacts[1]['artifactId']
    assert row['evidence']['subjects']['rows'][0]['kind'] == 'declaration'
    assert row['evidence']['coverage']['applicability'] == 'unavailable'
    assert row['resolution']['status'] == 'resolved'
    assert result['coverage']['proofCoverage'] == 'unknown'
    assert len(text_projection(result).encode()) < 32768
    assert len(json.dumps(result).encode()) < 32768


def test_unresolved_target_cannot_attach_same_name_dossier():
    manifest, artifacts = inputs()
    manifest['targets'][0]['source']['digest'] = 'sha256:' + '0' * 64
    seal(manifest)
    row = inspect_result_manifest(manifest, artifacts, section='evidence')['rows'][0]
    assert row['status'] == 'unavailable'
    assert row['resolution']['status'] == 'stale'
    assert 'evidence' not in row
