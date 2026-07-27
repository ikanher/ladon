## ADDED Requirements

### Requirement: Generated-family candidates preserve calibrated population ownership
Generated-family candidate detection SHALL consume canonical module,
declaration, import, source-hash, and population rows and SHALL leave the
primary population assignments owned by
`ladon-project-ownership-and-generated-calibration` unchanged. An unconfigured
candidate remains `target_owned` when that is its calibrated population and
MUST NOT be promoted to `project_generated`, `compiler_generated`, or quoted
generator provenance by heuristic evidence.

#### Scenario: Unconfigured regular target sources
- **WHEN** target-owned modules satisfy the advisory generated-family candidate rule but match no configured generated-family policy and have no Lean compiler-generation evidence
- **THEN** Ladon retains their `target_owned` primary population and attaches a separate generated-looking candidate relationship

#### Scenario: Configured generated family
- **WHEN** candidate members already belong to one policy-backed `project_generated` family
- **THEN** Ladon preserves the configured family identifier, policy digest, and quoted provenance as authoritative and does not replace them with heuristic provenance

#### Scenario: Lean compiler-generated declaration
- **WHEN** Lean-owned evidence classifies a declaration as `compiler_generated`
- **THEN** the advisory source-family detector does not downgrade or reinterpret that Lean-backed classification

### Requirement: Path-independent advisory family evidence
Candidate detection SHALL use generic, inspectable source and graph features
that do not require a `Generated` path segment, generated-looking filename,
target-specific namespace, theorem prefix, or repository-specific built-in
rule. Candidate formation MUST cite family-level structural evidence and
the required direct-import and normalized lexical evidence; a generated-looking
token alone MUST NOT be sufficient.

#### Scenario: Neutral numbered shard family
- **WHEN** modules under a neutral path satisfy every clause of `generic-numbered-family-v1`
- **THEN** Ladon emits one advisory candidate family with every predicate operand, clause result, and canonical member reference exposed

#### Scenario: Generated-looking name alone
- **WHEN** one target-owned module contains a generated-looking token in its path or declaration name but lacks qualifying family-level structural and source-pattern evidence
- **THEN** Ladon emits no generated-family candidate and preserves the existing target-owned classification

#### Scenario: Repository-specific vocabulary is absent
- **WHEN** the same structural fixture is renamed without changing its parent/numeric-suffix, direct-import, declaration-stem, or command-skeleton relationships
- **THEN** candidate membership and feature evidence remain equivalent apart from identities derived from the renamed source paths

### Requirement: The generic-numbered-family-v1 predicate is exact and versioned
The `generic-numbered-family-v1` predicate SHALL match a group if and only if:
all members have the same repository-relative parent; each final path segment
decomposes into the same non-empty prefix and a non-empty decimal suffix; the
group has at least four module paths; the number of distinct parsed suffix
values divided by the inclusive `maximum - minimum + 1` span is at least `4/5`;
one direct internal import target occurs in at least `ceil(4n/5)` of the `n`
members; one versioned normalized declaration stem or command skeleton occurs
in at least `ceil(4n/5)` members; and all evidence required to evaluate those
clauses is complete and known. Ladon MUST report every operand and clause result.

#### Scenario: Exact five-member boundary match
- **WHEN** `Neutral.Rows.Cell0` through `Neutral.Rows.Cell4` share one parent and prefix, all five suffix values are occupied, exactly four directly import `Neutral.Data`, exactly four share one `declaration-stem-v1` value or one `command-skeleton-v1` value, and all required evidence is complete
- **THEN** Ladon emits exactly one v1 candidate whose member set is exactly `{Neutral.Rows.Cell0, Neutral.Rows.Cell1, Neutral.Rows.Cell2, Neutral.Rows.Cell3, Neutral.Rows.Cell4}` and whose reported import and lexical coverage are both `4/5`

#### Scenario: Exact four-fifths density boundary
- **WHEN** one complete same-parent group contains exactly `Cell0`, `Cell1`, `Cell2`, and `Cell4`, all four share the required import and lexical witnesses, and no other module has the same parent and final-segment prefix
- **THEN** Ladon emits one v1 candidate with exactly those four members and reports four occupied suffixes over the five-value inclusive span

#### Scenario: One predicate clause misses
- **WHEN** an otherwise qualifying five-member group has common direct-import coverage of only `3/5`, common normalized lexical coverage of only `3/5`, or an occupied-suffix ratio below `4/5`
- **THEN** Ladon retains exact observed-key coverage, every required predicate witness, the bounded strongest non-winning aggregate feature rows, and the canonical raw source and graph evidence while emitting no v1 candidate for that group

#### Scenario: Required evidence is unknown
- **WHEN** any required parent, final-segment, direct-import, declaration-stem, or command-skeleton input is incomplete or unknown for a structural group
- **THEN** Ladon marks v1 evaluation unavailable and emits no candidate rather than interpreting missing evidence as an observed predicate failure

#### Scenario: Explicit profile override
- **WHEN** a caller uses `--generated-family-candidate-profile PATH` to select grouping, thresholds, or feature clauses different from v1
- **THEN** Ladon accepts them only from a valid explicit separately versioned profile and reports its normalized configuration and digest in analysis and cache fingerprints

#### Scenario: Explicit suffix-spelling-width grouping
- **WHEN** a valid explicit profile selects `parent-final-segment-decimal-suffix-width-v1`
- **THEN** Ladon evaluates otherwise-equal numbered families with different decimal suffix spelling widths as separate partitions and binds that grouping version into result identities and fingerprints

#### Scenario: Invalid or disguised override
- **WHEN** a supplied profile omits a version, contains an unknown clause, or reuses the reserved built-in v1 identity with different constants
- **THEN** Ladon rejects the profile before analysis and does not silently fall back to built-in v1

#### Scenario: No ambient override
- **WHEN** no explicit alternative profile is selected
- **THEN** repository names, environment state, current inventory size, and mutable live observations cannot change any v1 clause or constant

### Requirement: Inspectable candidate features and authority
Every generated-looking candidate family SHALL expose a stable candidate
identifier, member population, feature values, canonical evidence references,
source-index and scope fingerprints, bounded representatives, total and omitted
member counts, and deterministic predicate-clause results. Lexical features SHALL
retain `lexical_text` authority, import relationships SHALL retain
`module_import_graph` authority, configured provenance SHALL retain its policy
authority, and the combined advisory conclusion SHALL use
`ladon_derived_heuristic` authority.

For every numeric partition, Ladon SHALL count every observed aggregate feature
key before projection. `strongest-feature-keys-per-kind-version-v1` SHALL retain
at most 12 keys independently for each feature kind and normalization version,
ordered by descending distinct-member count, then feature value, then authority.
The selected direct-import and lexical predicate winners MUST remain retained.
Ladon SHALL report the projection version, fixed cap, selection rule, exact
observed key population, visible and omitted counts, and projection cause as
`featureCoverage`. The fixed feature-key cap is independent of candidate
representative limits and candidate-profile overrides, and its version and cap
MUST participate in the analysis fingerprint.

Canonical source, import, hash, and declaration evidence SHALL remain available
separately from the bounded aggregate candidate feature rows. Exact projected-key
coverage MUST NOT be presented as complete source evidence when upstream source
evidence is incomplete.

#### Scenario: Candidate combines lexical and graph evidence
- **WHEN** a candidate is supported by repeated declaration stems and uniform imports
- **THEN** the candidate preserves both component authorities, identifies the joining members, and labels the combined relationship as a Ladon-derived heuristic

#### Scenario: Candidate representatives are bounded
- **WHEN** a candidate family contains more members than the configured representative limit
- **THEN** Ladon reports exact total, visible, and omitted counts and retains a deterministic representative sample without presenting it as the complete family

#### Scenario: Bounded non-winning feature keys
- **WHEN** one numeric partition has more than 12 observed keys in one feature-kind and normalization-version group while its selected direct-import and lexical predicate winners are known
- **THEN** Ladon retains exactly the strongest 12 keys for that group in the specified order, retains both selected predicate winners, reports the exact larger observed total and omitted count with `strongest-feature-keys-per-kind-version-v1` as the cause, and produces the same feature projection when only the candidate representative limit changes

#### Scenario: Required evidence is incomplete
- **WHEN** source-index failure or upstream evidence incompleteness makes an input required by the candidate rule unavailable
- **THEN** Ladon marks candidate evaluation incomplete or unavailable and MUST NOT treat the unavailable feature as observed false, fabricate a complete candidate, or use exact projected-key coverage to upgrade the incomplete source evidence

#### Scenario: Bounded omission is not missing source evidence
- **WHEN** every required predicate input and selected witness is known but bounded projection omits only non-winning aggregate feature keys
- **THEN** Ladon evaluates the predicate exactly, reports complete observed-key counts for that projection, and does not mark the predicate unavailable solely because those non-winning aggregate rows are omitted

### Requirement: Stable generic sibling and sequence analysis
Numbered-sibling evidence SHALL be derived from generic parent identity and
the final-segment decomposition into a common non-empty prefix and decimal
suffix. Ladon SHALL record observed member paths, parsed integer suffixes, gaps,
bounds, occupied-value count, inclusive span, and density without assuming that
numbering proves generation. Discovery order and decimal zero padding MUST NOT
change parsed numeric values or predicate-clause results.

#### Scenario: Contiguous siblings in shuffled discovery order
- **WHEN** a qualifying row family is discovered in different filesystem or input order
- **THEN** Ladon produces the same normalized sequence evidence, candidate identifier, member order, and representative selection

#### Scenario: Decimal zero padding
- **WHEN** decimal suffix spelling changes only by leading zero padding while the module identities supplied to comparison are normalized accordingly
- **THEN** parsed suffix values, gaps, bounds, occupied-value count, inclusive span, density, and predicate outcome remain equivalent

#### Scenario: Sparse numbered handwritten modules
- **WHEN** a parent contains only a few numbered modules with substantial gaps, diverse imports, and unrelated declaration stems
- **THEN** Ladon preserves raw sibling evidence but emits no qualifying generated-family candidate

#### Scenario: Non-numeric regular family
- **WHEN** modules share source-shape evidence but have no numeric sibling structure
- **THEN** Ladon retains the canonical raw source and graph evidence, may retain only bounded aggregate feature rows, emits no `generic-numbered-family-v1` candidate, and MUST NOT invent sequence continuity

### Requirement: Declaration-stem and command-skeleton evidence remains lexical
Ladon SHALL derive repeated declaration stems, tactic-command skeletons,
normalized declaration blocks, exact source hashes, and near-shape summaries as
distinct feature kinds with versioned normalization identity in canonical raw
evidence. Their aggregate candidate rows are subject to the fixed bounded
feature-key projection. Only `declaration-stem-v1` or `command-skeleton-v1`
member coverage participates in the v1 lexical clause; exact hashes and other
shape summaries MUST NOT create a v1 candidate. These features MUST NOT be
presented as resolved Lean names, equal theorem statements, equal proofs,
successful tactics, or proof dependencies.

#### Scenario: Repeated declaration stem
- **WHEN** sibling modules contain many safely recognized lexical declarations with one normalized name stem
- **THEN** Ladon records the stem in canonical lexical evidence and, when it is a selected predicate winner or retained bounded aggregate key, records its exact frequency, member coverage, source anchors, and `lexical_text` authority without claiming a Lean-resolved declaration family

#### Scenario: Exact source clones
- **WHEN** distinct module paths have equal source-content hashes
- **THEN** Ladon records canonical exact-clone evidence separately from normalized shape evidence, retains its candidate aggregate row only when selected by the bounded feature projection, does not create a v1 candidate unless the exact numbered predicate independently matches, and does not claim that a generator produced either file

#### Scenario: Similar skeleton with different theorem text
- **WHEN** sibling modules share a normalized command skeleton but differ in exact source and declaration-block hashes
- **THEN** Ladon labels only source-shape similarity and MUST NOT call the theorem statements or proofs equal

### Requirement: Candidate status has explicit nonclaims
Every candidate aggregate, region-registration row, finding, renderer, and inspection row SHALL
state that generated-looking evidence does not establish generator
existence, generator identity, generator execution, provenance, freshness,
reproducibility, a generator defect, source authorship, proof correctness, or
theorem truth. Candidate detection MUST NOT write, activate, or silently infer
a generated-family policy.

#### Scenario: Exact predicate match routes directly
- **WHEN** a complete structural group matches every `generic-numbered-family-v1` clause
- **THEN** Ladon SHALL emit and route its advisory candidate without applying a second confidence score or review threshold, with component evidence and all provenance and proof nonclaims preserved

#### Scenario: Candidate suggests policy configuration
- **WHEN** a matched candidate is sufficient to form bounded advisory policy guidance
- **THEN** Ladon emits only structured review guidance and does not create, modify, select, or apply a policy file

#### Scenario: Candidate contains valid Lean proofs
- **WHEN** separate Lean extraction succeeds for declarations inside a candidate family
- **THEN** Ladon keeps Lean declaration evidence separate and does not strengthen or weaken proof authority because the source looks generated

### Requirement: Ownership labels are not authorship claims
Population-sensitive report fields, table identifiers, findings, and rendered messages MUST
describe the actual calibrated population. Ladon MUST NOT use
`handwritten` as a synonym for `target_owned`, because target ownership alone
does not establish how source bytes were produced. Compatibility fields that
retain an older name SHALL disclose the counted population and MUST NOT emit an
authorship claim.

#### Scenario: Candidate remains target-owned
- **WHEN** an advisory generated-looking family remains in the `target_owned` primary population
- **THEN** target-owned rankings identify that population exactly and do not describe the candidate members as proven handwritten source

#### Scenario: Configured generated rows are excluded
- **WHEN** a ranking is explicitly limited to target-owned modules and configured project-generated members are present
- **THEN** the ranking excludes those configured members and reports its numerator, denominator, and exclusions under the existing population contract

#### Scenario: Legacy handwritten field is serialized
- **WHEN** a compatibility report exposes an older field whose name contains `handwritten`
- **THEN** the report identifies the exact effective population, emits migration guidance, and does not use the field name as evidence of authorship

### Requirement: Candidate aggregation is deterministic and bounded
Candidate analysis SHALL partition evidence by stable structural keys before
forming member relationships, SHALL bound retained pair or representative
witnesses, and SHALL produce deterministic identities and ordering for
equivalent source bytes, source-index version, scope, and configuration. It
MUST NOT require materializing every pair across the complete module or
declaration inventory. Before retaining aggregate feature rows, Ladon SHALL
count every observed key in each feature-kind and normalization-version group,
retain at most 12 under
`strongest-feature-keys-per-kind-version-v1`, preserve selected predicate
winners, and report exact visible, total, and omitted key coverage. The
projection version and cap SHALL be fingerprinted independently of candidate
representative limits.

#### Scenario: Equivalent repeated inventory
- **WHEN** the same portable inventory is analyzed twice with equal fingerprints and explicit configuration
- **THEN** candidate identifiers, members, feature values, predicate operands and clause results, representatives, coverage, and normalized machine output are identical

#### Scenario: Many unrelated declarations
- **WHEN** a large inventory contains many declaration candidates that do not share a qualifying partition key
- **THEN** Ladon does not construct or retain a global all-pairs comparison table

#### Scenario: Existing large-inventory gate
- **WHEN** candidate detection is enabled on the tracked large-inventory fixture
- **THEN** the ordinary installed text-analysis route remains within the active wall-time, peak-RSS, JSON-size, text-size, determinism, and warm-cache ceilings owned by `ladon-large-inventory-scale-contract`

### Requirement: Candidate review registration retains canonical evidence
Generated-looking candidate summaries and region-registration rows SHALL link to
the canonical family aggregate, raw members, source features, import evidence,
coverage metadata, authority, nonclaims, and an ordinary inspection action. A
registration row MUST retain stable finding identity and evidence-link behavior
owned by `ladon-actionable-findings-workflow`, MUST NOT duplicate the full
candidate payload or create a second finding taxonomy, and MUST NOT synthesize a
complete review-region object. Final region synthesis remains owned by
`ladon-report-coverage-and-snapshot-integrity`. Every retained registration MUST
resolve its stable candidate, partition, selected-import feature, and
selected-lexical feature identifiers to the exact retained canonical rows.
Review projection MUST reconcile those identifiers by stable identity rather
than array position.

#### Scenario: Candidate region registration
- **WHEN** one complete family matches the selected explicit candidate predicate
- **THEN** its producer registration cites the canonical candidate identifier, member and feature evidence, authority, coverage, nonclaims, and an ordinary inspection action without emitting a complete review-region object

#### Scenario: Candidate evidence pointer is unavailable
- **WHEN** a required member or feature reference cannot be resolved in the canonical report or matched source index
- **THEN** Ladon marks the producer registration unavailable and does not promote a complete candidate finding

#### Scenario: Bounded review projection preserves candidate routes
- **WHEN** review projection omits candidates, partitions, or non-winning feature rows beyond their respective caps
- **THEN** every retained producer registration resolves to its exact retained candidate and partition plus the selected import and lexical feature rows, every omitted candidate has no producer registration, and no registration contains a dangling or cross-candidate reference

### Requirement: Portable positive and negative candidate gates
Required generated-family candidate gates SHALL use tracked, target-neutral
fixtures, SHALL run through the text backend without a target build or Lean
helper, and SHALL contain both qualifying and deliberately regular
non-qualifying source families. Required gates MUST NOT depend on a sibling
repository, network access, a target-specific family name, or a mutable source
tree.

#### Scenario: Portable positive candidate fixture
- **WHEN** the neutral fixture contains exactly `Neutral.Rows.Cell0` through `Neutral.Rows.Cell4`, all required evidence is complete, all five suffixes are occupied, and exactly four members share the asserted direct internal import and normalized lexical witness
- **THEN** the required gate asserts that the sole v1 candidate has exactly those five members, import and lexical coverage `4/5`, every predicate operand and clause result, canonical evidence links, lexical and graph authorities, unchanged primary populations, bounded coverage, and complete nonclaims

#### Scenario: Portable negative candidate fixture
- **WHEN** the neutral fixture also contains `{Neutral.Sparse.Cell0, Neutral.Sparse.Cell1, Neutral.Sparse.Cell2, Neutral.Sparse.Cell5}`; `{Neutral.Imports.Cell0, Neutral.Imports.Cell1, Neutral.Imports.Cell2, Neutral.Imports.Cell3, Neutral.Imports.Cell4}` with only `3/5` common direct-import coverage; `{Neutral.Lexical.Cell0, Neutral.Lexical.Cell1, Neutral.Lexical.Cell2, Neutral.Lexical.Cell3, Neutral.Lexical.Cell4}` with only `3/5` common normalized lexical coverage; `{Neutral.Clones.Alpha, Neutral.Clones.Beta}` as a non-numeric exact-clone pair; and `Neutral.GeneratedThing` as an isolated generated-looking name
- **THEN** the required gate asserts that none of those exact module identities occurs in any v1 candidate, while their raw source and graph rows remain available and no module is heuristically promoted to project-generated provenance

#### Scenario: Predicate boundary mutations
- **WHEN** the positive fixture is mutated one clause at a time across member-count, numeric-density, direct-import, normalized-lexical, or evidence-completeness boundaries
- **THEN** the required gate asserts the exact candidate member set at and above each documented boundary and exact absence or unavailable state below it

#### Scenario: Portable over-cap feature projection
- **WHEN** a tracked neutral fixture supplies more than 12 observed keys for one feature-kind and normalization-version group and report projection omits at least one candidate
- **THEN** the required gate asserts count-all/strongest-12 ordering, selected-winner retention, exact `featureCoverage`, projection identity and fingerprint participation, representative-limit independence, exact stable candidate/partition/selected-feature references, and absence of producer registrations for omitted candidates

#### Scenario: Required no-build execution
- **WHEN** the portable candidate gate runs with subprocess creation for Lake, Lean, version control, or target initialization made fatal
- **THEN** the text-backed candidate analysis completes without launching such a process

#### Scenario: Optional live repository observation
- **WHEN** candidate predicates are observed on a mutable large Lean repository
- **THEN** Ladon records source fingerprint, dirty state, analyzer identity, timing, peak RSS, coverage, and moving candidate counts and MUST NOT use that repository or its current family cardinalities as portable pass or fail authority
