use proofir_core::{
    parse_coverage, parse_derivation_steps, parse_observation, parse_subject, EnvironmentRef,
};
use serde_json::json;

#[test]
fn typed_records_parse_without_interpreting_lean_terms() {
    let subject = parse_subject(
        &json!({"kind": "statement", "localId": "S"}),
        EnvironmentRef("env".into()),
    )
    .unwrap();
    assert_eq!(subject.local_id, "S");
    assert_eq!(
        parse_coverage(&json!({"population": {"kind": "declarations"}, "queryMatched": 2}))
            .unwrap()
            .observed,
        2
    );
    assert_eq!(
        parse_derivation_steps(&json!([{"stepId": "s", "premises": ["A"], "conclusion": "B"}]))
            .unwrap()
            .len(),
        1
    );
    assert_eq!(parse_observation(&json!({"observationId": "o", "environmentRef": "env", "subjectRef": {"kind": "statement", "localId": "S"}})).unwrap().kind, "unknown");
}
