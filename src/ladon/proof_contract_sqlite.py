"""Normalized contract subjects and inputs in the disposable native projection."""

from ladon.proofir_v3 import canonical_bytes

TABLES = frozenset({"proofir_v3_contracts", "proofir_v3_contract_sources",
                    "proofir_v3_contract_analyses", "proofir_v3_contract_analysis_inputs",
                    "proofir_v3_contract_analysis_derivations"})
INDEXES = frozenset({"idx_v3_contract_statement", "idx_v3_contract_source",
                     "idx_v3_contract_analysis_input", "idx_v3_contract_analysis_derivation"})
DELETE_ORDER = ("proofir_v3_contract_analysis_derivations",
                "proofir_v3_contract_analysis_inputs", "proofir_v3_contract_analyses",
                "proofir_v3_contract_sources", "proofir_v3_contracts")
SCHEMA = """
CREATE TABLE IF NOT EXISTS proofir_v3_contracts (
    owner_artifact_id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL,
    profile_digest TEXT NOT NULL CHECK(profile_digest GLOB 'sha256:*'),
    statement_owner TEXT NOT NULL,
    statement_kind TEXT NOT NULL CHECK(statement_kind='statement'),
    statement_local_id TEXT NOT NULL,
    record_json TEXT NOT NULL CHECK(json_valid(record_json)),
    provenance_json TEXT NOT NULL CHECK(json_valid(provenance_json)),
    source_pointer TEXT NOT NULL,
    FOREIGN KEY(owner_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id)
        ON DELETE CASCADE,
    FOREIGN KEY(statement_owner,statement_kind,statement_local_id)
        REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
        DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS proofir_v3_contract_sources (
    owner_artifact_id TEXT NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    source_owner TEXT NOT NULL, source_kind TEXT NOT NULL CHECK(source_kind='source-map'),
    source_local_id TEXT NOT NULL, source_pointer TEXT NOT NULL,
    PRIMARY KEY(owner_artifact_id,ordinal),
    FOREIGN KEY(owner_artifact_id) REFERENCES proofir_v3_contracts(owner_artifact_id)
        ON DELETE CASCADE,
    FOREIGN KEY(source_owner,source_kind,source_local_id)
        REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
        DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS proofir_v3_contract_analyses (
    owner_artifact_id TEXT PRIMARY KEY, analysis_id TEXT NOT NULL,
    profile_digest TEXT NOT NULL CHECK(profile_digest GLOB 'sha256:*'),
    stage TEXT NOT NULL CHECK(stage IN ('comparison','propagation','obligations','probes','rational-branch')),
    result_json TEXT NOT NULL CHECK(json_valid(result_json)), source_pointer TEXT NOT NULL,
    FOREIGN KEY(owner_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id)
        ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proofir_v3_contract_analysis_inputs (
    owner_artifact_id TEXT NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    contract_owner TEXT NOT NULL, contract_kind TEXT NOT NULL CHECK(contract_kind='contract'),
    contract_local_id TEXT NOT NULL, source_pointer TEXT NOT NULL,
    PRIMARY KEY(owner_artifact_id,ordinal),
    FOREIGN KEY(owner_artifact_id) REFERENCES proofir_v3_contract_analyses(owner_artifact_id)
        ON DELETE CASCADE,
    FOREIGN KEY(contract_owner,contract_kind,contract_local_id)
        REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
        DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS proofir_v3_contract_analysis_derivations (
    owner_artifact_id TEXT PRIMARY KEY,
    derivation_owner TEXT NOT NULL,
    goal_kind TEXT NOT NULL CHECK(goal_kind='statement'),
    goal_local_id TEXT NOT NULL, source_pointer TEXT NOT NULL,
    FOREIGN KEY(owner_artifact_id) REFERENCES proofir_v3_contract_analyses(owner_artifact_id)
        ON DELETE CASCADE,
    FOREIGN KEY(derivation_owner,goal_kind,goal_local_id)
        REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
        DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX IF NOT EXISTS idx_v3_contract_analysis_derivation
    ON proofir_v3_contract_analysis_derivations(derivation_owner,goal_kind,goal_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_contract_statement
    ON proofir_v3_contracts(statement_owner,statement_kind,statement_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_contract_source
    ON proofir_v3_contract_sources(source_owner,source_kind,source_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_contract_analysis_input
    ON proofir_v3_contract_analysis_inputs(contract_owner,contract_kind,contract_local_id);
"""


def _reference(ref, owner):
    return ref.get("artifactRef", owner), ref["kind"], ref["localId"]


def reject_obsolete_contract_schema(connection):
    """Fail before projection writes when an older stage constraint is present."""
    from ladon.proofir_sqlite_v3 import _SCHEMA

    name = "proofir_v3_contract_analyses"
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,),
    ).fetchone()
    if row is None:
        return
    definition = _SCHEMA.split("CREATE TABLE IF NOT EXISTS " + name, 1)[1]
    expected = "CREATE TABLE " + name + definition.split(";", 1)[0]
    if " ".join(str(row[0]).split()) != " ".join(expected.split()):
        raise RuntimeError("obsolete contract-analysis schema requires a disposable rebuild")


def _json(value):
    return canonical_bytes(value).decode()


def project_contract(connection, artifact):
    p, owner = artifact["payload"], artifact["artifactId"]
    connection.execute(
        "INSERT INTO proofir_v3_contracts VALUES(?,?,?,?,?,?,?,?,?)",
        (owner, p["contractId"], p["profileDigest"], *_reference(p["statementRef"], owner),
         _json(p["record"]), _json(p["provenance"]), "/payload"),
    )
    for index, ref in enumerate(p["sourceMapRefs"]):
        connection.execute(
            "INSERT INTO proofir_v3_contract_sources VALUES(?,?,?,?,?,?)",
            (owner, index, *_reference(ref, owner), f"/payload/sourceMapRefs/{index}"),
        )


def project_analysis(connection, artifact):
    p, owner = artifact["payload"], artifact["artifactId"]
    connection.execute(
        "INSERT INTO proofir_v3_contract_analyses VALUES(?,?,?,?,?,?)",
        (owner, p["analysisId"], p["profileDigest"], p["stage"], _json(p["result"]), "/payload"),
    )
    for index, ref in enumerate(p["contractRefs"]):
        connection.execute(
            "INSERT INTO proofir_v3_contract_analysis_inputs VALUES(?,?,?,?,?,?)",
            (owner, index, *_reference(ref, owner), f"/payload/contractRefs/{index}"),
        )

    if p["stage"] in {"propagation", "obligations"}:
        connection.execute(
            "INSERT INTO proofir_v3_contract_analysis_derivations VALUES(?,?,?,?,?)",
            (owner, *_reference(p["derivationGoalRef"], owner), "/payload/derivationGoalRef"),
        )
