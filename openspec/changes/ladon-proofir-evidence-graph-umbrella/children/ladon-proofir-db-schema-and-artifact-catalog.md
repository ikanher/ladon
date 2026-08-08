# `ladon-proofir-db-schema-and-artifact-catalog`

Adds constrained configured-artifact identity, relationships, diagnostics, and
coverage to the existing project-local proof-search database.

- Starts after: no new child; reuses current proof-search lifecycle owners.
- Enables: every semantic ProofIR adapter and attachment packet.
- Excludes: semantic interpretation, raw payload storage, and unconfigured scans.
- Exit: TDD schema/configuration, constraints, indexes, limits, atomic failure,
  and unchanged two-build reproduction pass.
