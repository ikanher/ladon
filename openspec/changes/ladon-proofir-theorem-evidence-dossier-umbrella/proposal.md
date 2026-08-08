## Why

ProofIR data is now in Ladon's project-local database, but its value is limited by thin projections, incomplete route semantics, implicit absence, and weak CLI presentation. This umbrella turns stored evidence into theorem-centric answers and repository-wide review intelligence without collapsing ProofIR authority into Lean authority.

## What Changes

- Coordinate a complete theorem dossier projection over declaration, surface, claim, replay, DAG, lineage, diagnostic, and coverage evidence.
- Make obligation start/end routes and representative trees exact and bounded.
- Define explicit negative-evidence and coverage semantics.
- Add repository-wide triage queries for evidence health and review priorities.
- Finish ordinary CLI rendering, documentation, portable integration tests, and real-repository calibration.

## Capabilities

### New Capabilities

- `ladon-proofir-theorem-dossier-query`: Complete theorem-centric stored-evidence projection.
- `ladon-proofir-obligation-route-paths-and-trees`: Endpoint-correct bounded paths and selected trees.
- `ladon-proofir-negative-evidence-and-coverage`: Honest absence, ambiguity, staleness, and availability semantics.
- `ladon-proofir-repository-triage-queries`: Repository-wide evidence health and priority queries.
- `ladon-proofir-evidence-cli-rendering-and-calibration`: Ordinary CLI, renderers, docs, and calibration.

### Modified Capabilities

## Impact

Coordinates five dependency-ordered child changes across the existing SQLite schema/query layer, proof-search CLI, documentation, tests, calibration harnesses, and authoritative Ladon skill. No second database or implicit external execution is introduced.
