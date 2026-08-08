## Context

The project-local proof-search database owns declaration identity, module
source hashes, theorem-lineage closures, locks, integrity checks, and atomic
replacement. ProofIR remains outside that lifecycle: the bridge normalizes one
input in memory, joins it to one report, and optionally exports summary rows to
an unrelated atlas database.

The exploration found 315 current Quux JSON artifacts across 187 kinds. Only
nine are supported Lean-surface bundles, with 63 distinct surfaces. Fifty-two
of those surfaces also have separate successful replay-provenance records, and
the CDC ProofIR v2 DAG has 22 obligations with both established and conditional
routes. JSON lookup is already fast, so the design must earn its cost through
cross-evidence joins, provenance, and coverage.

## Goals / Non-Goals

**Goals:**

- Put normalized ProofIR evidence in the existing project-local database.
- Answer surface, replay, obligation-route, declaration, and lineage questions
  with indexed SQL and explicit authority boundaries.
- Make configured inputs reproducible across atomic base-index replacement.
- Give coders five ordered, TDD-first packets with portable exit classes.

**Non-Goals:**

- No relational mirror of every Quux artifact dialect.
- No raw ProofIR semantics inferred from filenames, prose, or module proximity.
- No promotion of replay, checker, paper, or ProofIR status to Lean theorem truth.
- No second database, graph service, daemon, or caller-specific command.
- No performance claim based on replacing already-fast `rg` or `jq` lookup.

## Decisions

### 1. Land five packets in strict evidence order

```text
artifact identity/catalog
          |
          v
surfaces + replay provenance     obligation DAG + SQL routes
          |                               |
          +---------------+---------------+
                          v
             declaration + lineage attachments
                          |
                          v
               CLI integration + calibration
```

The catalog packet lands first. Surface/replay ingestion then establishes the
artifact-owned evidence model. Obligation DAG ingestion follows the same model
and adds SQL traversal. Only then may attachments reference declaration and
lineage identities. CLI work begins after all stored result contracts are
stable.

### 2. Extend the existing proof-search database

All rows live in `<repo>/.ladon/index/proof-search.sqlite` and respect its
`--index` override, lock, constraints, size limit, schema generation, integrity
validation, and atomic publication. A second database is rejected because it
would duplicate repository identity, declaration IDs, lineage freshness, and
operational cleanup.

### 3. Separate catalog coverage from semantic support

Configured artifacts receive identity, kind, schema, hash, path, and status
rows even when their dialect is unsupported. Semantic tables accept only
explicit adapters. Unsupported input is observable but cannot create claims,
surfaces, nodes, edges, attachments, or authority.

### 4. Preserve facts rather than collapse status

A surface's `not_replayed_by_extractor` boundary and a separate provenance
artifact's successful `lake build` are two facts. They are linked by exact
artifact hash and surface ID but never folded into one synthetic `replayed`
status. The same rule separates checker validation, ProofIR obligation status,
paper authority, and Lean lineage authority.

### 5. Use SQL for graph selection and joining

Forward/reverse obligation traversal, minimum depth, source/target selection,
status filters, declaration lookup, artifact relationships, and lineage overlay
use parameterized SQL and recursive CTEs. Pure algorithms are permitted only on
already bounded rows when SQLite cannot express a stable presentation cleanly.

### 6. Attach by source identity, never by first match

Exact repository path, source hash, declaration name, and compatible range own
high-confidence attachment. Ambiguous names remain ambiguous. Module or prose
similarity is context-only. Attachment rows reference stable declaration IDs;
ProofIR edges never enter `lineage_edges`.

### 7. Make artifact inputs part of the generation recipe

The base index is replaced atomically, so mutable post-build imports would be
lost. Configured artifact paths/globs and their hashes become captured build
inputs and are ingested into the unpublished database before validation. An
explicit import operation, if retained for diagnostics, must state that it is
ephemeral unless its inputs are configured for the next rebuild.

## Risks / Trade-offs

- [Dialect sprawl turns Ladon into a ProofIR mirror] → Catalog unknown kinds but
  normalize only four admitted seams with versioned adapters.
- [Related evidence is mistaken for theorem authority] → Store authority and
  relation kind on every row and keep separate result sections/nonclaims.
- [Duplicate declarations produce arbitrary joins] → Require unique strongest
  matches and store ambiguity diagnostics rather than first-row selection.
- [Base rebuild silently loses evidence] → Capture imports in generation
  identity and test two consecutive rebuilds.
- [Recursive DAG queries explode] → Require depth/node/edge/route caps,
  deterministic ordering, and explicit truncation.
- [Downstream aggregates double-count source evidence] → Mark snapshots and
  architecture indexes as derived artifacts; do not normalize their copied
  surfaces as primary rows.

## Migration Plan

1. Bump the disposable private schema generation and rebuild local indexes.
2. Add artifact catalog tables and configured input capture.
3. Add surface/replay and obligation adapters with frozen fixtures.
4. Add exact declaration and lineage attachments.
5. Add CLI projections, docs, skills, and real-repository observations.
6. Roll back by deleting the generated database and rebuilding without
   configured ProofIR inputs; existing bridge commands remain available.

## Open Questions

- Whether configured artifact discovery belongs in the existing project config
  or a dedicated `.ladon/proofir.json` manifest; the first packet must select
  one ordinary repository-owned mechanism and fingerprint it.
- Whether a later adapter should normalize additional custom CDC witnesses.
  V1 catalogs them and reports their lack of explicit theorem attachment.
