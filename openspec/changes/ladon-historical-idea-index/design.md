# Design

## Context

See proposal.md. The current private schema is v6. `proof_search_index_update` clears active semantic projections after archival; it is unsuitable for a metadata-only migration. Declaration rows are replaced on source changes. Schema-layout validation currently accepts v5/v6. Source generation and lineage identity currently include the schema generation.

## Goals / Non-Goals

Preserve all existing proof records and support backward historical audits with honest attribution. No automatic priority inference, scientific dating guesses, new proof claims or shared-index rebuild. Qualify first on fixtures and independent SQLite backups of real indexes.

## Decisions

1. Add normalized historical tables rather than nullable date columns on every declaration. One declaration can implement multiple ideas; one idea can have disputed dates.
2. Store year intervals with year/decade/range/unknown precision. Expose `idea_year` and `guess_of_the_decade` through SQL projections. Selection requires review, but review is historical metadata, never Lean authority.
3. Store durable declaration correspondence separately from current bindings. Resolve package/module/name plus SHA-256 of the indexed statement; missing, changed and ambiguous matches remain explicit. Catalogue rows survive module deletion/reinsertion.
4. Use repository-root `ladon-ideas.json` as the authored catalogue. Its input identity is separate from proof inputs. Build ingests it; explicit synchronization updates history without clearing semantic evidence; ordinary source refresh rebinds links. Missing files do not silently delete retained annotations.
5. Introduce physical schema v7 while retaining v6 proof-input identity semantics for this additive extension. Change only physical schema metadata during migration. Existing lineage identities must still compare against the same evidence schema; adding historical tables is not a change to a theorem's environment. Freeze this with before/after lineage queries.
6. Implement migration with SQLite backup, existing publication locking and durable replacement. Do not call the lexical updater. Validate the pre-existing layout before migrating. New historical graph validation uses topological cycle detection; no date-based inference of edges.
7. Metrics compare streamed canonical row digests for every old table and selected deterministic query observations. Additive new tables are allowed; old content changes fail. Retain per-table results, not only an aggregate score. Include deletion, same-count swaps, authority promotion, unexpected metadata, cycle and interruption controls.

## Risks / Trade-offs

- Schema identity affects lineage freshness → separate physical and unchanged proof-input identity explicitly; exact fixture lineage checks must pass.
- Attribution links can drift → durable selectors plus statement fingerprints and unresolved statuses.
- SQL constraints cannot alone prove source truth → distinguish structurally valid, reviewed attribution from actual theorem verification.
- Large indexes → stream row digests; measure independent backups within a 1 GiB per-file starting fixture size. Do not mutate shared matrix-factorization indexes during qualification. Review size ratios above 1.10 and warm query median ratios above 1.25; sub-millisecond noise is reported separately. Preservation losses always block.

## Migration Plan

Freeze commit/status and metric red/green evidence; complete this packet; implement bounded tests and migration; qualify on fixture and real-index copies; run affected regressions and scoped quality checks. Publish code only after zero preservation loss. Retain original database backups. If repair cannot achieve the contract, restore only files created/changed by this task, preserving unrelated work and the diagnostic report.
