## Why

Large Lean repositories can contain highly regular row/shard families whose
paths never say `Generated`, while Ladon's configured generated provenance sees
only policy-matched families. The alpha product needs a conservative advisory
surface for discovering such candidates without converting source regularity
into provenance, authorship, generator, or proof claims.

## What Changes

- Detect path-independent generated-looking family candidates with the frozen
  `generic-numbered-family-v1` predicate: same-parent numeric siblings, at least
  four members, at least four-fifths numeric density, at least four-fifths common
  direct internal-import coverage, and at least four-fifths coverage by one
  versioned normalized declaration stem or command skeleton.
- Keep every candidate as an advisory relationship while preserving the existing
  calibrated primary population and configured project-generated provenance.
- Require every v1 predicate input to be complete and known. Candidate analysis
  counts every observed aggregate feature key, retains required predicate
  witnesses plus at most the 12 strongest keys per feature kind and normalization
  version, and reports exact visible, total, and omitted key coverage.
  Non-numeric, insufficient, sparse, import-diverse, and lexically diverse groups
  retain raw canonical source and graph evidence but do not create a v1 candidate.
- Expose stable candidate identity, member and feature evidence, authority,
  exact predicate/profile identity, fixed feature-projection identity and cap,
  coverage, representatives, and explicit nonclaims. Predicate overrides are
  explicit, separately versioned, fingerprinted, and reported; the analyzer-owned
  feature projection is not a profile or representative-limit override.
- Replace unsupported `target_owned` → `handwritten` wording with exact population
  labels and bounded compatibility guidance.
- Partition candidate analysis by stable structural keys, count feature keys
  before bounded projection, and avoid a repository-wide all-pairs comparison.
- Route every predicate match as an advisory candidate without applying a second
  implicit confidence or review threshold.
- Add portable positive and negative fixtures, no-build execution checks,
  installed/report parity, and existing large-inventory resource gates.
- Keep mutable live-repository observations optional and fingerprinted.

## Capabilities

### New Capabilities

- `ladon-generated-family-candidate-detection`: Advisory, path-independent
  generated-looking family evidence that remains separate from configured
  generation provenance and source authorship.

### Modified Capabilities

None.

## Impact

- Affected code: lexical source-index evidence, module/declaration family
  grouping, command-skeleton normalization, population-aware rankings, finding
  and review-registration adapters, report schemas, rendering, cache
  fingerprints, and large portable fixtures.
- `ladon-project-ownership-and-generated-calibration` remains the sole owner of
  primary populations and configured `project_generated` provenance.
  `ladon-actionable-findings-workflow` remains the owner of promoted finding
  identity and evidence links.
- Per the umbrella ledger, implementation starts after the report
  `coverage-foundation` and `ladon-declaration-and-audit-integrity`; it then
  enables `ladon-analysis-inspection-surface`.
- Candidate evidence remains lexical, graph-derived, or hash-derived navigation.
  It does not establish a generator, generator execution, provenance, freshness,
  authorship, a generator defect, proof correctness, or theorem truth.
- Required tests are target-neutral, text-backed, no-build, and independent of
  sibling repositories and network access.
