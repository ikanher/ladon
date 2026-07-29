# `ladon-theorem-capsule-materialization`

Consumes a valid plan and publishes a deterministic, path-safe, fully inventoried
locked/rebuildable module-prefix capsule outside the analyzed repository.

- Dependencies: completed `ladon-theorem-capsule-planning`, source/configuration
  fingerprints, module/source-root mapping, and filesystem safety contracts.
- Enables: independent Lean replay from a fixed capsule manifest and byte set.
- Excludes: dependency rediscovery, imported-module declaration slicing, source
  rewriting, implicit downloads, offline vendoring, or a verified status.
- Exit: portable fixtures preserve the owner prefix and multi-root import layout,
  account for every byte, reject drift and path attacks, leave targets unchanged,
  and reproduce directory/archive identities.
