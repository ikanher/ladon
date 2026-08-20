## Context

`proof_search_schema.py` already defines normalized declarations and a
`declaration_dependencies` table with both traversal indexes, but lexical v1 leaves
that population unavailable and lacks closure-level provenance. The theorem planner
produces the required exact nodes, typed edges, SCCs, external frontier, trust facts,
and fingerprints in `semanticGraph`.

## Goals / Non-Goals

**Goals:** persist multiple exact theorem closures, constrain every owned row,
validate plan authority/completeness, support atomic replacement, and expose enough
metadata for freshness and query selection.

**Non-Goals:** no JSON blob as the primary query store, no cross-toolchain raw Lean
expressions, no inferred lexical edges, and no public table compatibility.

## Decisions

### 1. Rebuild into a new private schema generation

Increment `PROOF_SEARCH_INDEX_SCHEMA_VERSION` and the schema generation. Because
the database is generated state, build a complete replacement and publish it using
the existing atomic path rather than maintain a fragile in-place v1 migration.

### 2. Add normalized lineage tables

- `lineage_closures`: closure id, theorem name, plan identity, closure fingerprint,
  repository/configuration/toolchain/helper/index identities, semantic status,
  authority, source target metadata, and unsupported-facet JSON.
- `lineage_nodes`: closure id plus exact declaration name, owner module, kind,
  project/external/generated/frontier flags, axiom/unsafe flags, and type/value
  fingerprints where available.
- `lineage_edges`: closure id, source, target, `type|value` kind, and target metadata.
- `lineage_trust`: closure id, trust kind, `type|value|declaration` scope, and target.
- `lineage_scc_members`: closure id, component identity, member, and cyclic flag.
- `lineage_omissions`: closure id, facet, subject, reason, and bounded detail JSON.

Every edge endpoint and trust target is represented in `lineage_nodes`; external
frontier endpoints are synthesized from the planner's typed dependency rows. Use
composite foreign keys with cascading deletion from one closure.

### 3. Require explicit access paths

Add and introspect indexes for closure lookup by theorem/freshness, nodes by closure
and boundary/owner/kind, forward edges `(closure_id, source, kind, target)`, reverse
edges `(closure_id, target, kind, source)`, trust targets, and SCC membership. Add
representative `EXPLAIN QUERY PLAN` assertions in addition to name/column checks.

### 4. Validate before the write transaction

The adapter accepts `TheoremPlan` or its validated payload, requires semantic status
`complete` and authority `lean_environment`, checks helper protocol compatibility,
recomputes node/edge counts and the closure fingerprint, synthesizes frontier nodes,
and verifies all endpoints. It does not require capsule `eligible=true`; instead it
records irrelevant packaging limitations without upgrading them.

### 5. Replace one theorem closure atomically

Within one immediate transaction, insert the new closure and children, run targeted
foreign-key/count/fingerprint checks, switch the theorem's active closure identity,
and delete the superseded closure. Any failure rolls back to the prior active row.
The base database's integrity and size ceiling still apply.

## Risks / Trade-offs

- [External targets have incomplete metadata] → Store explicit frontier/location
  status and never fabricate source paths.
- [Dense closures enlarge the DB] → Normalize strings, retain per-theorem closure
  ownership, enforce the existing size cap, and report rejected ingestion cleanly.
- [One edge appears in many closures] → Prefer simple closure-local correctness in
  v1 lineage; global edge deduplication can follow measured storage pressure.
- [A malformed plan corrupts the index] → Validate outside, transact inside, and run
  foreign-key/integrity checks before commit.

## Migration Plan

Rebuild v1 databases through the existing explicit index build command. A new base
index begins with zero stored lineages and coverage `unavailable:not_ingested`.
Ingest theorem closures individually. Removing the generated database remains the
rollback.

## Open Questions

- Whether plan source-range rows should be denormalized into lineage nodes initially
  or joined through declarations whenever the declaration is project-owned.
