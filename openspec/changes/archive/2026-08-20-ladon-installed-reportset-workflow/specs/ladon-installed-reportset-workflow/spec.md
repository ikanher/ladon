## ADDED Requirements

### Requirement: Installed ordinary report-set operations
An installed Ladon distribution SHALL expose supported public CLI operations
for atlas construction, canned queries, structural atlas diff, reviewer cards,
and report-set workflow summaries. These operations MUST be available to every
caller under the same documented options and MUST NOT require execution of
source-checkout-only scripts.

#### Scenario: Installed distribution outside checkout
- **WHEN** a wheel is installed into an isolated environment and invoked from a directory outside the Ladon source tree
- **THEN** atlas, query, diff, cards, and workflow help and successful fixture operations are available

#### Scenario: Caller parity
- **WHEN** a person, script, editor, or model invokes the same report-set operation with the same inputs
- **THEN** command behavior, analysis data, defaults, output schema, and exit status are identical

### Requirement: Existing report-set engines remain authoritative
Installed report-set operations MUST delegate to the existing atlas, SQLite
query, atlas diff, reviewer-card, and workflow library implementations.
CLI packaging SHALL NOT introduce a second atlas graph, query evaluator, diff
algorithm, card model, or review-priority calculation.

#### Scenario: CLI and library parity
- **WHEN** the installed CLI and the owning library process equivalent portable inputs
- **THEN** their normalized canonical atlas, query rows, diff rows, cards, and workflow sections are semantically identical

#### Scenario: Maintained source script remains
- **WHEN** a legacy maintainer script is retained during migration
- **THEN** it acts as a thin wrapper over the same packaged implementation and propagates its status unchanged

### Requirement: Canonical report and bundle ingestion
Report-set operations SHALL accept canonical supported Ladon reports and
versioned runset bundles, resolve bundle members by relative path, validate
every consumed artifact, and dispatch explicitly by report or bundle version.
Unknown major versions and dangling members MUST fail with actionable
diagnostics.

#### Scenario: Valid runset bundle
- **WHEN** atlas construction receives a valid bundle with several successful reports and recorded non-success entries
- **THEN** it consumes each successful report exactly once and preserves the non-success entry states as workflow diagnostics

#### Scenario: Unknown report major
- **WHEN** an input member declares an unsupported report major version
- **THEN** the operation returns the shared invocation or input failure class and identifies the unsupported member without silently coercing it

#### Scenario: Dangling bundle report
- **WHEN** a bundle references a missing or hash-mismatched report
- **THEN** the operation fails validation and does not construct an apparently complete atlas

### Requirement: Canonical atlas and derived-output ownership
Atlas JSON SHALL remain the canonical report-set machine artifact. SQLite,
Markdown, query output, structural diffs, reviewer cards, and workflow
summaries MUST remain deterministic derived projections that preserve report
identity, evidence links, authority, confidence, partial states, and nonclaims.

#### Scenario: Finding evidence survives atlas construction
- **WHEN** a source report contains a finding with typed evidence references and authority metadata
- **THEN** the atlas and applicable cards preserve or resolvably reference those fields without promoting their authority

#### Scenario: Derived artifact regeneration
- **WHEN** derived SQLite, Markdown, card, or workflow artifacts are deleted and regenerated from the same normalized atlas
- **THEN** their normalized semantic content is identical

### Requirement: Bounded structural diff ownership
The installed diff operation SHALL compare the existing normalized atlas row
categories only. It MUST NOT implement theorem-surface semantic comparison,
infer mathematical strengthening or weakening, inspect git refs, mutate a
checkout, or replace the retained theorem-changelog and Review Radar owners.

#### Scenario: Two explicit atlas inputs
- **WHEN** a caller supplies supported before and after atlas artifacts
- **THEN** the operation reports deterministic added, removed, and changed structural rows using the existing atlas diff contract

#### Scenario: Git reference supplied as an atlas path
- **WHEN** a caller supplies a git reference or repository revision where an explicit atlas artifact is required
- **THEN** the operation returns an actionable invocation error and performs no checkout or git mutation

#### Scenario: Theorem statement change is present
- **WHEN** input reports contain declaration surfaces whose theorem statements differ
- **THEN** this generic atlas operation preserves available rows but does not classify semantic strengthening, weakening, or proof-only change

### Requirement: Bounded canned query surface
The installed query operation SHALL expose the existing named canned
report-set queries with deterministic parameters and output schemas. It MUST
NOT accept natural-language queries as an alternate analysis path or silently
execute arbitrary SQL unless a separately documented existing SQLite boundary
explicitly permits it.

#### Scenario: Named canned query
- **WHEN** a caller selects a supported hotspot, recurring declaration, review-region, proof-pressure, evidence-gap, or low-confidence-join query
- **THEN** the CLI returns the existing query's rows in deterministic order with selected and omitted counts

#### Scenario: Unknown query
- **WHEN** a caller requests an unknown canned query name
- **THEN** the CLI returns the shared invocation-error exit class and lists the supported names

### Requirement: Report-set stream and exit discipline
Every installed report-set operation SHALL follow the shared public CLI
contract for output selection, stdout/stderr separation, signal handling, and
exit classes. JSON stdout MUST contain exactly one selected machine document,
and diagnostics or progress MUST be emitted only on stderr.

#### Scenario: JSON atlas on stdout
- **WHEN** atlas construction succeeds with JSON selected on stdout
- **THEN** stdout contains exactly one valid atlas document and no progress, card, Markdown, or diagnostic text

#### Scenario: Query input failure
- **WHEN** a query input is unreadable or schema-invalid
- **THEN** the operation writes an actionable diagnostic to stderr, emits no misleading successful document, and returns the shared operational-failure exit class

#### Scenario: Interrupted report-set operation
- **WHEN** a caller interrupts an installed operation
- **THEN** the command preserves the conventional signal-derived status and leaves no partially published output presented as complete

### Requirement: Deterministic installed-workflow acceptance
Required report-set gates SHALL install a clean-candidate distribution and run
atlas, query, diff, cards, and workflow operations from outside the checkout
against tracked portable report and bundle fixtures. The gates MUST verify
schema validity, library parity, relative-path portability, deterministic
normalized output, evidence-reference integrity, and clean stdout/stderr.

#### Scenario: Portable end-to-end workflow
- **WHEN** the installed acceptance gate builds an atlas from a portable bundle and derives all supported projections
- **THEN** the atlas report count matches the successful bundle entries, all references resolve, every output validates, and repeated normalized output is identical

#### Scenario: No source tree available
- **WHEN** the installed acceptance environment contains the wheel and fixture bundle but not the Ladon repository or its scripts directory
- **THEN** every supported report-set operation still completes successfully
