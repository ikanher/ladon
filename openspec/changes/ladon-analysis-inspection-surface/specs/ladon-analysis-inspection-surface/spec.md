## ADDED Requirements

### Requirement: Ordinary analysis inspection surface
An installed Ladon distribution SHALL expose caller-neutral inspection
operations for modules, declarations, imports, audits, options, resources, and
proof mechanisms. These operations MUST navigate canonical report or source-index
evidence through the same public CLI contract used by people, scripts, editors,
and models, and MUST NOT introduce an LLM-specific command, default, threshold,
or hidden analysis path. The installed grammar SHALL be `ladon inspect <noun>`
with exactly one of `--report` or `--source-index`; artifact-only inspection SHALL
be the default, while an explicitly supplied `--repo-root` SHALL select
live-repository-bound validation.

#### Scenario: Installed caller inspects declarations
- **WHEN** a caller uses the documented declaration-inspection operation against a canonical report or compatible source index
- **THEN** Ladon returns declaration rows through the ordinary installed CLI without requiring the source checkout or a caller-specific interface

#### Scenario: Inspection does not imply analysis
- **WHEN** a caller requests inspection of an existing compatible report or source index without explicitly requesting a new analysis
- **THEN** Ladon reads that evidence and starts no source analysis, Lake build, Lean helper, or target-controlled process

#### Scenario: Ordinary report retains additive lexical navigation
- **WHEN** a current report is produced from text-backed analysis containing generic options, resources, audits, declarations, or proof-mechanism occurrences
- **THEN** every noun remains inspectable from that report through bounded canonical rows whose stable identities, exact source anchors, registered coverage references, internal-cap omissions, and projection omissions remain truthful

### Requirement: Canonical evidence and owner adoption
Inspection SHALL consume the existing canonical source-index, report,
audit-command, finding, and atlas identities rather than create parallel
inventories or query engines. Every returned row MUST identify its canonical
stable identity, source/index fingerprint, schema version, selected population,
backend authority, and collection-completeness reference.

#### Scenario: Inspection resolves a canonical row
- **WHEN** an inspection result corresponds to a canonical declaration, audit command, import site, option, or resource row
- **THEN** the result carries a resolvable canonical identity and does not copy the row into a second authority-bearing inventory

#### Scenario: Evidence is unavailable
- **WHEN** a requested field or relationship is absent from the selected backend evidence
- **THEN** inspection reports the field as unavailable with its reason and does not infer it from a nearby label or another authority class

### Requirement: Deterministic filtering and pagination
Every list inspection operation SHALL provide documented deterministic filters
and bounded pagination. A page MUST record the normalized query, stable ordering,
visible row count, matching total, omitted count, completeness, and either a
stable cursor or an explicit offset/limit identity. Equivalent queries over the
same fingerprinted evidence MUST return identical page membership and cursors.

#### Scenario: Late declaration page remains reachable
- **WHEN** a matching declaration sorts after the first bounded page
- **THEN** a caller can request a subsequent page and retrieve that declaration with the same query identity and matching-total count

#### Scenario: Equivalent filtered query
- **WHEN** two callers submit semantically equivalent filters in different supported argument orders against unchanged evidence
- **THEN** Ladon normalizes the filters and returns identical row ordering, page boundaries, counts, and cursor identities

#### Scenario: Invalid filter
- **WHEN** a caller supplies an unsupported field, malformed value, or incompatible filter combination
- **THEN** Ladon returns the established invocation-error class with the supported filter vocabulary and emits no partial result that looks complete

### Requirement: Fingerprint-safe inspection
Inspection of cached or separately supplied source-index evidence MUST verify
compatibility with its recorded analysis identity, schema, scope-affecting
configuration, and any repository identity explicitly bound by the caller.
Pagination tokens MUST bind to the immutable artifact evidence and normalized
query fingerprints. Artifact-only inspection MUST NOT read a live checkout merely
to revalidate source bytes. A stale or mismatched fingerprint within the selected
inspection mode MUST fail explicitly and MUST NOT be treated as a cache hit or an
empty result.

#### Scenario: Immutable artifact remains selected
- **WHEN** a caller continues pagination over the same immutable report or source-index artifact while an unrelated live checkout changes
- **THEN** Ladon validates the cursor against the artifact fingerprint, returns the next artifact page, and does not inspect or mix rows from the live checkout

#### Scenario: Live-bound source changes between pages
- **WHEN** a caller explicitly selects live-repository-bound inspection and presents a pagination cursor after a registered source or configuration fingerprint has changed
- **THEN** Ladon rejects the cursor as stale, identifies the mismatched fingerprint class, and returns no rows from changed live evidence

#### Scenario: Index belongs to another analysis
- **WHEN** a supplied source index has a valid schema but does not match the requested repository, scope, policy, or analyzer identity
- **THEN** Ladon returns a structured incompatibility diagnostic instead of silently inspecting the mismatched index

### Requirement: Exact lookup and source navigation
Every inspectable row with a stable identity SHALL support exact lookup. The
lookup result MUST expose a repository-relative source anchor when one exists,
the reason when no exact anchor is available, authority and population labels,
and bounded links to related canonical rows or ordinary follow-up inspection
commands.

#### Scenario: Source-locatable option row
- **WHEN** a caller looks up a stable option-row identity that has an exact source range
- **THEN** Ladon returns the repository-relative path and range together with the row's lexical authority and containing scope

#### Scenario: Aggregate has no exact source range
- **WHEN** a caller looks up a proof-mechanism or resource aggregate derived from multiple source rows
- **THEN** Ladon reports that no single source range owns the aggregate and provides bounded canonical member links rather than fabricating a location

### Requirement: Lexical proof-mechanism navigation
The text source index SHALL record comment/string-safe occurrences of supported
tactic-command tokens and attributes within safely recognized declaration
ranges. Inspection SHALL summarize those occurrences by selected population,
module, declaration candidate, and generated-family candidate when those
dimensions are available. Every row MUST retain lexical authority and MUST state
that token occurrence is not an elaborated tactic invocation, theorem dependency,
rewrite direction, simplifier use, proof success, or theorem-quality verdict.

#### Scenario: Tactic tokens are summarized
- **WHEN** a selected declaration contains supported tactic-command tokens in executable source rather than comments or strings
- **THEN** inspection exposes bounded token rows and aggregates with source anchors, lexical authority, and explicit proof-mechanism nonclaims

#### Scenario: Comment and string contain tactic text
- **WHEN** tactic-like text occurs only in a comment or string literal
- **THEN** Ladon emits no executable tactic-occurrence row for that text

#### Scenario: Elaborated proof shape is requested
- **WHEN** a caller asks inspection for an elaborated tactic identity or InfoTree proof shape that the selected evidence does not contain
- **THEN** Ladon reports the evidence as unavailable and identifies the separately owned proof-xray route without manufacturing native proof-shape evidence

### Requirement: Lexical scope-context navigation
The source index SHALL retain safely recognized namespace, section, variable,
`omit`, local notation, local instance, `open scoped`, and export context for
declaration and command rows. Inspection MUST expose parser status and unresolved
scope state, and MUST NOT guess binding, name resolution, instance selection, or
effective elaboration context when lexical state is insufficient.

#### Scenario: Declaration has supported lexical context
- **WHEN** a declaration occurs inside safely recognized namespace and section context with visible variable and scoped-open commands
- **THEN** inspection returns that lexical context with source anchors and lexical authority

#### Scenario: Scope syntax is ambiguous
- **WHEN** unsupported or malformed syntax prevents safe lexical scope tracking
- **THEN** Ladon preserves an unresolved scope-context row and does not synthesize a fully resolved namespace, binding, or instance environment

### Requirement: Generic option and resource inspection
The text source index SHALL create a generic lexical row for every safely parsed
`set_option` command. Supported resource options MUST additionally expose their
normalized finite or unlimited value and lexical scope, while other options MUST
retain a bounded raw value and documented option class. Inspection SHALL support
module-, scope-, option-, and candidate-family aggregation without claiming that
a configured limit is consumed runtime, proof failure, or theorem quality.

#### Scenario: Unlimited heartbeat option
- **WHEN** source contains a safely parsed unlimited `maxHeartbeats` setting
- **THEN** inspection returns its normalized unlimited value, lexical scope, source anchor, population, and resource nonclaim

#### Scenario: Non-resource option
- **WHEN** source contains a safely parsed `set_option` command outside the supported resource-option vocabulary
- **THEN** inspection retains a bounded lexical row and option class without silently dropping it or treating it as runtime evidence

#### Scenario: Option-like text is not executable
- **WHEN** `set_option`-like text occurs only in a comment or string
- **THEN** Ladon emits no executable option row for that text

### Requirement: Bounded option and resource review registration
Option and resource rows SHALL remain navigation evidence by default. Ladon SHALL
label a row or aggregate as resource pressure in this capability only when a
supported resource setting is normalized as unlimited or when an explicit,
fingerprinted repository policy matches it. Ladon MUST NOT infer a finite-value
pressure threshold from the Matrix-Factorization observation, one repository,
source ordering, or an unexplained percentile. An eligible pressure row SHALL
expose canonical producer-registration data and an ordinary inspection action;
complete review-region synthesis remains owned by
`ladon-report-coverage-and-snapshot-integrity`.

#### Scenario: Unlimited resource setting
- **WHEN** a supported resource option is safely normalized as unlimited
- **THEN** Ladon may register an unlimited-resource review input with lexical authority, configured-setting nonclaims, and no measured-runtime or proof-failure claim

#### Scenario: Explicit finite policy match
- **WHEN** a finite resource row matches an explicit repository policy whose identity and threshold are present in the analysis fingerprint
- **THEN** Ladon registers policy-backed review input and cites both the source row and policy evidence

#### Scenario: Large finite value without policy
- **WHEN** a finite resource setting is numerically large but no explicit policy matches it
- **THEN** Ladon retains the row and aggregates for inspection but emits no pressure classification from its magnitude alone

### Requirement: Separate lexical and Lean enrichment authority
Optional Lean-backed identities or results SHALL remain separate enrichments of
lexical inspection rows and MUST retain the existing Lean extraction authority,
toolchain, scope, partial-state, and unavailable-reason contracts. Lexical
inspection MUST remain usable when Lean enrichment is skipped, partial, timed
out, or unavailable.

#### Scenario: Lean resolves an audit subject
- **WHEN** the selected report contains both a lexical audit-subject candidate and a Lean-resolved declaration identity
- **THEN** inspection links the two rows while preserving their distinct authority and source provenance

#### Scenario: Text backend only
- **WHEN** inspection uses a text-backed report with no Lean enrichment
- **THEN** lexical module, declaration, audit, mechanism, option, and resource rows remain available and no Lean result is implied

### Requirement: Portable inspection acceptance
Required acceptance gates SHALL exercise the installed ordinary CLI against
tracked, target-neutral fixtures. The gates MUST cover deterministic late-page
lookup, exact identities, filters, stale-fingerprint rejection, text/JSON
semantic parity, lexical mechanism and scope context, generic options and
resources, comment/string negatives, absent Lean enrichment, and clean output
channels. A mutable sibling repository MUST NOT define required cardinalities or
pass criteria.

#### Scenario: Installed portable inspection matrix
- **WHEN** the required inspection matrix runs from an installed candidate against the tracked portable fixture
- **THEN** every inspection noun, pagination path, authority boundary, completeness count, and positive and negative lexical predicate passes without reading Matrix-Factorization

#### Scenario: Optional live observation
- **WHEN** maintainers inspect an available Matrix-Factorization checkout for observational acceptance
- **THEN** they record its source fingerprint and moving counts separately and do not change portable expectations or production defaults
