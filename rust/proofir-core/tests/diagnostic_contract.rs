use proofir_core::{Diagnostic, MAX_DEPTH, MAX_ITEMS, MAX_STRING_BYTES};

#[test]
fn bounded_constants_and_diagnostic_shape_are_shared_contract() {
    assert_eq!(
        (MAX_DEPTH, MAX_ITEMS, MAX_STRING_BYTES),
        (64, 10_000, 1_048_576)
    );
    let row = Diagnostic::new("sha256:test", "decoded", "decode-failed");
    assert_eq!(row.stage, "decoded");
    assert!(!row.retained);
}
