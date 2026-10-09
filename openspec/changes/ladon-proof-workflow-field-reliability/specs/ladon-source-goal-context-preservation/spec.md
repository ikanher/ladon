## Purpose
Preserve complete local and source context while observing and independently replaying a selected Lean goal in bounded, read-only operations.

## ADDED Requirements

### Requirement: Independent replay preserves source declarations
Completion SHALL preserve preceding same-file declarations needed by the selected goal and proposed proof in its independent compiler replay, with exact source/import identity and transitive axiom checks.

#### Scenario: Earlier definition in an unfinished file
- **WHEN** a valid early goal uses a definition declared earlier in the same file and later source work is unfinished
- **THEN** completion checks the original goal in a separate compiler process without changing project files

#### Scenario: Earlier admitted dependency
- **WHEN** the replayed proof transitively depends on an earlier same-file admitted theorem
- **THEN** completion reports the disallowed dependency and does not claim completion

### Requirement: Capture preserves local meaning under bounds
Capture SHALL preserve ordered locals, local values and their full structural meaning using versioned expression identities. Bound exhaustion SHALL retain a specific operational outcome and informative size diagnostics without publishing an incomplete capture.

#### Scenario: Shared proof expressions
- **WHEN** a local proof contains repeated structural subexpressions
- **THEN** the capture preserves their complete meaning and repeated references without unbounded repeated expansion

#### Scenario: Output remains too large
- **WHEN** the helper exceeds the configured output limit
- **THEN** capture remains unavailable with output-limit and measured resource evidence
