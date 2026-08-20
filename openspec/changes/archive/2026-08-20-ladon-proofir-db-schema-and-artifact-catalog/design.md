## Context

`build_proof_search_index` creates a fresh temporary SQLite file, validates it,
and atomically replaces the canonical project-local database. Post-build rows
are therefore disposable. The first packet must make ProofIR artifact inputs a
reproducible part of that generation while preserving the existing lock and
failure semantics.

## Goals / Non-Goals

**Goals:**

- Establish constrained artifact identity and relationship tables.
- Catalog configured supported and unsupported artifacts honestly.
- Rebuild the same catalog deterministically with the base index.
- Validate all constraints, foreign keys, indexes, caps, and coverage.

**Non-Goals:**

- No surface, replay, DAG, declaration, or lineage semantics in this packet.
- No recursive repository-wide search for JSON based on filename guesses.
- No retained raw JSON blobs or public coupling to private table names.

## Decisions

1. Add `proofir_generations`, `proofir_artifacts`,
   `proofir_artifact_relations`, and `proofir_diagnostics` as normalized private
   tables. Use deterministic IDs derived from generation identity, relative
   path, content hash, kind, and schema.
2. Accept only explicitly configured repository-relative files or bounded
   globs. Reject paths escaping the repository and include configuration plus
   artifact bytes in generation/freshness identity.
3. Store compact identity and selected top-level metadata, not raw payloads.
   Adapter-specific packets own semantic columns.
4. Publish an artifact only after JSON shape, byte cap, content hash, kind, and
   schema metadata are captured. Malformed JSON becomes a diagnostic/catalog
   status and cannot produce semantic rows.
5. Reuse the existing build lock and unpublished database transaction. A failed
   catalog ingestion must not replace the previous database generation.
6. Add named indexes for active generation, kind/schema, path/hash, relation
   source/target, and diagnostic reason. Extend required-index and foreign-key
   validation rather than relying on implicit indexes.

## Risks / Trade-offs

- [Configured globs grow unexpectedly] → Enforce file-count, per-file, and total
  byte caps before publication.
- [Unsupported artifacts look validated] → Separate `cataloged` from
  `normalized` and record semantic coverage as unavailable.
- [Absolute paths reduce portability] → Store repository-relative paths and
  expose absolute paths only in runtime result rendering.
- [Rebuild cost increases] → Hash configured artifacts once during captured
  snapshot construction and record measured cost separately from correctness.

## Migration Plan

1. Add failing schema and two-rebuild tests.
2. Bump schema/helper identities.
3. Add configuration capture, schema, ingestion, validation, and counts.
4. Rebuild disposable fixture and real indexes.
5. Roll back by removing the generated database and rebuilding under the prior
   code; no source data is stored only in SQLite.

## Open Questions

- Select the exact repository-owned configuration filename after checking the
  existing configuration conventions; do not add an environment-only path.
