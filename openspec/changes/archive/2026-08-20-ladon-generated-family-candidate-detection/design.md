## Context

Ladon currently has two distinct generated-code signals:

- `ladon.extraction.is_generated_module` adds a lexical `generated` tag when a
  path/name segment or leading comment explicitly says generated; and
- `ladon-project-ownership-and-generated-calibration` assigns the authoritative
  `project_generated` population only through a versioned configured family
  policy, while Lean-owned compiler evidence assigns `compiler_generated`.

Those contracts are intentionally conservative, but they leave path-neutral
mechanical families invisible. The MF observation found large `Data`/`All` and
numbered sibling layouts with uniform imports and repeated declaration stems
outside every generated-looking path. Those modules remained correctly
`target_owned`, yet later tables described that population as handwritten and
provided no advisory route to inspect the regular family.

This child adds an advisory relationship over existing canonical evidence. It
explicitly adopts:

- `ladon-project-ownership-and-generated-calibration` as the sole owner of
  primary populations, configured family identity, policy provenance, and
  generated-family promotion thresholds;
- the source index as owner of module paths, content hashes, imports, lexical
  declarations, and source fingerprints;
- `ladon-declaration-and-audit-integrity` and the canonical source index as owners
  of lexical declaration, command-shape, and completeness evidence used by the
  predicate;
- `ladon-actionable-findings-workflow` as owner of finding identity and canonical
  evidence links; and
- `ladon-large-inventory-scale-contract` as owner of required wall-time, RSS,
  output-size, determinism, and cache ceilings.

Per the umbrella ledger, this child starts after
`ladon-report-coverage-and-snapshot-integrity#coverage-foundation` and
`ladon-declaration-and-audit-integrity`; its canonical candidates then become
inputs to `ladon-analysis-inspection-surface`.

A generated-looking candidate is never a fifth primary population. It is an
advisory relation attached to rows whose calibrated population remains exactly
what the existing owner established.

## Goals / Non-Goals

**Goals:**

- Discover structurally regular source families without requiring `Generated`
  paths, comments, or repository-specific tokens.
- Combine family-level structure with required import-graph and lexical evidence.
- Keep every required predicate witness, its authority, thresholds, and
  predicate-clause results inspectable, with exact coverage for omitted
  non-winning aggregate feature keys.
- Preserve configured provenance and Lean compiler evidence without upgrades or
  downgrades.
- Stop using `handwritten` as an unsupported synonym for `target_owned`.
- Keep analysis deterministic, bounded, cacheable, and linearithmic or better at
  large-inventory scale.
- Gate qualifying and deliberately regular non-qualifying fixtures through the
  ordinary no-build text route.

**Non-Goals:**

- No inference that a generator exists, ran, produced the current bytes, or is
  fresh or defective.
- No inference of source authorship, theorem equality, proof equality, proof
  correctness, tactic success, or theorem truth.
- No automatic policy generation, modification, activation, or provenance
  promotion.
- No Matrix-Factorization path, theorem prefix, family size, or numeric threshold
  in production code.
- No repository-wide all-pairs clone detector or new proof/tactic parser.
- No required target build, Lean helper, network access, or sibling checkout.

## Decisions

### 1. Model candidates as advisory relations, not populations

The canonical output adds a `generatedFamilyCandidates` collection. Each row
contains:

- stable candidate identifier and rule-profile version;
- current calibrated member populations and exclusions;
- parent/sequence structural evidence;
- required predicate-witness rows and authorities plus the bounded strongest
  non-winning feature rows;
- raw member references plus bounded deterministic representatives;
- exact visible, total, omitted, projection-cause, and completeness state;
- source-index, scope, policy, and analysis fingerprints;
- exact predicate-clause results; and
- provenance, authorship, generator, and proof nonclaims.

Members do not receive a new primary population. An unmatched candidate remains
`target_owned`; policy-matched members remain `project_generated`; Lean-marked
declarations remain `compiler_generated`. The candidate may annotate a configured
family, but it cannot replace its family ID, policy digest, or quoted provenance.

Alternative considered: add `generated_looking_candidate` as a fifth population.
That would violate the existing exclusive population contract and invite
consumers to treat heuristic regularity as provenance.

### 2. Freeze one versioned generic candidate predicate

The initial profile is `generic-numbered-family-v1`. A structural group is the
set of modules whose repository-relative paths have the same parent and whose
final segment decomposes into the same non-empty prefix followed by a non-empty
decimal suffix. Decimal suffixes are parsed as non-negative integers; density is
the number of distinct observed suffix values divided by the inclusive span
`max_suffix - min_suffix + 1`.

The group is a v1 candidate if and only if all of these clauses hold:

1. the group has at least four member module paths;
2. numeric density is at least `4/5`;
3. one direct internal import target occurs in at least `ceil(4n/5)` of the `n`
   members;
4. either one `declaration-stem-v1` value or one
   `command-skeleton-v1` value occurs in at least `ceil(4n/5)` members; and
5. parent/final-segment parsing, direct internal imports, and the lexical feature
   inputs required to evaluate every member are complete and known.

All clauses, operands, fractions, chosen import and lexical witness, member set,
and profile identity are reported. Required predicate witnesses are retained even
when non-winning aggregate feature keys are omitted by the bounded projection. A
failure of clauses 1–4 is an observed non-match; a failure of clause 5 is
unavailable evaluation, not false. Non-numeric groups, exact-clone groups, and
source-shape groups retain their canonical raw source or graph evidence and may
have bounded aggregate feature rows, but have no v1 qualification route.

The v1 constants are not mutable ambient defaults. Any alternative thresholds,
feature clauses, or grouping semantics require an explicit separately versioned
profile. Its full configuration is reported and participates in source-analysis
and cache fingerprints. There is no unreported environment, repository-name, or
target-specific override.

Aggregate feature-key projection is analyzer-owned rather than a candidate
predicate option. `strongest-feature-keys-per-kind-version-v1` retains at most 12
keys independently per feature kind and normalization version, regardless of the
candidate representative limit. Its version and cap are reported and
fingerprinted; changing them requires an analyzer-version change, not a profile
override.

The first supported alternative grouping is
`parent-final-segment-decimal-suffix-width-v1`. It retains the v1 parent,
basename-prefix, and decimal-suffix rules but partitions suffix spellings by
their digit width. Thus `Cell1`/`Cell2` and `Cell01`/`Cell02` are evaluated as
separate sequences. This semantic is available only from an explicit
non-default profile; the built-in profile remains unchanged.

The ordinary CLI selects the built-in v1 profile by default and accepts an
alternative only through `--generated-family-candidate-profile PATH`. The JSON
document must declare its schema and non-default profile version; validation
rejects missing versions, unknown clauses, implicit fallbacks, and a payload that
claims the reserved built-in v1 identity with different constants. Reports expose
the selected profile ID, normalized configuration, and digest.

Alternative considered: multiple scoring or exact-clone routes. They make
membership underdetermined and allow later routing to reinterpret the detector.
One frozen conjunction gives tests and callers an exact predicate.

### 3. Derive path-independent features from canonical evidence

The detector consumes rather than rescans:

- module parent, basename, imports, content hash, and population;
- lexical declaration names/kinds and their source ranges;
- safely available normalized declaration-block evidence; and
- optional canonical proof-mechanism/source-shape evidence supplied by the
  inspection owner.

`declaration-stem-v1` tokenizes the local declaration name at underscore,
apostrophe, letter/digit, and lower/upper boundaries; numeric serial tokens are
replaced by a placeholder while remaining identifier tokens are preserved.
Evidence records the original names, normalized stem, member/declaration
coverage, and `lexical_text` authority.

`command-skeleton-v1` is deliberately separate from exact hashes. It consumes the
comment/string-safe token stream, removes trivia, replaces numeric literals and
numeric serial name tokens with typed placeholders, and preserves command kinds,
non-serial identifiers, attributes, modifiers, and delimiters. The algorithm and
version are exposed. It is a lexical command-shape feature, not Lean syntax or
proof semantics. Exact hashes and other source-shape summaries remain inspectable
as canonical raw evidence and are eligible for the bounded aggregate feature
projection, but are not v1 qualification clauses. Retaining the raw evidence does
not require retaining every aggregate hash or shape key as a candidate feature
row.

Alternative considered: add a second regular-expression scan inside candidate
analysis. That would diverge from canonical source evidence and double large-file
work.

### 4. Partition before aggregation

Candidate construction performs bounded indexed passes:

1. partition modules by repository-relative parent and normalized basename stem;
2. build numeric suffix sequence summaries inside those partitions;
3. count every observed direct-import, declaration-stem, command-skeleton,
   exact-hash, and source-shape aggregate key by feature kind and normalization
   version;
4. order keys by descending distinct-member count, then feature value, then
   authority, and retain at most 12 keys independently in each kind/version group
   under `strongest-feature-keys-per-kind-version-v1`;
5. materialize exact member, occurrence, and source-anchor evidence for retained
   keys, guaranteeing that the selected direct-import and lexical predicate
   winners remain retained;
6. evaluate the exact v1 conjunction only inside complete numbered partitions;
   and
7. retain exact observed-key coverage, aggregate counts, and bounded
   representatives rather than member pairs.

The detector never materializes every module pair or declaration pair. Runtime is
bounded by source-index evidence plus sorting/hash-map costs. Candidate identity
hashes the profile version, structural partition identity, and ordered member
identities; discovery order cannot change it.

Alternative considered: generic near-duplicate pairwise similarity. It is too
expensive and produces an unbounded pair surface on six-figure declaration
inventories.

### 5. Preserve component authority and use derived candidate authority

Feature authorities remain:

- `lexical_text` for declaration stems and command skeletons;
- `module_import_graph` for imports, common importers, and structural graph joins;
- source-index content-hash evidence for exact byte equality;
- configured policy authority for project-generated family membership; and
- `lean_environment` only for separately supplied compiler-generation evidence.

The combined candidate relationship uses `ladon_derived_heuristic`. It cannot
upgrade any component. Every renderer, region-registration row, and inspection
row repeats the nonclaim that candidate evidence establishes neither provenance
nor proof facts.

Alternative considered: label candidate members generated with lexical authority.
That still makes a provenance claim and contradicts configured policy ownership.

### 6. Route predicate matches without a second threshold

Every exact v1 predicate match is available as a bounded canonical candidate and
candidate region-registration row. Registration does not apply another
confidence score, review cutoff, or undocumented threshold. The v1 profile does
not create a new default defect finding. If an existing configured
generated-family rule supplies an owning finding threshold, the
actionable-findings owner may promote its existing finding kind against the
configured family; advisory evidence may be linked as context but cannot
substitute for the configured threshold or provenance.

Registration rows and inspection actions point to canonical members/features and
coverage. A dangling pointer or incomplete required feature makes registration
unavailable. This child does not emit complete review-region objects; the report
child's `snapshot-and-region-integration` milestone synthesizes them through the
existing review-region owner.

Alternative considered: promote every candidate as a generator defect. The
detector has no generator authority and regular handwritten-style source is an
intentional negative case.

### 7. Replace authorship language with exact population language

Canonical v3 tables and messages use `target_owned`,
`project_generated`, `compiler_generated`, `imported`, `unclassified`, or an
explicit unfiltered population. `target_owned` states repository ownership only.

Existing compatibility fields containing `handwritten` may remain during their
bounded compatibility window only when they:

- disclose the exact effective population and filters;
- carry migration guidance to the target-owned spelling; and
- never use the legacy field name as evidence of authorship.

Advisory candidates remain in target-owned metrics unless the caller explicitly
filters them as a candidate relation. Configured generated rows remain excluded
from target-owned rankings under the existing population owner.

Alternative considered: exclude every generated-looking candidate from
target-owned tables. That silently changes primary population semantics on
heuristic evidence.

### 8. Version cache and coverage inputs

The candidate profile, declaration-stem/command-skeleton normalizer versions,
feature-projection version and fixed cap, generated-family policy digest,
source-index schema/fingerprint, selected scope, and representative limits
participate in the analysis fingerprint. Candidate aggregates may be cached only
against that complete identity. The fixed feature-key cap remains independent of
the profile and representative limit.

All raw members, required predicate witnesses, and bounded non-winning feature
rows use the shared coverage contract. Feature coverage reports the exact
observed key population as visible, total, and omitted with the projection cause.
Omitting a non-winning aggregate key does not make an otherwise complete
predicate evaluation unavailable. Missing or failed source units and an
unavailable required predicate witness do; exact projected-key coverage never
upgrades incomplete source evidence.

Alternative considered: cache by source paths alone. Feature normalization,
population policy, and scope changes would produce unsound warm hits.

### 9. Reuse current scale and no-build acceptance authority

The tracked large fixture gains a neutral exact-match group whose asserted
candidate member set is fixed, plus groups that miss one clause at a time and
whose exact absence from candidate membership is asserted. Required installed
runs preserve the active 2,600-module,
1,500,000-line, 100,000-declaration fixture and its existing cold/warm wall,
512 MiB RSS, JSON/text size, cache, and determinism ceilings.

Focused text tests make subprocess creation fatal to prove the detector starts no
Lake, Lean, VCS, target initializer, or build. Optional MF runs remain read-only
observations recording source/analyzer fingerprints, moving counts, time, RSS,
coverage, and output hashes.

The focused portable fixture fixes its positive group as
`Neutral.Rows.Cell0` through `Neutral.Rows.Cell4`: all five suffixes are
occupied, exactly four members share `Neutral.Data` as a direct internal import,
and exactly four share the selected normalized lexical witness. The negative
sets are explicitly named and independently miss density, import coverage, or
lexical coverage; a named non-numeric exact-clone pair proves that hash evidence
is feature-only. An over-cap partition proves exact observed-key coverage,
strongest-12 ordering, winner retention independent of the representative limit,
and stable candidate/partition/feature references through report projection.
Tests compare complete candidate member sets, not just counts.

Alternative considered: freeze MF family names and counts as test or threshold
authority. The checkout is large, actively changing, and not portable.

## Risks / Trade-offs

- **[Regular handwritten-style tables qualify]** → Require independent evidence
  classes, retain every predicate witness with exact bounded feature-key
  coverage, keep status advisory, and maintain deliberate negative fixtures.
- **[Numeric threshold choices are too strict or loose]** → Version the generic
  profile, gate it on portable labeled fixtures, and change it only through an
  explicit calibrated packet.
- **[Name normalization merges unrelated declarations]** → Preserve original
  names, report coverage and version, and use stems only as one lexical feature.
- **[Command-skeleton normalization hides semantic differences]** → Keep exact
  hashes distinct and state that skeleton equality is not theorem/proof equality.
- **[Large families inflate reports]** → Retain raw canonical evidence, required
  predicate witnesses, the deterministic strongest 12 aggregate keys per
  kind/version, bounded representatives, exact coverage, and late inspection
  rather than copied members.
- **[Legacy handwritten fields mislead consumers]** → Add exact population
  metadata and migration warnings, then remove them through the established
  compatibility process.
- **[Candidate work invalidates cache performance]** → Reuse source-index rows,
  partition before aggregation, and enforce existing cold/warm gates.

## Migration Plan

1. Add the typed candidate profile, feature, feature-projection, aggregate,
   authority, nonclaim, and coverage models without changing primary populations.
2. Implement exact parent/final-segment/decimal-suffix partitions and versioned
   declaration-stem/command-skeleton adapters over canonical source-index evidence.
3. Add direct internal-import and lexical feature indexes; count all observed
   feature keys; retain the strongest 12 per kind/version with exact coverage;
   then evaluate the frozen v1 conjunction with bounded representatives and
   explicit unavailable states.
4. Attach candidate rows after population calibration, preserving configured and
   Lean-owned classifications.
5. Add candidate inspection and review-registration rows through existing
   evidence/finding owners, leaving complete region synthesis to report
   integration.
6. Rename canonical target-owned tables/messages and add bounded compatibility
   metadata for legacy handwritten spellings.
7. Bind the feature-projection version and cap into analysis/cache fingerprints,
   extend the portable large fixture with over-cap and stable-reference cases,
   and run focused, installed, no-build, scale, quality, and strict OpenSpec
   gates.
8. Record optional live MF evidence separately without changing profile
   thresholds or portable expectations.

Rollback can disable candidate construction and routing while leaving existing
configured generation provenance and population metrics intact. It must not
restore target-owned-as-handwritten claims.

## Open Questions

None. The candidate predicate, normalization versions, thresholds, fixed
`strongest-feature-keys-per-kind-version-v1` cap, selection ordering, routing
boundary, population behavior, and compatibility language are fixed above.
Changing predicate semantics requires a later explicit versioned calibration
change; changing projection semantics requires a later analyzer-version change.
