"""Current projections remain reopenable and retain exact schema constraints."""
import sqlite3

import pytest
from support.proofir_v3_native import native_artifacts

from ladon.proofir_sqlite_v3 import create_v3_schema, project_envelopes


@pytest.mark.parametrize('manage_version', [True, False])
def test_current_augmented_schema_can_reopen_and_reproject(manage_version):
    connection = sqlite3.connect(':memory:')
    create_v3_schema(connection, manage_user_version=manage_version)
    create_v3_schema(connection, manage_user_version=manage_version)
    artifact = native_artifacts()['proofir.claim']
    project_envelopes(connection, [artifact], manage_user_version=manage_version)
    project_envelopes(connection, [artifact], manage_user_version=manage_version)
    sql = connection.execute("SELECT sql FROM sqlite_master WHERE name=?",
                             ('proofir_v3_contract_analyses',)).fetchone()[0]
    assert "'obligations'" in sql
    assert "CHECK(source_pointer=" in sql
