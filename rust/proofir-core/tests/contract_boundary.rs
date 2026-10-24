use proofir_core::{detached_content_id, validate_envelope, validation_diagnostics};
use serde_json::Value;

#[test]
fn mathematical_contract_kinds_are_explicitly_unsupported() {
    let vector: Value = serde_json::from_str(include_str!(
        "../../../tests/fixtures/proofir_v3_parity/normalized-row-vector.json"
    ))
    .unwrap();
    for kind in ["proofir.contract", "proofir.contract-analysis"] {
        let mut artifact = vector["artifact"].clone();
        artifact["artifactKind"] = kind.into();
        artifact["artifactId"] = detached_content_id(&artifact).unwrap().into();
        let diagnostics = validation_diagnostics(&artifact);
        assert_eq!(diagnostics.len(), 1);
        assert_eq!(diagnostics[0].code, "unsupported-artifact-kind");
        assert_eq!(diagnostics[0].pointer, "/artifactKind");
        assert!(!diagnostics[0].retained);
        assert!(validate_envelope(artifact).is_err());
    }
}
