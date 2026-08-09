## Why

ProofIR currently mixes file, generation, artifact, declaration-name, claim, DAG, and node identities, causing unnecessary generation churn and hidden string-equality joins.

## What Changes

- Define stable content artifact IDs separately from generation observations.
- Define Merkle-rooted prover environment manifests.
- Define typed environment-scoped subject references and artifact-scoped local references.
- Remove semantic joins based on unrelated bare strings.
- Specify Lean declaration and expression-fingerprint identity profiles without requiring non-Lean readers to parse Lean terms.

## Capabilities

### New Capabilities
- `proofir-content-environment-and-subject-identity`: Canonical identity and reference semantics for ProofIR.

### Modified Capabilities

## Impact

Touches canonical hashing, catalog IDs, replay relationships, claims, DAG nodes, attachments, diffs, caching, and SQLite keys.
