# Ladon Architecture

Ladon is being extracted from a single-file prototype into a tested analysis
pipeline. The rule for the refactor is TDD: add a small testable seam first,
then move logic out of the monolith.

## Target Pipeline

1. `extraction`: run the Lean parser helper and produce stable IR.
2. `ir`: dataclasses for modules, declarations, references, files, witnesses,
   review packets, and OpenSpec tasks.
3. `analysis`: pure functions over IR, with no filesystem or subprocess side
   effects.
4. `findings`: convert analysis results into review findings.
5. `report`: render JSON/text from stable report objects.
6. `cli`: orchestrate filesystem discovery, Lean subprocess calls, caching, and
   report writing.

## Current First Seam

`ladon.ir.LeanModule` and `ladon.analysis.module_dag.summarize_module_dag`
define the first extracted architecture seam.

Why this seam first:

- matrix-factorization and Quux both have clear acyclic module graphs;
- repo-wide module DAG analysis was a known Ladon blind spot;
- module DAG logic is pure and easy to test;
- it gives a useful Rust-port candidate later without touching Lean extraction.

## TDD Rules

- New architecture surfaces start with tests in `tests/`.
- Analysis modules must be pure: no shelling out, no reading arbitrary repo
  paths, no global state.
- CLI code may adapt legacy objects into IR, but analysis modules should not
  import the CLI.
- Do not port to Rust until the Python seam has stable tests and phase timing
  proves the seam is a real hotspot.

## Next Test Slices

1. Convert legacy `audit.ModuleInfo` into `LeanModule`.
2. Move repo proof-hole scanning into `analysis.proof_holes`.
3. Move OpenSpec task backlog scanning into `analysis.openspec_backlog`.
4. Move local-script/runtime-artifact provenance into `analysis.runtime_scripts`.
5. Add phase timing around extraction, indexing, analysis, findings, rendering.
6. Add cache keys for per-file Lean extraction.
