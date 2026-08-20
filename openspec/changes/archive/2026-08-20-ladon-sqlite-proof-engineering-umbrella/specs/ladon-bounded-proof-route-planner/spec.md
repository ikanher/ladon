## ADDED Requirements

### Requirement: Planner states model AND/OR proof obligations
The planner SHALL represent a state as a canonical multiset of unresolved goal fingerprints and a transition as applying one Lean-verified candidate to one goal and replacing it with all residual proof premises.

#### Scenario: Candidate creates two premises
- **WHEN** Lean verifies a theorem application with two residual proof goals
- **THEN** the successor state contains both goals and is complete only after both are discharged

### Requirement: Search is deterministic and bounded
The planner SHALL use bounded best-first search with the documented lexicographic cost and explicit limits for states, candidates, depth, unresolved goals, Lean requests, routes, diagnostics, and output bytes.

#### Scenario: State cap is reached
- **WHEN** alternatives remain after the expansion cap
- **THEN** search terminates deterministically and records the cap and omitted frontier without claiming no route exists

### Requirement: Every transition is Lean verified
SQLite shapes and lexical evidence MAY shortlist transitions but MUST NOT enter a route unless the semantic verifier confirms the candidate application under the exact generation and context.

#### Scenario: Stored candidate is stale
- **WHEN** a shortlisted declaration is missing from the current Lean environment
- **THEN** it is a rejected stale transition and does not produce a successor state

### Requirement: Replay and history preserve identities
A complete route MAY become `replayed` only after a supervised scratch example succeeds; optional rejected-route memory MUST use a separate sidecar keyed by index, worker, goal, context, registry, and policy identities.

#### Scenario: Same goal has a new generation
- **WHEN** the repository or worker identity changes
- **THEN** prior history is not reused as current acceptance or rejection evidence
