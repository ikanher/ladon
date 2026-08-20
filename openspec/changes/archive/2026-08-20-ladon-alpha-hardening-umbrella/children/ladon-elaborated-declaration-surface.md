# `ladon-elaborated-declaration-surface`

Owns Lean-backed declaration statements, binders/premises/conclusions, bounded
source navigation, distinct parser/type/value dependencies, imported stubs, and
direct axiom/sorry/unsafe facts.

- Dependencies: report v2 and Lean extraction runtime.
- Enables: later theorem changelog, Review Radar, and proof-xray work without
  duplicating extraction.
- Excludes: theorem truth, complete proof terms, goal states, tactic advice, and
  before/after comparison.
- Exit: tracked real-Lean fixtures achieve required field/dependency coverage
  while staying bounded and authority-correct.
