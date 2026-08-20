# `ladon-cli-execution-contract`

Owns the shared public CLI execution contract, default no-build behavior,
explicit build/preflight, output destinations, partial-report behavior,
`--fail-on`, and process exit classes.

- Dependencies: report v2 phase/result model and reconciliation's archived
  `canonicalized-legacy-cli-deltas` milestone; clean package smoke consumes this
  contract.
- Enables: predictable interactive, shell, CI, and model use through the same
  command.
- Excludes: report field schemas, Lean-helper protocol recovery, and analyzer
  selection algorithms. It owns the generic target-process timeout supervisor.
- Exit: installed subprocess tests prove stream discipline and exit codes
  0/1/2/3, and public help contains no caller-specific path.
