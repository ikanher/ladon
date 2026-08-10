//! Prover-neutral ProofIR v3 identity types. Lean terms remain opaque.

use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

pub const VERSION: &str = "3.0";
pub const MAX_DEPTH: usize = 64;
pub const MAX_ITEMS: usize = 10_000;
pub const MAX_STRING_BYTES: usize = 1_048_576;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Artifact {
    pub envelope: Value,
    pub content_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProofIrError(pub String);

/// Environment-scoped identity supplied by a prover worker.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EnvironmentRef(pub String);

/// Opaque subject identity; Rust never parses the prover's term language.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SubjectRef {
    pub environment: EnvironmentRef,
    pub kind: String,
    pub local_id: String,
    pub fingerprint: Option<String>,
}

/// Stable validation/omission observation shared with the Python vocabulary.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Diagnostic {
    pub artifact_id: String,
    pub stage: String,
    pub code: String,
    pub pointer: String,
    pub retained: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Observation {
    pub observation_id: String,
    pub subject: SubjectRef,
    pub kind: String,
    pub result: String,
    pub authority_basis: String,
    pub guarantee_scope: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Coverage {
    pub population_kind: String,
    pub expected: Option<u64>,
    pub observed: u64,
    pub omissions: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DerivationStep {
    pub step_id: String,
    pub premises: Vec<String>,
    pub conclusion: String,
    pub rule: String,
}

pub fn parse_subject(
    value: &Value,
    environment: EnvironmentRef,
) -> Result<SubjectRef, ProofIrError> {
    let object = value
        .as_object()
        .ok_or_else(|| ProofIrError("subject reference must be an object".into()))?;
    let kind = object
        .get("kind")
        .and_then(Value::as_str)
        .filter(|v| !v.is_empty())
        .ok_or_else(|| ProofIrError("subject kind is required".into()))?;
    let local_id = object
        .get("localId")
        .and_then(Value::as_str)
        .filter(|v| !v.is_empty())
        .ok_or_else(|| ProofIrError("subject localId is required".into()))?;
    Ok(SubjectRef {
        environment,
        kind: kind.into(),
        local_id: local_id.into(),
        fingerprint: object
            .get("fingerprint")
            .and_then(Value::as_str)
            .map(str::to_owned),
    })
}

pub fn parse_coverage(value: &Value) -> Result<Coverage, ProofIrError> {
    let object = value
        .as_object()
        .ok_or_else(|| ProofIrError("coverage must be an object".into()))?;
    let population = object
        .get("population")
        .and_then(Value::as_object)
        .ok_or_else(|| ProofIrError("coverage population is required".into()))?;
    let kind = population
        .get("kind")
        .and_then(Value::as_str)
        .filter(|v| !v.is_empty())
        .ok_or_else(|| ProofIrError("coverage population kind is required".into()))?;
    let observed = object
        .get("observed")
        .or_else(|| object.get("queryMatched"))
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let omissions = object
        .get("omissions")
        .and_then(Value::as_array)
        .map_or(0, Vec::len) as u64;
    Ok(Coverage {
        population_kind: kind.into(),
        expected: object.get("expected").and_then(Value::as_u64),
        observed,
        omissions,
    })
}

pub fn parse_observation(value: &Value) -> Result<Observation, ProofIrError> {
    let object = value
        .as_object()
        .ok_or_else(|| ProofIrError("observation must be an object".into()))?;
    let observation_id = object
        .get("observationId")
        .and_then(Value::as_str)
        .filter(|v| !v.is_empty())
        .ok_or_else(|| ProofIrError("observationId is required".into()))?;
    let environment = object
        .get("environmentRef")
        .and_then(Value::as_str)
        .filter(|v| !v.is_empty())
        .ok_or_else(|| ProofIrError("environmentRef is required".into()))?;
    let subject = parse_subject(
        object
            .get("subjectRef")
            .ok_or_else(|| ProofIrError("subjectRef is required".into()))?,
        EnvironmentRef(environment.into()),
    )?;
    let kind = object
        .get("kind")
        .and_then(Value::as_str)
        .unwrap_or("unknown");
    let result = object
        .get("result")
        .and_then(Value::as_str)
        .unwrap_or("unknown");
    let authority_basis = object
        .get("authorityBasis")
        .and_then(Value::as_str)
        .unwrap_or("unknown");
    let guarantee_scope = object
        .get("guaranteeScope")
        .and_then(Value::as_str)
        .unwrap_or("unknown");
    Ok(Observation {
        observation_id: observation_id.into(),
        subject,
        kind: kind.into(),
        result: result.into(),
        authority_basis: authority_basis.into(),
        guarantee_scope: guarantee_scope.into(),
    })
}

pub fn parse_derivation_steps(value: &Value) -> Result<Vec<DerivationStep>, ProofIrError> {
    let rows = value
        .as_array()
        .ok_or_else(|| ProofIrError("derivation steps must be an array".into()))?;
    let mut steps = Vec::with_capacity(rows.len().min(MAX_ITEMS));
    if rows.len() > MAX_ITEMS {
        return Err(ProofIrError("derivation steps exceed item limit".into()));
    }
    for row in rows {
        let object = row
            .as_object()
            .ok_or_else(|| ProofIrError("derivation step must be an object".into()))?;
        let step_id = object
            .get("stepId")
            .and_then(Value::as_str)
            .filter(|v| !v.is_empty())
            .ok_or_else(|| ProofIrError("stepId is required".into()))?;
        let conclusion = object
            .get("conclusion")
            .and_then(Value::as_str)
            .filter(|v| !v.is_empty())
            .ok_or_else(|| ProofIrError("conclusion is required".into()))?;
        let rule = object
            .get("rule")
            .and_then(Value::as_str)
            .unwrap_or("unknown");
        let premises = object
            .get("premises")
            .and_then(Value::as_array)
            .ok_or_else(|| ProofIrError("premises are required".into()))?
            .iter()
            .map(|v| {
                v.as_str()
                    .map(str::to_owned)
                    .ok_or_else(|| ProofIrError("premise must be a string".into()))
            })
            .collect::<Result<Vec<_>, _>>()?;
        steps.push(DerivationStep {
            step_id: step_id.into(),
            premises,
            conclusion: conclusion.into(),
            rule: rule.into(),
        });
    }
    Ok(steps)
}

/// Validate the acyclic portion of a derivation graph without interpreting
/// prover terms. Each step is an AND edge over its premises.
pub fn validate_derivation(steps: &[DerivationStep]) -> Result<(), ProofIrError> {
    let mut adjacency = std::collections::HashMap::<&str, Vec<&str>>::new();
    for step in steps {
        if step.step_id.is_empty() || step.conclusion.is_empty() {
            return Err(ProofIrError("derivation step has an empty identity".into()));
        }
        adjacency.entry(step.conclusion.as_str()).or_default();
        for premise in &step.premises {
            adjacency
                .entry(premise.as_str())
                .or_default()
                .push(step.conclusion.as_str());
        }
    }
    fn visit<'a>(
        node: &'a str,
        graph: &std::collections::HashMap<&'a str, Vec<&'a str>>,
        active: &mut std::collections::HashSet<&'a str>,
        done: &mut std::collections::HashSet<&'a str>,
    ) -> bool {
        if active.contains(node) {
            return false;
        }
        if !done.insert(node) {
            return true;
        }
        active.insert(node);
        let valid = graph
            .get(node)
            .map(|next| next.iter().all(|child| visit(child, graph, active, done)))
            .unwrap_or(true);
        active.remove(node);
        valid
    }
    let mut active = std::collections::HashSet::new();
    let mut done = std::collections::HashSet::new();
    if adjacency
        .keys()
        .all(|node| visit(node, &adjacency, &mut active, &mut done))
    {
        Ok(())
    } else {
        Err(ProofIrError("derivation graph contains a cycle".into()))
    }
}

impl Diagnostic {
    pub fn new(
        artifact_id: impl Into<String>,
        stage: impl Into<String>,
        code: impl Into<String>,
    ) -> Self {
        Self {
            artifact_id: artifact_id.into(),
            stage: stage.into(),
            code: code.into(),
            pointer: String::new(),
            retained: false,
        }
    }
}

pub fn validation_diagnostics(value: &Value) -> Vec<Diagnostic> {
    let artifact_id = value
        .as_object()
        .and_then(|m| m.get("artifactId"))
        .and_then(Value::as_str)
        .unwrap_or("<unbound>");
    let Some(object) = value.as_object() else {
        return vec![Diagnostic {
            artifact_id: artifact_id.into(),
            stage: "decoded".into(),
            code: "decode-failed".into(),
            pointer: String::new(),
            retained: false,
        }];
    };
    if object.get("proofirVersion") != Some(&Value::String(VERSION.into())) {
        return vec![Diagnostic {
            artifact_id: artifact_id.into(),
            stage: "envelope-valid".into(),
            code: "unsupported-version".into(),
            pointer: "/proofirVersion".into(),
            retained: false,
        }];
    }
    if object
        .get("artifactKind")
        .and_then(Value::as_str)
        .is_none_or(str::is_empty)
    {
        return vec![Diagnostic {
            artifact_id: artifact_id.into(),
            stage: "kind-schema-valid".into(),
            code: "invalid-artifact-kind".into(),
            pointer: "/artifactKind".into(),
            retained: false,
        }];
    }
    Vec::new()
}

impl std::fmt::Display for ProofIrError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}
impl std::error::Error for ProofIrError {}

pub fn canonical_bytes(value: &Value) -> Result<Vec<u8>, ProofIrError> {
    check_bounds(value, 0)?;
    let mut out = Vec::new();
    write_canonical(value, &mut out)?;
    Ok(out)
}

fn check_bounds(v: &Value, depth: usize) -> Result<(), ProofIrError> {
    if depth > MAX_DEPTH {
        return Err(ProofIrError(
            "canonical payload exceeds nesting limit".into(),
        ));
    }
    match v {
        Value::String(s) if s.len() > MAX_STRING_BYTES => {
            Err(ProofIrError("string exceeds byte limit".into()))
        }
        Value::Array(xs) => {
            if xs.len() > MAX_ITEMS {
                return Err(ProofIrError("collection exceeds item limit".into()));
            }
            for x in xs {
                check_bounds(x, depth + 1)?;
            }
            Ok(())
        }
        Value::Object(m) => {
            if m.len() > MAX_ITEMS {
                return Err(ProofIrError("object exceeds item limit".into()));
            }
            for (k, x) in m {
                check_bounds(&Value::String(k.clone()), depth + 1)?;
                check_bounds(x, depth + 1)?;
            }
            Ok(())
        }
        _ => Ok(()),
    }
}

fn write_canonical(v: &Value, out: &mut Vec<u8>) -> Result<(), ProofIrError> {
    match v {
        Value::Null => out.extend_from_slice(b"null"),
        Value::Bool(b) => out.extend_from_slice(if *b { b"true" } else { b"false" }),
        Value::Number(n) => out.extend_from_slice(n.to_string().as_bytes()),
        Value::String(s) => {
            serde_json::to_writer(&mut *out, s).map_err(|e| ProofIrError(e.to_string()))?
        }
        Value::Array(xs) => {
            out.push(b'[');
            for (i, x) in xs.iter().enumerate() {
                if i > 0 {
                    out.push(b',');
                }
                write_canonical(x, out)?;
            }
            out.push(b']');
        }
        Value::Object(m) => {
            out.push(b'{');
            let mut keys: Vec<_> = m.keys().collect();
            keys.sort();
            for (i, k) in keys.iter().enumerate() {
                if i > 0 {
                    out.push(b',');
                }
                serde_json::to_writer(&mut *out, *k).map_err(|e| ProofIrError(e.to_string()))?;
                out.push(b':');
                write_canonical(&m[*k], out)?;
            }
            out.push(b'}');
        }
    }
    Ok(())
}

pub fn detached_content_id(envelope: &Value) -> Result<String, ProofIrError> {
    let mut detached = envelope.clone();
    if let Value::Object(m) = &mut detached {
        m.remove("artifactId");
    } else {
        return Err(ProofIrError("v3 artifact must be an object".into()));
    }
    let mut hasher = Sha256::new();
    hasher.update(canonical_bytes(&detached)?);
    Ok(format!("sha256:{:x}", hasher.finalize()))
}

pub fn validate_envelope(value: Value) -> Result<Artifact, ProofIrError> {
    let m = value
        .as_object()
        .ok_or_else(|| ProofIrError("v3 artifact must be a JSON object".into()))?;
    for key in [
        "proofirVersion",
        "artifactKind",
        "artifactId",
        "producer",
        "environmentRef",
        "subjectRefs",
        "coverage",
        "payload",
        "extensions",
    ] {
        if !m.contains_key(key) {
            return Err(ProofIrError(format!("v3 envelope missing key: {key}")));
        }
    }
    if m["proofirVersion"] != VERSION {
        return Err(ProofIrError("unsupported ProofIR version".into()));
    }
    if m["artifactKind"].as_str().is_none_or(str::is_empty) {
        return Err(ProofIrError(
            "artifactKind must be a non-empty string".into(),
        ));
    }
    if !m["producer"].is_object() || !m["coverage"].is_object() {
        return Err(ProofIrError("producer and coverage must be objects".into()));
    }
    if !m["subjectRefs"].is_array() || !m["extensions"].is_object() {
        return Err(ProofIrError(
            "subjectRefs must be an array and extensions an object".into(),
        ));
    }
    let encoded = canonical_bytes(&value)?;
    if encoded.len() > 8 * 1024 * 1024 {
        return Err(ProofIrError("canonical payload exceeds byte limit".into()));
    }
    let expected = detached_content_id(&value)?;
    if m["artifactId"] != expected {
        return Err(ProofIrError(
            "artifactId does not match detached canonical content".into(),
        ));
    }
    Ok(Artifact {
        envelope: value,
        content_id: expected,
    })
}

pub fn make_envelope(
    kind: &str,
    producer: Value,
    environment: &str,
    payload: Value,
) -> Result<Artifact, ProofIrError> {
    let mut m = Map::new();
    m.insert("proofirVersion".into(), Value::String(VERSION.into()));
    m.insert("artifactKind".into(), Value::String(kind.into()));
    m.insert("artifactId".into(), Value::Null);
    m.insert("producer".into(), producer);
    m.insert("environmentRef".into(), Value::String(environment.into()));
    m.insert("subjectRefs".into(), Value::Array(vec![]));
    m.insert("coverage".into(), Value::Object(Map::new()));
    m.insert("payload".into(), payload);
    m.insert("extensions".into(), Value::Object(Map::new()));
    let mut value = Value::Object(m);
    let id = detached_content_id(&value)?;
    value
        .as_object_mut()
        .unwrap()
        .insert("artifactId".into(), Value::String(id));
    validate_envelope(value)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn canonical_keys_are_sorted() {
        assert_eq!(
            canonical_bytes(&serde_json::json!({"b":1,"a":2})).unwrap(),
            br#"{"a":2,"b":1}"#
        );
    }
}
