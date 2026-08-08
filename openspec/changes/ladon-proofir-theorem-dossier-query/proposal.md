## Why

ProofIR is now normalized in the project-local index, but theorem lookup exposes only a thin surface/attachment slice. Users need one theorem-centric result that assembles all relevant stored evidence while preserving the boundary between Lean declarations, quoted ProofIR claims, replay observations, obligation context, and lineage.

## What Changes

- Replace the thin theorem evidence projection with a versioned, bounded theorem dossier.
- Return declaration attachment, surfaces, claims, replay runs, artifact relations, DAG participation, lineage availability, diagnostics, and nonclaims in separate sections.
- Support exact theorem identity through selected attachments and explicit ProofIR declaration names; never infer theorem evidence from proximity or filenames.
- Make all ordering, bounds, freshness, and authority fields deterministic and render-neutral.

## Capabilities

### New Capabilities

- `ladon-proofir-theorem-dossier-query`: Complete theorem-centric projection over stored ProofIR and Lean evidence.

### Modified Capabilities

## Impact

Primarily affects `proofir_queries.py`, attachment/lineage joins, proof-search result contracts, and focused query tests. It reuses the existing project-local SQLite database and performs no external execution.
