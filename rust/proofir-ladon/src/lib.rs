//! Small Ladon adapter facade. SQLite and graph queries remain projection concerns.
use proofir_core::{validate_envelope, Artifact, ProofIrError};
use serde_json::{json, Map, Value};
pub fn inspect(value: Value) -> Result<Artifact, ProofIrError> {
    validate_envelope(value)
}

/// Normalize the identity-bearing rows shared with Ladon's Python SQLite
/// projection. Values in Lean-specific payloads remain opaque.
pub fn normalized_rows(value: Value) -> Result<Value, ProofIrError> {
    let artifact = validate_envelope(value)?;
    let envelope = artifact.envelope;
    let object = envelope.as_object().expect("validated envelope object");
    let artifact_id = object["artifactId"].clone();
    let environment = object["environmentRef"].clone();
    let mut subjects = Vec::new();
    if let Some(items) = object["subjectRefs"].as_array() {
        for subject in items {
            let Some(row) = subject.as_object() else {
                continue;
            };
            let Some(kind) = row.get("kind").and_then(Value::as_str) else {
                continue;
            };
            let Some(local_id) = row.get("localId").and_then(Value::as_str) else {
                continue;
            };
            subjects.push(json!({
                "environmentRef": environment,
                "kind": kind,
                "localId": local_id,
                "fingerprint": row.get("fingerprint").cloned().unwrap_or(Value::Null),
                "display": row.get("display").cloned().unwrap_or(Value::Null),
            }));
        }
    }
    let coverage = object["coverage"].as_object();
    let population = coverage
        .and_then(|c| c.get("population"))
        .and_then(Value::as_object);
    let selector = population
        .and_then(|p| p.get("selector"))
        .cloned()
        .unwrap_or_else(|| json!({}));
    let population_kind = population
        .and_then(|p| p.get("kind"))
        .cloned()
        .unwrap_or_else(|| Value::String("unknown".into()));
    let query_matched = coverage
        .and_then(|c| c.get("queryMatched"))
        .and_then(Value::as_i64)
        .unwrap_or(0);
    let extensions = object["extensions"]
        .as_object()
        .map(|extensions| {
            extensions
                .iter()
                .map(|(namespace, payload)| {
                    json!({
                        "contentArtifactId": artifact_id,
                        "namespace": namespace,
                        "payload": payload,
                    })
                })
                .collect::<Vec<_>>()
        })
        .unwrap_or_default();
    let mut result = Map::new();
    result.insert(
        "artifacts".into(),
        json!([{
            "contentArtifactId": artifact_id,
            "artifactKind": object["artifactKind"],
            "proofirVersion": object["proofirVersion"],
            "environmentRef": environment,
        }]),
    );
    result.insert("subjects".into(), Value::Array(subjects));
    result.insert(
        "coverage".into(),
        json!([{
            "contentArtifactId": artifact_id,
            "populationKind": population_kind,
            "selector": selector,
            "queryMatched": query_matched,
        }]),
    );
    result.insert("extensions".into(), Value::Array(extensions));
    Ok(Value::Object(result))
}
