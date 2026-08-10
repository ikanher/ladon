use proofir_ladon::normalized_rows;
use serde_json::Value;

#[test]
fn normalized_rows_match_shared_fixture_shape() {
    let vector: Value = serde_json::from_str(include_str!(
        "../../../tests/fixtures/proofir_v3_parity/normalized-row-vector.json"
    ))
    .unwrap();
    let rows = normalized_rows(vector["artifact"].clone()).unwrap();
    assert_eq!(rows, vector["normalized"]);
}
