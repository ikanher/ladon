## Design

### Goal

Make Ladon easier to evolve by separating side-effectful orchestration from
pure analysis kernels, then recording where time is spent in a stable way.

### Non-Goals

- Do not rewrite Ladon in Rust in this packet.
- Do not replace the existing CLI or report formats.
- Do not optimize before instrumentation shows where optimization matters.
- Do not broaden the analyzer's theorem-quality heuristics in this packet
  except where needed to route existing module graph analysis through the new
  seam.

### Pipeline Model

Introduce an internal pipeline surface with named phases:

- `discover`: resolve repository root, root files/modules, and options.
- `lean_extraction`: invoke Lean/export helpers or load existing extraction
  data.
- `indexing`: normalize extracted modules/declarations into stable Python IR.
- `module_dag`: run pure module dependency graph analysis.
- `declaration_graph`: prepare declaration-level graph facts when available.
- `witness_audit`: inspect witness metadata when requested.
- `openspec_audit`: inspect OpenSpec/OpsX metadata when requested.
- `findings`: convert analysis facts into findings.
- `rendering`: write text/JSON reports.

The first implementation can be lightweight: dataclasses plus a timing helper
are enough. The important part is that tests can assert which phases ran and
which keys appear in the result.

### Data Boundaries

Use small stable data objects:

- `RunContext`: repository root, requested roots, options, output paths,
  warnings, and a phase timer.
- `PipelineResult`: normalized modules, analysis summaries, findings, report
  paths, warnings, and timing metadata.
- `PhaseTiming`: phase name, elapsed seconds, status, and optional counters.

Pure analysis modules should accept normalized IR such as `LeanModule` and
return plain Python data. They should not inspect the filesystem, invoke Lean,
or render reports.

### Compatibility Strategy

The current Ladon implementation remains the operational source of truth during
the transition. This packet should add adapters around legacy extraction data
instead of forcing a full rewrite. Report changes must be additive:

- Existing text report sections remain available.
- Existing JSON consumers keep their old keys.
- New timing data appears under a clearly namespaced key such as
  `pipeline.timings` or `metadata.pipeline_timings`.

### TDD Strategy

Tests should avoid brittle wall-clock assertions. They should check:

- required phase keys are present,
- phases report nonnegative elapsed times,
- phase status is explicit,
- legacy module data can be adapted into `LeanModule`,
- module DAG analysis is shared between the CLI path and pure analysis tests,
- existing CLI smoke behavior still runs.

### Risks

- Timing values are noisy. Tests must assert shape and invariants, not exact
  durations.
- A partial pipeline refactor could produce two competing sources of truth.
  Keep adapters thin and route existing module graph logic through
  `analysis.module_dag`.
- Report churn could break external users. Add new fields without removing or
  renaming existing fields.

### Validation

Expected validation commands:

```bash
uv run pytest -q
uv run python -m compileall -q src tests
uv build
bin/ladon --root /home/codex/projects/quux /home/codex/projects/quux/Quux/Semantics/Propagation.lean --json /tmp/ladon-quux-propagation.json --text /tmp/ladon-quux-propagation.txt
```
