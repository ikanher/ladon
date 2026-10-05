"""Red contract tests for supplied result lineage inspection and cursor binding."""
from __future__ import annotations

import copy
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

import pytest
from test_result_resolution import inputs
from test_theorem_lineage_store import _test_identity, sample_plan

from ladon.proof_search_schema import create_proof_search_schema
from ladon.result_inspection import inspect_result_manifest
from ladon.result_manifest_io import ResultManifestError
from ladon.theorem_lineage_store import LineageIdentity, ingest_theorem_lineage


def _lineage_fixture(tmp_path: Path, *, identity: LineageIdentity | None = None):
    db = tmp_path / 'lineage.sqlite3'
    conn = sqlite3.connect(db)
    conn.execute('PRAGMA foreign_keys = ON')
    create_proof_search_schema(conn)
    identity = identity or _test_identity()
    plan = sample_plan()
    # Keep the fixture target identical to the result-manifest target, which
    # lets canonical resolution and lineage inspection both exercise a current
    # target mapping.
    def rename(value):
        if isinstance(value, dict):
            return {key: rename(child) for key, child in value.items()}
        if isinstance(value, list):
            return [rename(child) for child in value]
        return 'Demo.proof' if value == 'Demo.target' else value
    inserted = ingest_theorem_lineage(conn, rename(plan), identity)
    conn.close()
    manifest, artifacts = inputs()
    target = manifest['targets'][0]
    from ladon.result_manifest_io import content_revision
    target['revision'] = content_revision('target', target)
    manifest['revision'] = content_revision('manifest', manifest)
    companion = {
        'schema': 'ladon-result-lineage-inputs-v1', 'resultId': manifest['resultId'],
        'manifestRevision': manifest['revision'],
        'entries': [{'id': 'lineage-demo', 'targetId': target['id'],
                     'targetRevision': target['revision'], 'database': db.name,
                     'closureId': inserted['closureId'], 'identity': asdict(identity)}],
    }
    return manifest, artifacts, companion, db, inserted


def _inspect(manifest, artifacts, companion, tmp_path, **kwargs):
    return inspect_result_manifest(manifest, artifacts, lineage_inputs=companion,
                                   lineage_base=tmp_path, **kwargs)


def test_inspection_distinguishes_identity_staleness_from_missing_lineage(tmp_path):
    manifest, artifacts, companion, _db, _inserted = _lineage_fixture(tmp_path)
    target_id = manifest['targets'][0]['id']
    fresh = _inspect(manifest, artifacts, companion, tmp_path, section='lineage', target_id=target_id)
    row = fresh['rows'][0]
    assert row['status'] == 'available'
    assert row['ownerSummary']['freshness'] == 'fresh'
    assert row['targetId'] == target_id
    assert row['associationBasis'] == 'producer-selected'
    assert row['sourceFreshness'] == 'not-assessed'
    assert row['environmentBinding'] == 'not-established'
    assert row['selectionCurrency'] == 'current'



def test_inspection_reports_stale_and_missing_lineage(tmp_path):
    manifest, artifacts, companion, _db, _inserted = _lineage_fixture(tmp_path)
    target_id = manifest['targets'][0]['id']
    stale = copy.deepcopy(companion)
    stale['entries'][0]['identity']['source_fingerprint'] = 'different-source'
    stale_result = _inspect(manifest, artifacts, stale, tmp_path, section='lineage', target_id=target_id)
    assert stale_result['rows'][0]['status'] == 'unavailable'
    assert stale_result['rows'][0]['reason'] == 'stale-source'

    missing = copy.deepcopy(companion)
    missing['entries'][0]['database'] = 'absent.sqlite3'
    missing_result = _inspect(manifest, artifacts, missing, tmp_path, section='lineage', target_id=target_id)
    assert missing_result['rows'][0]['status'] == 'unavailable'
    assert missing_result['rows'][0]['reason'] == 'database-unavailable'


def test_companion_is_fully_validated_before_selector_and_cli_paths_are_relative(tmp_path, capsys):
    manifest, artifacts, companion, db, _inserted = _lineage_fixture(tmp_path)
    malformed = copy.deepcopy(companion)
    malformed['entries'][0]['identity'].pop('helper_identity')
    with pytest.raises(ResultManifestError):
        _inspect(manifest, artifacts, malformed, tmp_path, section='lineage')

    elsewhere = tmp_path / 'inputs'
    elsewhere.mkdir()
    companion_path = elsewhere / 'lineage.json'
    companion_path.write_text(json.dumps(companion))
    manifest_path = elsewhere / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest))
    artifact_args = []
    for index, artifact in enumerate(artifacts):
        artifact_path = elsewhere / f'artifact-{index}.json'
        artifact_path.write_text(json.dumps(artifact))
        artifact_args.extend(['--artifact', str(artifact_path)])
    companion['entries'][0]['database'] = '../lineage.sqlite3'
    companion_path.write_text(json.dumps(companion))
    from ladon.entrypoint import main
    assert main(['result', 'inspect', str(manifest_path), *artifact_args,
                 '--lineage-inputs', str(companion_path), '--section', 'lineage',
                 '--target', manifest['targets'][0]['id']]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output['rows'][0]['status'] == 'available'
    assert db.exists()


def test_assumptions_keep_trust_categories_separate_and_unknown_inventory_unproven(tmp_path):
    manifest, artifacts, companion, _db, _inserted = _lineage_fixture(tmp_path)
    result = _inspect(manifest, artifacts, companion, tmp_path, section='assumptions',
                      target_id=manifest['targets'][0]['id'], limit=100)
    axioms = [row for row in result['rows'] if row.get('kind') == 'observed-axioms']
    assert any(row['status'] == 'observed' and row['observation']['kind'] == 'axiom_reference'
               and row['authority'] == 'lean_environment' and row['coverage'] == 'partial'
               and row['total'] is None for row in axioms)
    unavailable = {row['kind']: row for row in result['rows'] if row['status'] == 'unavailable'}
    assert unavailable['theorem-hypotheses']['coverage'] == 'unknown'
    assert any(row.get('observation', {}).get('external_frontier') is True for row in result['rows'])


def test_lineage_cursor_binds_database_bytes_and_companion(tmp_path):
    manifest, artifacts, companion, db, _inserted = _lineage_fixture(tmp_path)
    first = _inspect(manifest, artifacts, companion, tmp_path, section='assumptions', limit=1)
    cursor = first['pagination']['nextCursor']
    assert cursor
    with sqlite3.connect(db) as conn:
        conn.execute("DELETE FROM lineage_trust")
    with pytest.raises(ResultManifestError, match='cursor'):
        _inspect(manifest, artifacts, companion, tmp_path, section='assumptions', limit=1, cursor=cursor)
    changed_companion = copy.deepcopy(companion)
    changed_companion['entries'][0]['identity']['configuration_fingerprint'] = 'other'
    with pytest.raises(ResultManifestError, match='cursor'):
        _inspect(manifest, artifacts, changed_companion, tmp_path, section='assumptions', limit=1, cursor=cursor)


def test_inspection_reads_lineage_store_without_writes_or_external_activity(monkeypatch, tmp_path):
    import socket
    import subprocess
    manifest, artifacts, companion, db, _inserted = _lineage_fixture(tmp_path)
    before = db.read_bytes()
    def forbidden(*_args, **_kwargs):
        raise AssertionError('inspection attempted subprocess or network activity')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(socket, 'socket', forbidden)
    result = _inspect(manifest, artifacts, companion, tmp_path, section='lineage')
    assert result['rows']
    assert db.read_bytes() == before
