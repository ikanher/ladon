## Context

The four implementation packets create a new path spanning Lean helper execution,
the repository-local DB, recursive SQL, a bounded pure projection step, and the
installed CLI. Acceptance needs portable authority plus observational large-project
evidence.

## Goals / Non-Goals

**Goals:** end-to-end deterministic fixtures, query-plan and integrity gates,
separate timing measurements, source-linked quality checks, and synchronized docs
and skills.

**Non-Goals:** no sibling checkout as a mandatory CI fixture, no hard-coded theorem
recommendations, no universal latency claim, and no benchmark-generated DB commit.

## Decisions

### 1. Build a portable lineage fixture repository

Include a chain, diamond, shared axiom, type-only axiom, value-only axiom, external
frontier, compiler-generated node, mutually recursive/SCC helper case where Lean
permits it, and a theorem with no declared axiom. Generate an authoritative theorem
plan through the existing fixture helper, ingest it, and assert SQL/projection/CLI
results without hand-writing a contradictory second graph.

### 2. Test every failure boundary

Cover missing index, v1 schema, missing closure, stale source/config/toolchain/helper,
partial plan, checksum mismatch, dangling endpoint, failed transaction, depth/node/
edge/route/report caps, timeout, interruption, and corrupt DB. Each case asserts the
prior valid generation survives where applicable.

### 3. Calibrate on Quux and Matrix-Factorization observationally

Use the existing Quux CDC theorem to compare known `Classical.choice` and `propext`
spines. Select at least two fully qualified Matrix-Factorization theorems by indexed
declaration evidence, not hard-coded product logic. Record closure size, DB growth,
ingestion, warm SQL, projection, and full CLI latency with fingerprints.

### 4. Gate result quality without pretending to prove mathematics

Require returned paths to be edge-valid, start at selected roots, end at the exact
target, retain type/value kinds, and source-link all project-owned declarations for
which source evidence exists. Human usefulness observations remain separate from
semantic fixture assertions.

### 5. Synchronize public guidance

Update README/CLI docs and the authoritative `codex-skills/ladon` skill. Teach status
and DB lifecycle, refresh behavior, common lineage command, filters/caps, and the
actual-dependency-versus-alternative-proof nonclaim. Add stale-command scans.

## Risks / Trade-offs

- [Real checkout changes invalidate measurements] → Record repository/toolchain/
  source/closure fingerprints and label results observational.
- [Benchmark encourages hard-coded thresholds] → Keep portable generous gates and
  report real-repo distributions rather than a single pass/fail number.
- [Docs drift from help] → Assert maintained command fragments against parser help
  and scan active examples for removed flags.
- [Generated DB bloats git status] → Keep `.ladon/index/` ignored and verify no DB is
  tracked.

## Migration Plan

Land this packet last, rebuild disposable local indexes, run the full acceptance
matrix, then publish docs/skill examples. Rollback removes generated calibration
artifacts and documentation references without touching Lean repositories.

## Open Questions

- Which Matrix-Factorization theorem sizes best represent small, medium, and large
  closures after the first indexed sampling run.
