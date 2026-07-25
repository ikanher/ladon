## Why

A post-alpha run on the live Matrix-Factorization repository showed that Ladon
can find useful architecture pressure, but its ordinary review loop is not yet
operable at large-project scale: a 2,611-module text run took about 53 seconds,
a full JSON report occupied 218 MB, and one Lean-backed owner run peaked near
8 GB before returning a poorly explained partial result. The next product pass
should make the same public CLI useful to people, scripts, editors, and models
on real Lean repositories without introducing caller-specific commands or
defaults.

## What Changes

- Establish a measured large-inventory contract for discovery, memory, report
  size, and deterministic reuse. Replace repeated report payload copies with a
  single canonical owner plus explicit projections; this is **BREAKING** for
  consumers that rely on duplicated `phases.*.data` or
  `pipeline.timings.*.data` after the compatibility window.
- Separate the requested review root from the inventory population. Add
  inspectable owner, import-closure, namespace, named multi-root, changed-set,
  and full-inventory scope planning without claiming that Ladon can infer the
  mathematically correct roots.
- Make long and partial runs observable through stderr progress, overall
  resource bounds, structured failure reasons, and schema-valid partial
  reports. Reuse the existing supervisor and cache protocol.
- Calibrate target-owned, imported, compiler-generated, and project-generated
  declaration/module populations so generated tables and synthetic Lean names
  do not dominate owner review.
- Make every promoted finding inspectable from the ordinary installed CLI by
  stable ID, scope, source/evidence references, confidence, and suggested next
  review command.
- Add versioned, resumable analysis runsets that execute several ordinary Ladon
  analyses with shared indexes/caches and produce one canonical report per
  root plus a deterministic bundle manifest.
- Package the existing atlas, query, diff, cards, and workflow libraries as
  supported installed CLI operations rather than source-checkout-only scripts.
- Recognize command-only Lean audit facades (`#check`, `#print axioms`, and
  bounded resource directives) as review surfaces with explicit authority and
  nonclaims.
- Use portable generated fixtures for required regression gates. Keep the
  current dirty Matrix-Factorization tree as fingerprinted observational
  acceptance evidence, never as hidden or moving CI truth.
- Reuse the retained `ladon-theorem-surface-changelog` and Review Radar roadmap
  by reference; do not create a second semantic comparator or atlas engine.

## Capabilities

### New Capabilities

- `ladon-large-inventory-scale-contract`: Defines cold/warm discovery, memory,
  serialization, payload-ownership, and large-fixture non-regression behavior.
- `ladon-analysis-root-and-scope-contract`: Resolves, previews, and records
  owner, closure, namespace, multi-root, changed-set, and inventory scopes.
- `ladon-partial-run-observability`: Makes progress, limits, cancellation,
  partial states, and failure causes visible and machine-readable.
- `ladon-project-ownership-and-generated-calibration`: Separates target,
  imported, compiler-generated, and configured generated-family populations.
- `ladon-actionable-findings-workflow`: Provides stable evidence links,
  owner-relevant ranking, filtering, and finding lookup through the public CLI.
- `ladon-analysis-runsets-and-bundles`: Defines resumable multi-root plans,
  isolated per-root reports, shared reuse, and deterministic bundle manifests.
- `ladon-installed-reportset-workflow`: Exposes existing atlas, query, diff,
  cards, and workflow operations from an installed Ladon distribution.
- `ladon-lean-audit-command-surface`: Reports command-only audit references,
  axiom-query intent, and resource directives without promoting them to proof
  authority.

### Modified Capabilities

None. Each implementation child must adopt existing report-v2, CLI execution,
Lean runtime, atlas, and theorem-changelog contracts by reference rather than
silently redefining them.

## Impact

- Affected code includes source discovery/indexing, report construction and
  serialization, text rendering, Lean extraction adaptation, finding evidence,
  CLI dispatch, atlas script packaging, and benchmark fixtures.
- Public CLI behavior gains general analysis planning, report inspection,
  runset, and report-set operations. No operation is specific to an LLM or to
  Matrix-Factorization.
- Report consumers receive a documented migration path away from duplicated
  v2 payload locations and toward stable canonical sections/projections.
- Portable CI gains a generated large-project fixture and resource/report-size
  budgets; optional live-repository acceptance records target fingerprint,
  Lean toolchain, Ladon identity, timings, RSS, helper counts, and output hashes.
- Matrix-Factorization source remains read-only and no target-specific module
  names or thresholds enter Ladon production code.
