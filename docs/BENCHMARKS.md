# Portable signal benchmarks

Ladon's required benchmark measures the installed CLI against tracked fixtures.
Run it with an explicit candidate:

```bash
uv run --locked python scripts/ladon_benchmarks.py \
  --candidate worktree \
  --required \
  --output /tmp/ladon-benchmark-results.json
```

`--candidate` is mandatory. It accepts a treeish, a materialized directory, or
the explicit `worktree` sentinel. The candidate is materialized through the
same clean-source boundary used by the release gates, built as an sdist and
wheel, installed into an isolated environment, and exercised through the
ordinary `ladon` console command. A missing candidate fails before a build or
measurement begins.

## Required evidence

The versioned manifest is
`tests/fixtures/benchmark_harness/manifest-v1.json`; its packaged schema is
`ladon/schemas/ladon-benchmark-manifest-v1.schema.json`. Required cases cover:

- text-backed structural signals, including seeded internal/external missing
  imports, generated-aware fan populations, facade and namespace behavior,
  architecture/source-pattern rows, and declaration masking;
- Lean-backed declaration surfaces through a deterministic Lake stand-in,
  including theorem, definition, axiom, opaque, unsafe, statement, direct
  type/value dependency, and parser-only negative cases;
- report-v2 schema validity, normalized byte determinism, JSON/text semantic
  parity, and explicit size ceilings;
- cold and warm runtime, peak resident memory where Linux process metrics are
  available, parser-helper launches, five cache fingerprint invalidations,
  timeout cleanup, caller cancellation, and absence of orphan descendants.

The stand-in controls subprocess and cache behavior without downloading a Lean
toolchain. It does not replace the pinned real-Lean gates:

```bash
uv run --locked python scripts/lean_runtime_gate.py --required
uv run --locked python scripts/lean_declaration_gate.py --required
```

Those gates own real batch-protocol, Lake-layout, declaration-surface, and
Lean-environment compatibility evidence. Parser candidates remain
parser-authority evidence; the benchmark never counts them as elaborated type
or value dependencies.

## Metrics and promotion

Machine output keeps correctness, coverage, runtime, memory, cache, process,
and stability families separate. It deliberately has no proof-quality,
repository-quality, model-quality, or aggregate quality score. Labeled
correctness rows report per-kind confusion counts; declaration/dependency rows
report extraction coverage; control rows retain the expected and observed
machine values.

A named promotion family is ready only when its positive,
intentional-negative, and boundary labels all exist and pass. Labels are
reviewed fixture data with rationales, not expectations copied from the
candidate's current output. Passing an oracle means Ladon reproduced that
labeled analyzer behavior. It does not establish theorem truth, proof
correctness, transitive axiom closure, or the quality of an LLM.

## Synthetic ceilings

Manifest v1 uses deliberately generous regression tripwires:

| Measure | Required ceiling |
| --- | ---: |
| cold wall time per case | 20 seconds |
| warm wall time per case | 20 seconds |
| supported peak RSS | 512 MiB |
| normalized JSON | 2,000,000 bytes |
| text report | 500,000 bytes |
| timeout/cancellation cleanup | 5 seconds |
| parser launches per inventory run | 12 |

The 2026-07-25 Linux reference run completed the largest cold and warm cases in
under 0.20 seconds, observed under 35 MiB peak RSS, emitted under 350,000
normalized JSON bytes and 9,000 text bytes, used one parser launch for a
two-module inventory, completed cleanup in under 0.5 seconds, and passed all
five invalidation cases. These observations justify broad headroom; they are
not throughput promises or exact future-output assertions. Required CI records
the current observations and fails only when a committed ceiling or structural
invariant is crossed.

## Optional live drift

Matrix-factorization and mathlib are opt-in through
`LADON_MATRIX_FACTORIZATION_ROOT` and `LADON_MATHLIB_ROOT`. Quux is never a
Ladon benchmark or drift target.
Live rows must record repository revision, toolchain, and environment
provenance. Their changing module counts and top nodes are observational drift,
never portable correctness gates.
