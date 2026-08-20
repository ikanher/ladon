## Context

Semantic rows must come from the loaded Lean environment and remain attributable to the requested owner module.

## Goals / Non-Goals

**Goals:** framed NDJSON v1, complete module-owned extraction, versioned fingerprints, validated partial evidence, and supervised cleanup.

**Non-Goals:** exposing helper-internal encodings publicly or accepting partial extraction as complete.

## Decisions

1. Frames are `module-start`, row variants, `module-end`, and `summary`, all carrying protocol/request/module identity.
2. The collector validates ordering, duplicates, terminal counts, identities, bounds, and completeness before producing cache artifacts.
3. `exact_expr_fingerprint_v1` alpha-normalizes structural Lean expressions; `search_shape_key_v1` indexes conclusion/premise shapes without implying definitional equality.
4. Imported declarations appear only as symbol references unless owned by the requested module.

## Risks / Trade-offs

- [Lean API instability] → isolate behind versioned helpers and a pinned integration fixture.
- [Interrupted streams] → retain validated prefixes as partial diagnostics but fail complete semantic publication.
