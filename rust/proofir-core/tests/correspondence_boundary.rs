use proofir_core::{detached_content_id, validate_envelope, validation_diagnostics};
use serde_json::Value;

// The legacy nine-kind parity corpus remains frozen. These additive kinds
// have Python payload validators, but no Rust payload validator yet.
#[test]
fn correspondence_kinds_are_explicitly_unsupported_in_rust() {
    let vector: Value = serde_json::from_str(include_str!(
        "../../../tests/fixtures/proofir_v3_parity/normalized-row-vector.json"
    ))
    .unwrap();
    for kind in ["proofir.interpretation", "proofir.correspondence"] {
        let mut artifact = vector["artifact"].clone();
        artifact["artifactKind"] = kind.into();
        artifact["artifactId"] = detached_content_id(&artifact).unwrap().into();
        let diagnostics = validation_diagnostics(&artifact);
        assert_eq!(diagnostics.len(), 1, "{kind} must have an explicit boundary");
        assert_eq!(diagnostics[0].code, "unsupported-artifact-kind");
        assert_eq!(diagnostics[0].pointer, "/artifactKind");
        assert!(!diagnostics[0].retained);
        let error = validate_envelope(artifact).err().expect("no Rust payload validator");
        assert!(error.to_string().contains("unsupported artifact kind"));
    }
}
