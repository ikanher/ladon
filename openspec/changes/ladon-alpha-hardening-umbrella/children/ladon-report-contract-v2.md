# `ladon-report-contract-v2`

Owns typed phase/result objects, explicit availability states, preserved
reasons, deterministic `ladon-report-v2` serialization, JSON Schema, reader
dispatch, and the bounded v1 transition.

- Dependencies: reconciliation for authoritative historical ownership and the
  clean packet's tracked-source baseline for constrained artifact inspection.
- Enables: CLI phase mapping, runtime diagnostics, and declaration extensions.
- Excludes: finding algorithms, build/extraction execution, and caller-specific
  output.
- Exit: every emitted JSON report validates, text/JSON semantics agree, and
  existing readers handle or clearly reject report versions.
