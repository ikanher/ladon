# Design

Keep the predicate system simple:

- `live` remains the default suite for existing preregistration reports.
- `root-matrix` targets the maintained matrix output layout.
- `review_region_present` checks region kind and minimum signal count.
- `root_scope_classification` checks the classification embedded in the
  `root_scope_pressure` finding.

The suite intentionally checks representative signals, not every report row.
This makes the gate stable while still catching regressions in the signals that
matter most: Quux project pressure, Quux Propagation cleanliness, MF BIFR
proof-family pressure, and context-vs-pressure region labels.
