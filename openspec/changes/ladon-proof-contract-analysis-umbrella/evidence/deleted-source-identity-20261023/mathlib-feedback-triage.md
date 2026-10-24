# Mathlib navigation feedback, 2026-10-24

Source: `../lean/matrix-factorization/temp/ladon-mathlib-feedback-r01/README.md`.
This feedback comes from a pinned Mathlib proof-port session. Its lexical index
built in 69.909 seconds with 55.8 MiB sampled process-tree peak RSS; its separate
direct Lean declaration check peaked at 3,591.65 MiB. These are different
workloads and neither measures the full Ladon strict test suite.

## Reproduced and addressed here

- The source index included `where measurable` in the lexical signature of
  `MeasureTheory.measurePreserving_piCongrLeft`. A local index built from the
  cited source excerpt reproduced the defect. The root-level `where` scanner
  now ends the signature even when `where` shares the header's line. An indexed
  regression failed before the change and passed afterward. The cited excerpt
  now yields a signature ending at `(Measure.pi μ)`.
- The lexical extractor identity moved from v4 to v5. A second regression
  verifies that a v4 index containing the stale signature is reported stale and
  `index update` re-extracts the module without a source edit. The existing v3
  recovery path remains supported. Focused scanner/index/recovery checks: 27
  passed. Full strict qualification is recorded separately.
- Build `counts.moduleImports` counts parsed import sites, while status
  `counts.module_imports` counts unique `(source, target)` rows. The insert uses
  `OR IGNORE` and the table has a unique primary key. A duplicate-import fixture
  produced build=2 and status=1. The reported 36,302 versus 36,226 is thus
  compatible with 76 duplicate sites. This distinction is now documented.

## Remaining work

1. Generated declaration coverage: `ge_of_tendsto` is available in the pinned
   Lean environment but absent from the source-only exact-name population.
   Design an optional compiled-name lookup or enrichment with explicit module,
   toolchain, source revision, generated-name authority and resource bounds.
   Keep source navigation available without Lean.
2. Full type context: a lexical header omits section variables and inferred
   instances. Expose this limitation in query output and offer a separately
   attributed, cached elaborated type for a selected candidate. Never promote
   the source snippet to a checked full type.
3. Dependency navigation: make named, revision-bound companion indexes reusable
   across projects, preserving explicit read-only index selection.
4. Query guidance: make invalid module scope and zero scoped population salient,
   and provide a bounded broader search suggestion. Keep lexical and semantic
   evidence distinct, with a compact projection for agent navigation.

The source-only index cannot establish that a declaration is absent from Lean.
The feedback did not benchmark semantic candidate checking or prove that the
proposed navigation changes improve proof completion.
