## Context

The current pipeline promotes several text and graph heuristics into findings.
Reproductions show that selected-root filtering can hide an internal missing
import, generated importers inflate a table described as handwritten,
declaration detection misses ordinary Lean forms, conventional parent
namespaces are labeled drift, and coarse unresolved classes can dominate proof
family similarity. Quux output also contains duplicate fan-in findings; the
benchmark child separately owns stale live-repository calibration/drift gates.

## Goals / Non-Goals

**Goals:**

- Fix every reproduced signal defect with a minimal positive and negative
  fixture.
- Make the population and authority behind each promoted row explicit.
- Preserve raw evidence while removing misleading promotion and duplication.
- Ensure ordinary Lean declaration forms do not distort facade classification.

**Non-Goals:**

- Implement elaborated dependency extraction or compile diagnostics.
- Define project-specific namespace style.
- Add a new quality score or heuristic family.
- Make text markers authoritative for proof correctness.

## Decisions

1. **Derive internal-import scope from repository top namespaces, not the exact
   owner module.** An absent `Pkg.Missing` referenced from `Pkg.Owner` remains
   internal when `Pkg` is a discovered project namespace. Imports outside known
   project namespaces remain external. Restricting to the selected root string
   was rejected because it caused the reproduced false negative.

2. **Name and compute graph populations together.** Generic fan tables count all
   eligible modules; handwritten tables filter both endpoints and importers.
   Generated-only pressure is reported through generated-attribution rows.
   Filtering only the target was rejected because the rendered claim then
   disagreed with the count.

3. **Use a masked lexical scanner for the text fallback.** Comments and strings
   are masked while preserving offsets; declaration recognition accepts
   modifiers and the supported kinds `theorem`, `lemma`, `def`, `abbrev`,
   `instance`, `structure`, `class`, `inductive`, `opaque`, `axiom`, and
   `constant`. A full Lean parser in Python was rejected; unsupported syntax
   stays explicitly text-limited and the Lean backend remains authoritative.

4. **Model namespace compatibility instead of equality.** A declaration in the
   module's namespace or a parent namespace is conventional. Drift requires an
   unrelated namespace, conflicting dominant namespaces, or an explicit policy
   violation. Exact file/namespace equality was rejected because Lean does not
   require it.

5. **Cap coarse similarity evidence.** Unresolved-reference classes may annotate
   a pair, but high similarity requires overlap in resolved declarations or
   concrete normalized identifiers. Taking the maximum of coarse and concrete
   overlap was rejected because unrelated proofs could score 1.0.

6. **Separate measurement from promotion.** Stable keys deduplicate equivalent
   existing finding rows while raw metrics stay inspectable. This child supplies
   focused positive/negative regression evidence but does not own benchmark
   manifests, live-repository drift policy, or promotion of a new family.

7. **Label trust markers by backend.** Text-observed `sorry` and axiom
   declarations remain raw lexical review evidence; Lean-confirmed footprints
   are separate elaborated facts supplied by the declaration child. Promoting a
   new default finding requires the downstream benchmark-backed process.

## Risks / Trade-offs

- **Expanded text detection still misses Lean syntax** → Publish the supported
  declaration set and use Lean-backed extraction when semantic authority is
  required.
- **Namespace compatibility becomes too permissive** → Keep unrelated and
  multi-dominant namespace fixtures plus policy overrides.
- **Finding counts change sharply** → Preserve raw metric tables and explain
  deduplication/population metadata.
- **Existing generated-attribution packet overlaps one fix** → Reconciliation
  records this packet as the defect owner and closes the old packet only after
  its residual regression is represented here.

## Migration Plan

Land one regression at a time behind stable finding identifiers and focused
fixtures, then hand labeled cases to the benchmark owner. Rollback can revert
individual promotion corrections without reverting corrected raw extraction.

## Open Questions

None. Project-specific namespace rules remain policy data and are not resolved
in analyzer code.
