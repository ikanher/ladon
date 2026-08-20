## Context

The theorem CLI already offers `plan`, `materialize`, `replay`, and `extract` with
shared format/output and resource options. Lineage should be another ordinary
theorem operation and should reuse those execution/error contracts.

## Goals / Non-Goals

**Goals:** one theorem-name command, explicit DB and refresh behavior, bounded views,
text/JSON parity, clean streams, and actionable missing/stale diagnostics.

**Non-Goals:** no hidden model-facing mode, no default target build, no interactive
UI, no implicit lexical fallback, and no DOT contract in the first release.

## Decisions

### 1. Add `ladon theorem lineage THEOREM`

Options are `--repo-root`, `--index`, `--view graph|routes|spines|tree|bottlenecks`,
`--from trust|project|external|package|declaration`, repeatable `--root`,
`--edge-kind type|value|all`, `--include-generated`, `--max-depth`, `--max-nodes`,
`--max-edges`, `--max-routes`, `--refresh missing|stale|always|never`, existing
theorem planner timeout/RSS limits, `--format text|json`, and `--output PATH|-`.

### 2. Make database reuse the default

Default refresh is `missing`: use a compatible stored closure; if absent, run the
existing supervised theorem planner and ingest it. A stale closure fails with a
specific instruction unless `--refresh stale|always` is selected. `never` performs
no Lean/Lake process. Refresh execution is reported on stderr/progress and in JSON.

### 3. Keep one versioned envelope

JSON contains schema/version, operation, theorem, index and closure identities,
freshness, authority, query parameters, bounds, selected nodes/edges/routes,
projection metadata, omissions, truncation, timing split, and nonclaims. Text shows
the same target/status followed by compact source-linked paths and summaries.

### 4. Reuse established process behavior

Argument errors return 2, operational/index/planner failures return 1, and completed
bounded queries return 0 even when truncated. Partial reports are not written as
successful lineage. Signals supervise and reap any planner helper process.

### 5. Guard all output dimensions

The query caps and existing report-byte cap apply before serialization. Text never
prints the full dense graph by default; `routes` is the ordinary view. JSON `graph`
still obeys node/edge/byte caps and identifies omitted populations.

## Risks / Trade-offs

- [Default missing refresh surprises users with Lean startup] → Describe it in help,
  show progress, provide `--refresh never`, and never run a target build.
- [Many options obscure the common case] → Keep defaults useful and group advanced
  filters in help while retaining one command.
- [Text and JSON diverge] → Render both from one typed result and test parity of
  identities, counts, roots, omissions, and truncation.
- [The term tree overclaims structure] → Help and output call it a bounded DAG
  unfolding with shared-node references.

## Migration Plan

Add the subcommand without changing existing theorem operations. Documentation and
skills switch to it only after installed-wheel tests pass. Rollback removes the
subcommand; stored private tables remain disposable.

## Open Questions

- Whether `--refresh missing` should become `never` after local indexes routinely
  contain Lean dependency evidence; calibrate before changing the initial default.
