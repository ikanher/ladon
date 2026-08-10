//! Strict envelope validation; semantic Lean payloads are deliberately opaque.
use proofir_core::{validate_envelope, Artifact, ProofIrError};
use serde_json::Value;
pub fn validate(value: Value) -> Result<Artifact, ProofIrError> {
    validate_envelope(value)
}
