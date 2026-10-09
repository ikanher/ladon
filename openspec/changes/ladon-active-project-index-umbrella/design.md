# Design

## Context

See `proposal.md` for the motivation and `sources.md` for the report disposition. Current snapshot capture hashes supported source bytes, configuration, toolchain, ProofIR inputs and layout. The index already stores per-module source hashes. Status computes a current identity but returns no source delta. Name search already prioritizes case-folded exact names and labels ranking contributions; it does not summarize an exact miss before suggestions. The default name CLI verifies freshness, while stored mode intentionally avoids verification.

Publication already uses a persistent kernel-held destination lock and durable replacement. The base-build default is 1 GiB; complete-database and lineage policies have separate owners. These existing contracts should carry the new operations.

## Goals / Non-Goals

**Goals:** coherent source inventories, useful stale-search diagnostics, explicit incremental lexical publication, and preview-first index lifecycle operations, implemented in three dependency-ordered batches.

**Non-Goals:** automatic rebuilds on queries, a watcher/daemon, source edits or Lean builds in the external project, automatic pruning, new theorem ranking or semantic engines, and requalification of unrelated historical feature programs.

## Decisions

### 1. Reuse one snapshot comparison

Compare stored module path/hash/identity rows with the same supported source population used for builds. Return aggregate deltas plus bounded sorted samples. A rename is an addition and removal unless content identity supports an explicitly labelled correlation. Full source verification remains content-based; timestamps alone cannot certify freshness. Include supported untracked files and retain generated/external-source policies.

Expose `index status --changed` with bounded listing controls and `--details` for the existing large inventory. Preserve JSON fields; default text gets a concise projection. Add source-change and exact-match diagnostics to name search without changing Boolean operators or silently dropping query terms. For an identifier, distinguish fully qualified exact matches, basename exact matches and lexical suggestions, preserving ambiguity and scope. Counts describe the selected indexed population before the display limit. If change relevance cannot be established from exact selected source membership, return unknown; namespace similarity is only a hint.

Document `generationIdentity` as the database rows' identity and `currentGenerationIdentity` as the supported inputs observed now. Stored mode keeps the latter null. Characterize the August fresh-build discrepancy with stable fixtures and configuration variations; identical displayed stored fingerprints alone do not establish that live inputs were identical. Do not assume its hypothesized transient-state cause is confirmed.

### 2. Update a private copy and publish atomically

Add `proof-search index update`, using the existing base schema and metadata checks. No compatible base means an explicit full-build-required outcome. Start with a consistent SQLite backup under the destination publisher lock, reuse unchanged module extraction, and replace changed/deleted lexical rows and their dependent symbols, binders, structures, FTS postings and import records. Recompute affected global lexical summaries through their existing owners; report work that remains global. Validate referential integrity, query access paths and statistics before replacement.

Retain canonical and lineage records with their original identities; invalidate their current associations when necessary. Never advance semantic coverage merely because lexical metadata changed. If the current storage model cannot safely retain those records during update, stop with a supported full-build-required reason rather than silently deleting or reparenting evidence. Compare updated lexical outputs and identities with clean builds, including database populations with stored evidence.

Reobserve supported inputs before publication. A change during extraction produces a source-changed terminal outcome and leaves the old database intact. A no-op does not replace it. Existing open readers retain the old complete file; new readers see the new complete file. Preserve the shared lock implementation, current storage ceilings, temp-file cleanup and failure receipts.

Alternative: mutate the published database in place. Rejected initially because atomic replacement already provides a clear reader and rollback boundary. A consistent copy has disk cost; acceptance depends on measuring it.

### 3. Inventory first, explicit cleanup second

Add `proof-search index list` and `index prune` over an explicitly selected index directory (default the project's `.ladon/index`). List reports bounded inspected entries, their bytes and an exact entry count; when truncated, byte accounting is explicitly limited to the returned entries. It includes read-only metadata, repository identity, filesystem mtime as an age hint, lock state, and classification. It does not claim the time is last use.

Prune defaults to preview. `--apply` plus explicit path selection or an explicitly selected age-filtered private-index population authorizes deletion. Protect the default index, explicit `--keep` selections and indexes with retained semantic/lineage/ProofIR payloads; no force-delete route is needed in this package. Reuse kernel ownership, revalidate file identity after locking, and refuse symlinks, foreign metadata or uncertain sidecar ownership. Do not unlink persistent lock inodes. Group a recognized temporary database and journal only when ownership and inactivity are established; otherwise list them as protected and explain manual follow-up. Never use age or PID text as proof of inactivity. Support partial outcomes and idempotent retries without widening the selection.

### 4. Reconcile rather than duplicate older owners

Use the finding table in `sources.md`. Run existing coverage, explain, lineage and ranking/projection contracts first; record each finding as reproduced, covered by fresh evidence, unresolved or explicitly deferred. Current source branches and checked umbrella tasks alone do not establish acceptance. Add residual fixes to the existing owner and link their evidence here. Broad all-term relaxation, split databases and global lineage deduplication are suggestions, not prerequisites. Explain existing `any`/minimum-segment options and retain current query semantics.

## Risks / Trade-offs

- Full content verification still reads the source population → measure hashing separately and avoid promising constant-time freshness.
- Database copy and global derived-table work may dominate update → before extending the implementation, use a portable large fixture with at most 1% changed modules. Require equal lexical outcomes, extraction reuse, and at least 30% lower median wall time than full rebuild over five alternating pairs. Retain all samples; this is a proposed acceptance gate, not a known result or a CI timing assertion. If unmet, stop the optimization batch with an explicit deferred outcome; do not relax the gate after measurement.
- Concurrent editors can prevent a stable snapshot → one bounded attempt, clear retry guidance and no rebuild loop. Record any inability to obtain stable external evidence.
- Cleanup can race with new publishers → hold and revalidate destination ownership during deletion; refuse uncertain files. Persistent lock files can remain after reclaiming large databases.
- A schema change may prove necessary → version it and require rebuild of incompatible indexes; never modify old metadata to simulate compatibility.

## Migration Plan

Ship diagnostic changes first with additive JSON and updated text snapshots. Add explicit update and lifecycle commands after their portable failure/race tests pass. Existing build/status/search commands retain their meanings. Keep the shared index usable for concurrent readers; private indexes become an isolation option with an explicit lifetime, not the default response to every stale query. Update README links, CLI reference, repo skill and `../codex-skills/ladon` guidance together.

Use 32 GiB process caps where supervised work needs them, recording actual use. For retained real-repository measurement, use a frozen copy and explicit storage budgets; a proposed 1536 MiB per-database calibration ceiling is an input to the experiment, not a raised global default. Record temporary peak disk and stop on budget failure. No build, index deletion or cleanup is performed in the concurrently edited matrix-factorization checkout by this planning task.
