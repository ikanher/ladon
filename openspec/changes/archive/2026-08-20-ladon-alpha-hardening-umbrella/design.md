## Context

The audit found a useful fast text analyzer and disciplined evidence boundary,
but also six classes of alpha risk: known signal defects, ambiguous CLI
semantics, unbounded Lean execution, a shallow declaration model, a drifting
report schema, and a clean-checkout failure. The OpenSpec inventory itself also
overstates the backlog because implemented and superseded changes remain active.

The product boundary is the ordinary documented CLI surface. People, scripts,
CI, and models use the same public commands with the same defaults and receive
the same report model. A machine-readable rendering is not a separate analysis
product.

## Goals / Non-Goals

**Goals:**

- Give every in-scope alpha technical risk one implementation owner and one
  measurable exit condition.
- Land correctness and contract foundations before promoting deeper Lean data.
- Bound target-code execution, cache behavior, report growth, and failure modes.
- Make a clean exported checkout the authority for tests and packaging.
- Leave a small, truthful OpenSpec backlog.

**Non-Goals:**

- Add new heuristic families, caller-specific thresholds, or model-oriented
  commands.
- Build a UI, daemon, MCP-only route, prompt renderer, or agent protocol.
- Prove theorem truth, synthesize proofs, or apply refactorings.
- Pull Review Radar, semantic changelog, or full InfoTree work into the alpha
  critical path.

## Decisions

1. **Use eight top-level implementation children plus this planning umbrella.**
   Top-level changes remain independently applicable and archivable. Short child
   briefs under the umbrella record membership and dependencies. Embedding all
   work in one task list was rejected because it would couple unrelated
   correctness, runtime, and repository gates.

   Children may archive independently. Umbrella readiness resolves each child
   by stable change ID from either `openspec/changes` or a unique dated archive,
   validates archived artifacts in an isolated temporary change root, loads the
   archived automation registry, and checks resulting canonical specs. Requiring
   every child to remain active until umbrella close was rejected because it
   defeats independent archival. For an archived child, readiness replaces its
   now-invalid active-ID `openspec validate <change>` command with isolated
   artifact validation, then executes the remaining preserved commands.

2. **Make interface parity a milestone invariant.** Public CLI entrypoints obey
   the same execution and evidence rules. Text and JSON serialize the same
   result, and no caller identity changes analysis. A specialized model command
   was rejected because it would create two products and two calibration
   surfaces.

3. **Sequence the work by authority and dependency.**

   - First: reconcile OpenSpec state and establish clean-checkout baseline gates.
   - In parallel: repair existing signals, define report v2, and define CLI
     execution semantics.
   - Next: land the bounded Lean runner on the new phase/report contract.
   - Then: add elaborated declaration surfaces.
   - Last: benchmark the stabilized signals and run the full clean release gate.

   Starting with theorem enrichment was rejected because it would add fields to
   an unstable schema through an unsafe runtime.

4. **Freeze default heuristic expansion.** Existing raw metrics may remain
   visible, but a new default finding cannot be added during this milestone
   without a separate approved change and positive/negative oracle evidence.
   This directs alpha effort toward trust rather than report volume.

5. **Preserve evidence authority.** Text observations, parser candidates,
   Lean-elaborated facts, and quoted external witnesses remain distinct in every
   child. Neither ranking nor rendering may promote one authority class into
   another.

6. **Treat external repositories as observational smokes.** Portable fixtures
   are required gates. Quux, matrix-factorization, and mathlib runs may inform
   thresholds and drift reports but cannot make CI depend on sibling paths or
   moving module counts.

## Risks / Trade-offs

- **Broad milestone stalls on one child** → Each child is independently
  applicable; the umbrella readiness state reports blockers instead of hiding
  partial completion.
- **Report/CLI changes break early users** → Mark breaks explicitly, keep
  bounded compatibility fixtures where feasible, and document migration.
- **Clean gates expose unrelated historical drift** → Reconciliation runs
  before repository-wide OpenSpec validation becomes mandatory.
- **Lean runtime work expands into a proof platform** → The declaration child
  has bounded fields and explicit post-alpha deferrals.

## Migration Plan

1. Apply state reconciliation and clean-source fixes without changing analyzer
   output.
2. Land signal fixes and report/CLI contracts with compatibility documentation.
3. Replace the Lean runner and invalidate old cache entries by version.
4. Add declaration fields under report v2.
5. Establish benchmark baselines and require all umbrella gates.
6. Mark the umbrella complete only when every child is complete and strictly
   valid.

Rollback is child-local: retain the previous report adapter and disable the new
Lean backend path while preserving corrected text signals and repository gates.

## Open Questions

None. Report-v1 compatibility expires after exactly one published v2 alpha.
Until the project owner grants a license, publication remains blocked without
preventing the alpha technical gate or local distribution smoke from closing.
