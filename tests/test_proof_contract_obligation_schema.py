"""Disposable native projections reject stale stage constraints before mutation."""
import sqlite3
from pathlib import Path

import pytest
from test_proof_contract_obligation_bundles import _request

from ladon.proofir_sqlite_v3 import V3_SCHEMA_VERSION, create_v3_schema, project_envelopes

OLD_TABLE = Path(__file__).parent / 'fixtures/proof_contract_obligation_bundles/old-analysis-table.sql'


def test_new_native_schema_admits_obligations_stage():
    connection = sqlite3.connect(':memory:')
    create_v3_schema(connection)
    sql = connection.execute("SELECT sql FROM sqlite_master WHERE name=?",
                              ('proofir_v3_contract_analyses',)).fetchone()[0]
    assert "'obligations'" in sql


def test_old_projection_version_requires_explicit_rebuild():
    connection = sqlite3.connect(':memory:')
    create_v3_schema(connection)
    connection.execute('PRAGMA user_version = 11')
    with pytest.raises(RuntimeError, match='rebuild'):
        create_v3_schema(connection)


@pytest.mark.parametrize('manage_version', [True, False])
def test_old_stage_constraint_is_rejected_even_if_version_is_relabelled(manage_version):
    _, request = _request()
    inputs = [request.derivation_artifact, *request.contract_artifacts]
    connection = sqlite3.connect(':memory:')
    project_envelopes(connection, inputs)
    before = connection.execute('SELECT * FROM proofir_v3_contracts').fetchall()
    connection.execute('DROP TABLE proofir_v3_contract_analyses')
    connection.executescript(OLD_TABLE.read_text())
    connection.execute(f'PRAGMA user_version = {V3_SCHEMA_VERSION}')
    with pytest.raises(RuntimeError, match='rebuild'):
        project_envelopes(connection, inputs, manage_user_version=manage_version)
    assert connection.execute('SELECT * FROM proofir_v3_contracts').fetchall() == before
