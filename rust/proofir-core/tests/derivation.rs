use proofir_core::{validate_derivation, DerivationStep};

#[test]
fn derivation_steps_are_acyclic_and_premises_remain_conjunctive() {
    let steps = vec![
        DerivationStep {
            step_id: "s1".into(),
            premises: vec!["A".into(), "B".into()],
            conclusion: "C".into(),
            rule: "rule".into(),
        },
        DerivationStep {
            step_id: "s2".into(),
            premises: vec!["C".into()],
            conclusion: "D".into(),
            rule: "rule".into(),
        },
    ];
    assert!(validate_derivation(&steps).is_ok());
    let cyclic = vec![DerivationStep {
        step_id: "s".into(),
        premises: vec!["D".into()],
        conclusion: "D".into(),
        rule: "recursive".into(),
    }];
    assert!(validate_derivation(&cyclic).is_err());
}
