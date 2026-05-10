# Design

## Evidence Checks

The first slice inspects file names and lightweight text markers:

- metadata/manifest files;
- witness JSON or artifact JSON files;
- checker scripts;
- positive/negative test files;
- verification command files or scripts;
- Markdown/source references to Lean/theorem/owner surfaces.

Each check produces a pass/fail row and example paths. The aggregate score is a
completeness score, not a validity score.

## CLI Integration

`--packet-dir` becomes an additive, repeatable flag. Normal module-DAG analysis
still runs; packet evidence is added to the JSON/text report when packet
directories are provided.
