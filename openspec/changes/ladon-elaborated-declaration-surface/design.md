## Context

`LeanDeclaration` currently carries names, ranges, and parser reference
candidates. The helper computes a syntax body tree that Python discards, and it
does not serialize the elaborated type or traverse elaborated expressions for
constants. As a result, the report cannot show theorem premises/conclusions or
distinguish real dependencies from lexical candidates.

## Goals / Non-Goals

**Goals:**

- Provide bounded, readable declaration and theorem statements from Lean.
- Separate type dependencies, value/proof dependencies, and parser candidates.
- Attach source navigation, hashes, authority, and truncation metadata.
- Surface direct axiom/sorry/unsafe evidence without proof-truth claims.

**Non-Goals:**

- Store complete proof terms, full syntax trees, InfoTrees, or goal-state
  traces.
- Add tactic skeletons, tactic-head counts, or proof-shape heuristics already
  owned by the proof-xray lane.
- Explain or repair proofs.
- Classify theorem truth, mathematical strength, or proof quality.
- Implement before/after semantic changelogs.

## Decisions

1. **Extend a typed declaration row rather than attach arbitrary helper JSON.**
   The row contains fully qualified name, declaration kind, module, source
   range/hash, backend/toolchain identity, and distinct optional surface
   namespaces. Keeping raw dictionaries was rejected because report v2 needs a
   stable schema.

2. **Derive statement structure from the elaborated type.** The helper
   pretty-prints the type with recorded printer settings and decomposes leading
   `forall` binders into bounded binder/premise rows plus a conclusion string.
   Pretty text is version-scoped; it is not claimed byte-stable across Lean
   releases.

3. **Traverse elaborated expressions for direct constants.** Type and
   value/proof expressions produce separate, deduplicated constant-reference
   sets. Parser identifiers remain in a `parserCandidates` field with parser
   authority. Merging both into one graph was rejected because it would
   overclaim dependency resolution.

4. **Represent imported targets without requiring complete inventory rows.**
   A resolved imported constant may appear as a named external declaration stub
   with module/provenance. When inventory extraction supplies its full row, the
   graph joins deterministically by fully qualified name.

5. **Keep source and body metadata bounded.** The report includes a statement
   excerpt, statement/proof ranges, and proof presence/form, each with byte/row
   caps and truncation flags. Full proof source, tactic summaries, and the
   unused body tree are not serialized.

6. **Use explicit trust-footprint categories.** Declared axiom, unsafe status,
   and direct `sorryAx`/axiom references are Lean-observed rows with scope
   (`declaration`, `type`, or `value`). Transitive axiom closure is not claimed
   unless a later Lean-owned backend supplies it.

## Risks / Trade-offs

- **Pretty-printed types vary by toolchain/options** → Record both and scope
  comparisons to compatible versions.
- **Dependency rows enlarge reports** → Deduplicate, cap displayed text, and
  summarize high-volume imported targets while retaining counts.
- **Source ranges differ between syntax and environment metadata** → Preserve
  both origins when they disagree and emit attachment confidence.
- **Trust rows are read as correctness verdicts** → Use explicit authority and
  nonclaim text in schema and rendering.

## Migration Plan

Version the helper payload, extend Python IR with optional fields, add report-v2
serialization, then enable the fields for root extraction before inventory.
Older helper payloads normalize to unavailable surface fields. Rollback can
disable the new fields without changing module analysis.

## Open Questions

None. Implementation SHALL choose conservative, finite, versioned excerpt and
dependency caps with focused size tests. The downstream benchmark packet may
propose tuned caps later without blocking this child.
