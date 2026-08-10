//! Boundary types for Lean workers. No Lean parser, elaborator, or kernel is linked.
use serde_json::Value;
#[derive(Debug, Clone, PartialEq)]
pub struct OpaqueLeanPayload(pub Value);
