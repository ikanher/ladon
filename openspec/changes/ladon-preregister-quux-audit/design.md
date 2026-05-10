# Design

## Planned Runs

1. Project-level architecture run:

   ```bash
   bin/ladon --repo-root /home/codex/projects/quux --root Quux --skip-build
   ```

2. Owner-level declaration run:

   ```bash
   bin/ladon --repo-root /home/codex/projects/quux \
     --root Quux/Semantics/Propagation.lean \
     --extraction-backend lean --lean-extraction-scope root
   ```

## Pre-Registered Predictions

### Project-Level Quux

- The module graph should be acyclic.
- Module count should be approximately `370`, with most modules under
  `Quux/Problems`, `Quux/Semantics`, and `Quux/Bridge`.
- `Quux.Basic` should be the dominant in-repo fan-in hotspot.
- `Quux.Problems`, `Quux.Semantics`, and `Quux.Bridge.Example.Core` should be
  top fan-out surfaces.
- Project-level findings should include facade/fanout or umbrella-style
  architecture pressure.
- The `Quality Baseline` section should make `Quux.Basic` a top percentile
  module fan-in outlier.

### Propagation Owner

- Declaration graph should be small, around a dozen declarations.
- `Quux.Semantics.PropagationAlgebra` should be a declaration fan-in hotspot.
- The unresolved-reference surface should include parser/name-resolution noise
  around names such as `Edge` and local field names.
- The owner root should show root-scope pressure because it is a narrow owner
  inside a broad inventory.
- Proof-family similarity candidates are not expected for this small owner.

## Falsification Conditions

- No quality baseline appears in either report.
- `Quux.Basic` is not near the top module fan-in surface.
- `Quux.Problems`/`Quux.Semantics` do not appear as broad fan-out surfaces in
  the project-level run.
- The Propagation owner yields a large repeated proof-family surface.
