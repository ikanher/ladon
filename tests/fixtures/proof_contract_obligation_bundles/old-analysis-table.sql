CREATE TABLE proofir_v3_contract_analyses (
    owner_artifact_id TEXT PRIMARY KEY, analysis_id TEXT NOT NULL,
    profile_digest TEXT NOT NULL CHECK(profile_digest GLOB 'sha256:*'),
    stage TEXT NOT NULL CHECK(stage IN ('comparison','propagation')),
    result_json TEXT NOT NULL CHECK(json_valid(result_json)), source_pointer TEXT NOT NULL,
    FOREIGN KEY(owner_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id)
        ON DELETE CASCADE
);
