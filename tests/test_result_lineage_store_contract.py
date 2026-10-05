"""Validate owner invariants before calling fixed-shape lineage summaries."""
from __future__ import annotations

import sqlite3

import pytest
from test_result_lineage import _inspect, _lineage_fixture

from ladon.result_manifest_io import ResultManifestError


@pytest.mark.parametrize('statement', [
    "UPDATE lineage_edges SET kind='unexpected-kind'",
    "UPDATE lineage_trust SET scope='unexpected-scope'",
    'UPDATE lineage_nodes SET project_owned=12',
    'UPDATE lineage_nodes SET compiler_generated=2',
    'UPDATE lineage_nodes SET unsafe=2',
    "UPDATE lineage_closures SET authority='lexical-only'",
])
def test_malformed_summary_domains_fail_before_owner_promotion(tmp_path, statement):
    manifest, artifacts, companion, db, _inserted = _lineage_fixture(tmp_path)
    with sqlite3.connect(db) as conn:
        conn.execute('PRAGMA ignore_check_constraints=ON')
        conn.execute(statement)
    with pytest.raises(ResultManifestError, match='lineage'):
        _inspect(manifest, artifacts, companion, tmp_path, section='lineage')
