use proofir_core::canonical_bytes;
use serde_json::{json, Value};

fn payload(count: usize) -> Value {
    let rows: Vec<Value> = (0..count)
        .map(|i| json!({"module": format!("Module{i}"), "digest": format!("sha256:{i:064x}")}))
        .collect();
    json!({
        "prover": {}, "toolchain": {}, "dependencies": [], "compiledModules": rows,
        "options": {}, "trust": {}, "fingerprintScheme": {}
    })
}

#[test]
fn compiled_module_capacity_is_root_scoped_and_finite() {
    for count in [10_001, 10_517, 32_768] {
        let environment = payload(count);
        assert!(canonical_bytes(&environment).is_ok());
        let envelope = json!({"proofirVersion": "3.0", "artifactKind": "proofir.environment",
                              "payload": environment});
        assert!(canonical_bytes(&envelope).is_ok());
    }
    assert!(canonical_bytes(&payload(32_769)).is_err());
    assert!(canonical_bytes(&json!({"unrelated": payload(10_001)})).is_err());
    assert!(canonical_bytes(&json!({"compiledModules": vec![0; 10_001]})).is_err());
    assert!(canonical_bytes(&json!(vec![0; 10_001])).is_err());
}

#[test]
fn environment_exemption_does_not_apply_to_nested_arrays() {
    let mut environment = payload(10_517);
    environment["dependencies"] = json!(vec![0; 10_001]);
    assert!(canonical_bytes(&environment).is_err());
    let envelope = json!({"proofirVersion": "3.0", "artifactKind": "proofir.environment",
                         "payload": payload(10_517),
                         "extensions": {"fixture.scope/v1": payload(10_001)}});
    assert!(canonical_bytes(&envelope).is_err());
}
