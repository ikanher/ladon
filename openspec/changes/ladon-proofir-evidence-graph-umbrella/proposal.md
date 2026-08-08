## Why

Ladon can render one compact ProofIR input at a time, but its project-local
database cannot preserve or query ProofIR artifacts, replay provenance,
obligation routes, or their explicit attachments to Lean declarations. Real
Quux evidence shows that the value is cross-evidence querying and honest
authority boundaries, not faster JSON lookup.

## What Changes

- Catalog configured ProofIR artifacts and their immutable identities in the
  existing project-local proof-search database.
- Normalize supported Lean surfaces, replay provenance, obligation DAGs, and
  checker witnesses without importing arbitrary ProofIR dialect semantics.
- Attach surfaces to exact source-backed declaration rows and overlay them on
  stored theorem lineage without converting ProofIR edges into Lean edges.
- Query artifact relationships and obligation routes with indexed SQL and
  bounded recursive CTEs.
- Add ordinary CLI inspection, generation-safe rebuild behavior, coverage,
  documentation, and portable plus real-repository calibration.

## Capabilities

### New Capabilities

- `ladon-proofir-db-schema-and-artifact-catalog`: Project-local artifact
  generations, identities, relationships, constraints, indexes, and coverage.
- `ladon-proofir-surface-and-replay-ingestion`: Normalized Lean surfaces,
  quoted claims, replay provenance, and non-promoting evidence joins.
- `ladon-proofir-obligation-dag-ingestion-and-queries`: Normalized obligation
  facts and edges with bounded SQL route queries and preserved authority.
- `ladon-proofir-declaration-lineage-attachments`: Exact declaration joins,
  ambiguity handling, source freshness, and lineage overlays.
- `ladon-proofir-cli-integration-and-calibration`: Installed CLI queries,
  rebuild integration, documentation, and fixture/Quux calibration.

### Modified Capabilities

None.

## Impact

- Extends the private proof-search SQLite schema, generation lifecycle,
  integrity validation, coverage, and status counts.
- Reuses the current ProofIR normalizer and bridge trust rules while adding
  adapters for replay provenance and ProofIR v2 obligation DAG evidence.
- Extends ordinary Ladon CLI surfaces, JSON/text result schemas, tests, docs,
  and the maintained Ladon skill.
- Does not add a second database, graph service, daemon, or raw-dialect store.
