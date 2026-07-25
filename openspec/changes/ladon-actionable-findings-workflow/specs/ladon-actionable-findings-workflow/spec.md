## ADDED Requirements

### Requirement: Inspectable finding identity and scope
Every promoted finding SHALL expose a stable finding identifier, its existing
finding kind and severity, the analysis scope that produced it, its authority,
and any available confidence metadata. This capability MUST NOT introduce a
parallel finding taxonomy or reinterpret an existing finding's severity.

#### Scenario: Finding survives presentation changes
- **WHEN** wording, text rendering order, or unrelated report rows change while the finding's semantic evidence is unchanged
- **THEN** the finding retains the same stable identifier, kind, severity, authority, and scope identity

#### Scenario: Scope is visible
- **WHEN** a finding is produced for an owner, import closure, namespace, named root, changed set, or inventory scope
- **THEN** finding inspection reports that scope explicitly rather than requiring the caller to infer it from the message

### Requirement: Resolvable evidence links
Every promoted finding MUST contain one or more typed evidence references, or
an explicit aggregate-evidence reference when no single source location is
truthful. Evidence references SHALL resolve to canonical report rows,
repository-relative source locations, or named external quoted artifacts
without copying those payloads into a second authority surface.

#### Scenario: Source-locatable evidence
- **WHEN** a finding is derived from evidence with a source path and range or line
- **THEN** the finding links to that repository-relative source evidence and preserves its source hash, authority, and confidence when available

#### Scenario: Aggregate graph evidence
- **WHEN** a finding is derived from an aggregate such as fan-in, closure size, or family recurrence
- **THEN** the finding links to the canonical aggregate row and its bounded sample evidence rather than fabricating one source line

#### Scenario: Evidence is unavailable
- **WHEN** the owning analysis cannot provide a truthful source or canonical-row reference
- **THEN** the finding records an explicit unavailable reason and MUST NOT synthesize a path, range, confidence, or stronger authority

### Requirement: Deterministic owner-relevant ordering
Finding views SHALL support deterministic owner-relevant ordering based only on
inspectable scope and evidence fields. The ordered view MUST expose its ranking
components and MUST NOT mutate the canonical findings, their kinds, their
severities, or their identifiers.

#### Scenario: Owner-local evidence is available
- **WHEN** findings from several scopes are viewed for one selected owner
- **THEN** the ordered view places directly owner-locatable evidence ahead of broader contextual aggregates and reports the factors used for that ordering

#### Scenario: Equal ranking evidence
- **WHEN** two findings have equal owner-relevance factors
- **THEN** their order is determined by documented stable keys and is identical across equivalent runs

### Requirement: Public finding filtering and exact lookup
The ordinary installed Ladon CLI SHALL support finding filtering and exact
lookup by stable, documented fields, including finding identifier. Filtering
and lookup MUST project the canonical report and MUST NOT rerun analysis,
change thresholds, or produce caller-specific results.

#### Scenario: Exact identifier lookup
- **WHEN** a caller requests a finding by a stable identifier present in a report
- **THEN** the CLI returns that canonical finding together with its scope, evidence references, authority, confidence, and available next review action

#### Scenario: Finding filter
- **WHEN** a caller filters findings by supported kind, severity, scope, authority, or repository-relative path
- **THEN** the CLI returns only matching canonical rows in deterministic order and reports the full selected and omitted counts

#### Scenario: Missing identifier
- **WHEN** a caller requests a well-formed finding identifier that is absent from the selected report
- **THEN** the CLI emits no fabricated row and returns the documented not-found diagnostic and exit behavior

### Requirement: Executable next review actions
A finding view SHALL provide a bounded suggested next review action when an
ordinary public Ladon command can inspect the referenced evidence more closely.
Suggested commands MUST be represented as structured arguments, MUST use only
caller-independent documented options, and MUST remain advisory.

#### Scenario: Further inspection is available
- **WHEN** a finding has enough root, scope, report, and evidence identity to form a narrower inspection
- **THEN** the finding view emits a structured invocation of the same public CLI that a person, script, editor, or model can execute

#### Scenario: No truthful next command exists
- **WHEN** the evidence cannot support a narrower Ladon inspection
- **THEN** the finding records that no next Ladon command is available rather than inventing an action or source target

### Requirement: Finding workflow stream and format discipline
Finding list, filter, and lookup operations SHALL follow the shared CLI output
and exit contract. Machine-readable output MUST contain only the selected
document on stdout, while progress, warnings, and diagnostics MUST be written
to stderr.

#### Scenario: JSON finding lookup
- **WHEN** a caller selects JSON output to stdout for a successful finding lookup
- **THEN** stdout contains exactly one valid JSON document and contains no progress or prose diagnostic bytes

#### Scenario: Invalid finding filter
- **WHEN** a caller supplies an unsupported field or malformed filter
- **THEN** the CLI returns the shared invocation-error exit class before producing a partial result

### Requirement: Portable evidence-link acceptance
Required finding-workflow gates SHALL run from tracked portable fixtures and an
installed clean-candidate distribution. They MUST verify deterministic lookup,
filtering, evidence resolution, text/JSON semantic parity, and absence of
dangling evidence references without requiring a sibling repository.

#### Scenario: Portable finding matrix
- **WHEN** the required fixture matrix emits each promoted finding kind covered by the product
- **THEN** every emitted finding has a resolvable typed evidence reference or an explicit aggregate or unavailable-evidence record

#### Scenario: Equivalent repeated inspection
- **WHEN** an installed CLI inspects the same normalized portable report twice
- **THEN** normalized machine output is byte-identical and all selected, omitted, authority, and evidence-reference fields agree with text output
