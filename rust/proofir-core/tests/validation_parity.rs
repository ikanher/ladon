use proofir_core::validation_diagnostics;
use serde_json::json;

#[test]
fn invalid_version_uses_shared_diagnostic_vector() {
    let rows =
        validation_diagnostics(&json!({"artifactId": "sha256:invalid", "proofirVersion": "2.0"}));
    assert_eq!(rows.len(), 1);
    assert_eq!(rows[0].artifact_id, "sha256:invalid");
    assert_eq!(rows[0].stage, "envelope-valid");
    assert_eq!(rows[0].code, "unsupported-version");
    assert_eq!(rows[0].pointer, "/proofirVersion");
}
