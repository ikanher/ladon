# Design

## Context

See `proposal.md` for motivation. The existing explicit updater captures source identities, backs up SQLite into a private candidate, replaces changed module rows, rebuilds FTS, validates and atomically publishes. `first_retained_evidence_table` prevents this path from deleting or reassigning semantic, lineage and ProofIR records. `declarations` mixes lexical and semantic columns; binders, shapes and module semantic state use cascading foreign keys. Simply removing the guard is unsafe.

Lineage closures already retain source, configuration, toolchain and base-generation identities. The current lineage command compares them with the live project even when refresh is disabled, so merely printing an archived filename would not provide historical lineage inspection. Existing list/prune protects evidence-bearing databases. `sqlite_publication.py` supplies a persistent inode lock and fsync/replace publication. Mutation-capable lineage CLI operations already acquire that destination lock; other mutation routes need an explicit compatibility audit before integration.

Main ProofIR identity/authority specs remain authoritative. The unarchived active-index delta permits preservation or refusal; this package implements preservation for recognized layouts and keeps refusal for unknown extensions.

## Goals / Non-Goals

**Goals:** a single active index path, durable historical evidence, current lexical results equal to a clean build, explicit historical lineage inspection, deterministic bounded diagnostics and tests through ordinary CLI paths.

**Non-Goals:** rechecking proofs during update; inferring unchanged mathematical meaning from names or owner hashes; selective compiled reuse across generations; automatic builds, background watchers, history deletion, a new evidence format or canonical registration. External files referenced by an archive are not automatically copied or represented as replayable.

## Decisions

### Preserve complete database snapshots before changing lexical ownership

Use an adjacent `<index-filename>.history/` directory, including for explicit external index paths. Before a supported evidence-bearing update, take a consistent SQLite backup under destination ownership, checkpoint the private backup into a standalone database, validate it, compute its byte digest and publish it as `<sha256>.sqlite`. Do not byte-copy a live WAL database or hard-link the mutable active file.

Keep an internal versioned history catalog in the active candidate. Each entry names snapshot digest, relative path, bytes, original repository/generation/schema identities and evidence inventory. The catalog travels atomically with the active database; there is no second mutable current-pointer file. Carry prior entries forward without recursively duplicating their database files. Generation identity alone is not the archive key: more evidence can be ingested under unchanged sources. Identical verified snapshot bytes can reuse an existing archive; never overwrite a conflicting file.

This keeps original declaration/evidence relationships intact. Retrofitting generation keys into every semantic and ProofIR table would require a much larger owner migration. Separate manually managed indexes remain the fallback for unknown layouts.

### Keep the new active population strictly lexical

Prepare the new active candidate from the supported schema and lexical extraction data, reusing unchanged lexical material. Do not copy elaborated signatures or semantic authority flags into lexical declarations. Where semantic ingestion overwrote lexical fields and the original lexical projection cannot be recovered, re-extract that module from the observed source even if its bytes are unchanged; report this work separately rather than claiming extraction reuse. Preserve all retained evidence in the snapshot first; clear/reinitialize active semantic, lineage and ProofIR evidence using explicit owner-defined handling, not a wildcard drop of tables. Preserve configuration without claiming that cataloged external files were freshly validated. Use clean-build lexical projection parity as the oracle, independent of history metadata.

Inventory every supported evidence table/column before enabling migration. Unknown evidence tables, schemas or external authority requirements produce a full-build-to-new-path recommendation and leave the original untouched. Unchanged compatible source and configuration identities preserve the existing no-op: no replacement, archive or Lean invocation. A missing base is not a no-op.

### Expose history with small additive CLI surfaces

Planned interface (not currently implemented):

- `proof-search index update`: existing spelling; additionally reports preserved snapshot IDs, retained-history bytes and current-evidence association.
- `proof-search index history`: bounded listing at the selected `--index`, with snapshot identity, original generation, bytes, inventory and integrity availability; default limit 100, maximum 1000, continuation information when truncated.
- `proof-search theorem lineage ... --history SNAPSHOT_ID --refresh never`: selects an exact registered snapshot, validates its digest and opens it read-only. Reject any mutation-capable refresh policy with `--history`. The history selector bypasses only live-project selection, never stored record validation. Projection uses the archived base identity, retaining any stale/missing association already present in that archive; it must not fabricate identity from the chosen closure to make it fresh.

Historical output states `selectionBasis: historical-snapshot` and `currentAssociation: not-established`, identifies both the archive and original observation, and preserves the existing receipt guarantees. It can render without a live Lean environment. Implement this through the existing lineage projection owner plus an explicit historical selection context. Do not turn current-mode `fresh` into a label for historical availability. Use a separately versioned historical wrapper if existing result enums cannot represent this additively. Exact field/schema choices are frozen with red CLI fixtures before runtime edits.

Other supported evidence remains intact in the snapshot and accessible to existing offline owners where supported. Do not claim every command becomes an offline history viewer. New broad historical semantic search is outside this package.

Current search never consults archives for candidate signatures or authority. Status distinguishes lexical comparison from stored evidence and compiled association. Acquiring new evidence uses existing explicit commands and checks. Successful acquisition does not rewrite old snapshots; unsuccessful acquisition cannot select history as current by default.

### Publish the archive before publishing the active generation

Under the same destination lock: inspect compatibility; capture sources; create/validate/fsync/archive the consistent base if needed; construct and validate the active candidate with all history references; recheck source and base ownership; publish with the existing durable replacement owner. Use relative history paths confined to the selected history root; reject symlinks, traversal and substituted files. Snapshots are read-only by Ladon policy and verified by content, not trusted because of a filename or mode bit.

Before the replacement linearization point, failure leaves the old active database unchanged. After replacement, a directory-fsync failure has uncertain durability: report publication uncertainty and inspect identities on recovery rather than claiming rollback. A crash can leave an unreferenced complete archive or a private temporary; inventory reports it as protected/uncertain. Never adopt a partial archive, infer completion from filenames, delete an uncertain artifact automatically, or unlink persistent locks.

All supported writers must serialize against this operation and reject writes to historical selections. Audit semantic and ProofIR entrypoints as well as lineage. Legacy raw SQLite access is not a public contract. Existing readers can finish on one complete old generation while later readers open the new one.

### Preserve history across the whole lifecycle

Bump the private schema/layout identity and add strict schema checks to affected readers and writers. Recognize the current supported pre-history layout for explicit update migration. Older runtimes must reject the new active schema; retained snapshots preserve their original schema. Full build over a history-owning active path must refuse with a new-path instruction until a preservation-aware replacement path exists. This prevents a later build from silently losing the catalog.

Extend status/list to report active and history bytes with clear bounded-total scope. History snapshots and catalogs remain protected from ordinary prune even when manually selected or old. Do not add history deletion in this package. A moved active file with missing history reports missing history, never empty history; current lexical inspection may still work, but preservation-requiring mutation refuses broken references. Moving the index and its adjacent history together preserves relative navigation, while original repository identities remain historical facts.

Retain the existing active-index size policy. Report archive bytes and peak temporary disk; enforce an explicit optional history ceiling when supplied (proposed `--max-history-mib`, no silent eviction). Without a history ceiling, actual disk/write failures remain terminal. Recheck sizes after writing; free-space estimates alone do not guarantee publication. No change to the 32 GiB process cap.

### Use TDD around the public contract and failure boundaries

The current refusal is a passing characterization, not the new desired behavior. Record it first. Add a schema-valid mixed-evidence fixture and public tests that fail because supported update/history selection is absent. Keep unknown-layout refusal tests. Explicitly supersede only known-evidence refusal assertions with stronger preservation assertions, retaining the original tests and red logs in evidence.

For each implementation slice, record the failing assertions against the pre-change candidate, implement the minimum owner change, make the same assertions pass, then refactor under those tests. Test stable IDs, row/payload equality, detached source references and current search output, not private helper call counts. Use real SQLite for ownership and integrity tests and deterministic process barriers for races; mock only fault boundaries. Include at least one actual Lean-acquired lineage fixture before acceptance, so synthetic shape validity is not mistaken for runtime evidence.

## Risks / Trade-offs

- Snapshot cost → measure archive, candidate-copy and search-projection phases separately. Do not claim speedup solely from extraction reuse. Deduplicate only verified identical snapshot bytes; no automatic archival on every lexical edit.
- Hidden evidence ownership → before enabling migration, inventory all retained columns/tables and execute a bounded feasibility slice: one valid mixed-evidence base, one source delta, unchanged archived records and clean-build lexical parity. Keep the current refusal if this requires rewriting canonical or checker semantics; return for design review rather than quietly narrowing preservation.
- Writer races → test lineage/semantic/ProofIR mutation versus update through supported entrypoints. A missing lock owner is a blocking defect, not a reason to relax preservation.
- Historical freshness accidentally upgraded → separate selection context and current association; same-name/changed-type and changed-import controls must fail closed. Do not infer applicability from unchanged owner bytes.
- Growth and uncertain publication → report full disk costs, honor declared ceilings, preserve evidence on failure and protect orphaned snapshots. Explicit history deletion remains follow-up work.
- Real-project concurrency → exercise disposable copies of the Adam fixture; do not build or mutate the shared matrix-factorization checkout. No speed target is asserted yet: the primary gate is safe usable update. Preserve all timing samples, including poor results, before judging further optimization.

## Migration Plan

1. Freeze owner inventory, CLI contract and red tests against the current commit; preserve existing refusal/authority controls.
2. Implement archival publication and current lexical isolation, then historical read selection and lifecycle protections through successive TDD slices.
3. Exercise legacy migration, unsupported schemas, source mutation, interruption, reader/writer overlap and missing/corrupt archives. Retain rollback access through the original snapshot and compatible runtime; restoring it is an explicit operation, never automatic evidence rebinding.
4. Qualify affected installed contracts on supported Python runtimes, run strict maintained checks and the disposable real-workflow replay. Record candidate/package identities and actual resource costs.
5. Update CLI/index docs and skill; bump package version after implementation is complete and qualify the final versioned candidate. Close with a source-first delta review of implementation and evidence if authority/storage changes need pro review. Do not claim qualification at the planning stage.
