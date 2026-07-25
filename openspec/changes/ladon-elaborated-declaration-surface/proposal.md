## Why

The Lean backend currently reports declaration names and parser-level reference
candidates but drops the theorem type and computed body syntax. Ladon therefore
cannot show the proof surface a reviewer needs to understand a declaration or
separate elaborated dependencies from lexical guesses.

## What Changes

- Extend normalized declaration IR with fully qualified name, kind, source
  range, rendered elaborated type, binder/premise summary, conclusion surface,
  bounded source excerpt, and proof/body presence.
- Extract elaborated constant references from Lean expressions and keep them
  separate from parser-observed identifier candidates.
- Preserve bounded proof/body presence and source-navigation metadata, including
  truncation, instead of computing a full syntax tree and discarding it.
- Represent declared axioms, unsafe declarations, `sorry` exposure, and
  unresolved imported constants with explicit Lean/text authority and
  provenance.
- Resolve imported declaration references across the selected root closure when
  inventory data is available.
- Render compact declaration surfaces in the existing text and JSON reports
  without adding a role-specific command or explanation layer.

## Capabilities

### New Capabilities

- `ladon-elaborated-declaration-surface`: Lean-backed theorem and declaration
  surfaces with bounded source context, elaborated dependencies, and explicit
  authority.

### Modified Capabilities

None.

## Impact

- Affected code: Lean helper JSON, Python IR, normalization, declaration graph,
  proof-surface findings, report schema/rendering, atlas exports, and cache
  versioning.
- Affected tests: synthetic Lean declarations, imported dependency resolution,
  parser/elaborator disagreement, source bounds, axiom/sorry/unsafe cases, and
  absent-backend behavior.
- This child depends on the extraction runtime and report-contract foundations
  but does not make Ladon a proof checker.
