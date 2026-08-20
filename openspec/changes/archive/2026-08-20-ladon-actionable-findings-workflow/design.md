## Context

The live compact report omitted 73 of 88 findings and offered no installed
lookup path. This child makes existing findings navigable without adding
another smell taxonomy or rerunning analysis during inspection.

## Decisions

### Findings retain semantic identity

Stable IDs derive from kind, subject, scope, and canonical evidence identity,
not wording or display position. Severity, confidence, priority, authority, and
owner relevance remain separate fields.

### Evidence references resolve into canonical owners

Each finding links to typed source, raw-row, or aggregate evidence. When no
truthful exact location exists, it records an unavailable reason rather than a
fabricated source anchor.

### Inspection is a report projection

The ordinary installed CLI offers deterministic finding list/filter/show
operations. They consume reports or bundles, never rerun analysis or alter
thresholds. Suggested next commands are structured ordinary Ladon arguments
and remain advisory.

## Existing Owners And Exclusions

Existing finding kinds, severities, report sections, prescriptions, CLI exits,
scope plans, and ownership populations remain authoritative. This child adds no
finding taxonomy, caller-specific ranking, or natural-language query path.

## Risks

Evidence can disappear under bounded projections. Projection omissions and
unavailable reasons remain explicit, and portable gates reject dangling
references.
