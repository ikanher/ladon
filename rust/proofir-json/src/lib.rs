//! JSON adapter for the canonical ProofIR core.
use proofir_core::{canonical_bytes, ProofIrError};
use serde_json::Value;
pub fn canonical_json(value: &Value) -> Result<Vec<u8>, ProofIrError> {
    canonical_bytes(value)
}
