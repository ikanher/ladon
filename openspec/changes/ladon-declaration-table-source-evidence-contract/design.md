## Context

Current clean-core reports may omit explicit declaration rows. The ProofIR
bridge derives declaration rows from graph edges, chosen roots, and fan tables
when necessary, which only supports medium or low confidence joins. The next
stable seam is an explicit declaration evidence table that remains source-level
and conservative.

## Goals / Non-Goals

**Goals:**

- Emit explicit declaration rows when declaration extraction is available.
- Attach source path, range, selection range, content hash, backend, extractor
  version, name-resolution method, and confidence.
- Preserve additive report compatibility.
- Upgrade ProofIR join precedence using source evidence.

**Non-Goals:**

- Do not claim elaborated proof dependencies.
- Do not make text extraction produce declaration semantics unless a test-backed
  source exists.
- Do not validate ProofIR authority or theorem truth.
- Do not remove derived-row fallback from the bridge.

## Decisions

1. Add source evidence to `LeanDeclaration` or an adjacent report row type.

   The IR can carry optional fields from the Lean helper while preserving tests
   that construct minimal declarations.

2. Hash source content at the CLI/extraction boundary.

   Content hash belongs to source attachment and cache invalidation. The hash
   should be deterministic and tied to the exact file content used for
   extraction.

3. Use explicit confidence labels.

   Suggested labels are `source_hash`, `source_range`, `module_decl`,
   `basename_only`, and `none` for joins, with extraction-side confidence
   labels such as `parser_source_range` and `derived`.

4. Keep bridge trust rules unchanged but more visible.

   Better joins establish attachment confidence. They do not establish proof
   correctness, witness adequacy, or artifact authority.

## Risks / Trade-offs

- Report schema drift -> Keep all fields additive and versioned by report
  version or row method.
- Lean helper version drift -> Include extractor version and backend fields.
- False confidence -> Render confidence and non-claims near bridge diagnostics.
- Hash cost -> Hash only files already being extracted or reported.
