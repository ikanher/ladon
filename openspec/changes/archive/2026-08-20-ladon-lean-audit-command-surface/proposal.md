## Why

Large Lean repositories use command-only modules containing `#check`,
`#print axioms`, and resource directives as intentional review surfaces.
Current declaration-oriented analysis either misses those files or risks
misrepresenting their commands as proof authority.

## What Changes

- Extract comment-safe lexical audit-command rows for every backend.
- Optionally enrich those rows through the existing bounded Lean helper when
  the Lean backend is selected, without blocking lexical evidence when
  enrichment is unavailable.
- Classify command-only audit facades, resolve subjects where evidence permits,
  and report the mathematical owner separately from the audit file.
- Record heartbeat and recursion-depth directives with lexical scope and
  literal/normalized value while leaving finding promotion policy-driven.
- Consume explicit scopes, calibrated ownership, and partial-run diagnostics;
  reuse declaration identities and optional elaborated extraction from
  `ladon-elaborated-declaration-surface`.

## Capabilities

### New Capabilities

- `ladon-lean-audit-command-surface`: Authority-bounded audit references,
  command-only facade classification, optional subject resolution, and Lean
  resource-directive facts.

### Modified Capabilities

None. Existing declaration, source-evidence, authority, and provenance
vocabularies remain authoritative.

## Impact

- Start after `ladon-analysis-root-and-scope-contract`,
  `ladon-project-ownership-and-generated-calibration`, and
  `ladon-partial-run-observability`.
- Affected code: masked lexical extraction, optional Lean row adaptation,
  facade classification, resource-directive parsing, rendering, and fixtures.
- Downstream change enabled: `ladon-installed-reportset-workflow`.
- Excluded work: proof-truth claims, unsourced transitive axiom closure,
  filename-only audit inference, or unconditional resource-budget findings.
- The same ordinary CLI surface serves every caller.
