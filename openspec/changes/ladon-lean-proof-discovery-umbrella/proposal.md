## Why

Ladon's architecture reports help reviewers locate proof surfaces, but active Lean
work still falls back to name guessing and repeated compiler failures when the
needed declaration, adapter, or constructor field is unknown. The concrete
acceptance cases in `TODO.md` justify a dependency-ordered proof-discovery program
that uses elaborated Lean evidence without presenting heuristics as compiled proofs.

## What Changes

- Introduce a persistent, freshness-labeled elaborated declaration index and
  explicit proof-search scope contract.
- Add type-directed and semantic declaration search with substitutions, imports,
  source locations, theorem-family grouping, and honest fallback labels.
- Explain why candidates fail to apply, route unmatched premises through existing
  declarations and advisory adapters, and preserve accepted/rejected route cards.
- Add reverse consumer search, structure-field coverage, and certificate-leakage
  checks for constructor work.
- Capture local goals from scratch files and emit isolated application probes.
- Let repositories declare representation, scaling, and parameter-range relations
  that affect candidate validity.
- Export declaration-level proof frontiers and revision diffs into review packets.
- Repair and maintain the CLI/documentation/skill contract for ordinary proof work.

## Capabilities

### New Capabilities

- `ladon-proof-discovery-cli-contract`: Maintained caller-neutral proof-search CLI,
  report-version, documentation, and skill examples.
- `ladon-lean-proof-search-index-and-scope`: Versioned Lean-aware local index,
  freshness contract, transitive scope selection, and omission evidence.
- `ladon-type-and-semantic-declaration-search`: Elaborated type-pattern search and
  combined fuzzy name, documentation, namespace, and signature search.
- `ladon-premise-difference-and-adapter-routing`: Candidate application differences,
  premise discharge routes, and advisory adapter suggestions.
- `ladon-declaration-consumers-and-constructor-coverage`: Reverse consumers,
  structure-field coverage matrices, and certificate-leakage diagnostics.
- `ladon-goal-capture-and-application-probes`: Lean goal/context capture and isolated
  candidate application examples.
- `ladon-proof-representation-and-scale-awareness`: Repository-declared
  representation transports, scale checks, and parameter-range classification.
- `ladon-proof-frontier-review-output`: Review-packet frontier tables, route history,
  freshness evidence, and declaration-surface revision comparisons.

### Modified Capabilities

None.

## Impact

- Adds eight ordered implementation packets and umbrella governance.
- Extends the installed CLI, Lean helper protocol, cache/index storage, JSON rows,
  text rendering, packet evidence, fixtures, and maintained documentation/skills.
- Reuses existing module DAG, source evidence, elaborated declaration surface,
  declaration-family, theorem-surface changelog, process supervision, and packet
  authorities rather than introducing parallel proof authorities.
- Requires large-project latency and freshness gates in addition to portable
  semantic correctness fixtures.
