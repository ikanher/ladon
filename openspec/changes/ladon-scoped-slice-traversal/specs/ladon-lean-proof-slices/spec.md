# Spec Delta

## Purpose

Expose source-bound application observations with explicit traversal allowances and reproducible resource settings.

## ADDED Requirements

### Requirement: Configurable traversal allowance
The CLI and Python extraction API SHALL accept a node allowance from 1 to 1,048,576, defaulting to 131,072, for both declaration and scoped profiles. Invalid API types, booleans and out-of-range values SHALL be rejected before filesystem or compiler setup. Increasing this allowance SHALL NOT increase time, memory, depth, source, expression or output bounds.

#### Scenario: Explicit allowance reaches Lean
- **WHEN** the same supported slice is requested with a one-node allowance and with sufficient allowance
- **THEN** the first result is incomplete with node exhaustion and the second extracts the slice, recording the chosen allowance in each result

#### Scenario: Invalid allowance
- **WHEN** the API receives zero, a negative value, a boolean, a fractional value, a string or an integer above the maximum
- **THEN** it rejects the node budget before resolving the repository or invoking Lean

### Requirement: Traversal allowance retained on replay
The selected node allowance SHALL be validated, included in slice identity, and used for initial and final correspondence freshness extraction. A new default SHALL NOT silently replace an explicit historical allowance.

#### Scenario: Nondefault correspondence replay
- **WHEN** a correspondence plan contains a slice extracted with a 37,000-node allowance
- **THEN** both freshness extractions use 37,000 and retain the exact application and scoped observation contract

### Requirement: Dependent instance names survive closed proof replay
Slice exports and source-goal completion SHALL preserve instance names referenced by later binder types, even when absent from the final proof body. They SHALL retain empty-context parsing, type/proof equality, freshness, and independent completion trust checks. Completion SHALL NOT inherit the slice-only 64-level telescope limit.

#### Scenario: Unused dependent instance
- **WHEN** a valid closed proof has an instance referenced only by a later binder type
- **THEN** extraction and completion retain the binding and replay the exact proof without an unknown-identifier failure

#### Scenario: Completion telescope exceeds the slice limit
- **WHEN** a valid 70-binder completion fits Lean's configured recursion limit
- **THEN** completion checks and independently replays it while slice consumers retain their own depth bound
