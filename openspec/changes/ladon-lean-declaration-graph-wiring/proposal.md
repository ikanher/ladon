## Why

Ladon has a pure declaration graph kernel and a Lean-native extraction backend,
but the parser-helper declaration/reference data is not yet wired into the
pipeline. The next useful step is to expose declaration graph summaries when
the Lean backend provides declaration references.

## What Changes

- Add an extraction bundle that can carry modules and declarations.
- Normalize parser-helper command reference candidates into `LeanDeclaration`.
- Add a timed `declaration_graph` pipeline phase.
- Add JSON/text report output for declaration graph summaries when available.
- Keep text backend behavior unchanged.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `ladon-lean-extraction`: Lean extraction also carries declaration reference
  facts when parser-helper output provides them.
- `ladon-declaration-graph`: The pure graph kernel is used by the pipeline when
  declaration IR is present.
- `ladon-pipeline`: Adds an optional `declaration_graph` phase with explicit
  skipped/ok status.

## Impact

- Affected code: `src/ladon/ir.py`, `src/ladon/lean_extraction.py`,
  `src/ladon/pipeline.py`, `src/ladon/render.py`.
- Affected tests: pipeline/report tests for declaration graph output.
- CLI remains compatible.
