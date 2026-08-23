## ADDED Requirements

### Requirement: Explanation compares attributable candidate-type evidence
`proof-search explain` SHALL resolve exactly one declaration candidate and SHALL compare the requested goal only with a nonempty, non-truncated candidate type whose stored authority and freshness are reported. It SHALL NOT compare the goal with the candidate's declaration name or silently fall back to that name.

#### Scenario: Exact stored candidate type matches
- **WHEN** `Demo.proof` uniquely resolves to a fresh, non-truncated stored type `True` and the requested goal is `True`
- **THEN** structural explanation compares `True` with `True`, records the declaration and type evidence, and does not compare against `Demo.proof`

#### Scenario: Candidate type is unavailable or truncated
- **WHEN** the selected declaration has no usable type or its type text is truncated
- **THEN** explanation returns an explicit unavailable or indeterminate result naming that evidence limitation and does not report applicability

#### Scenario: Candidate lookup is ambiguous
- **WHEN** the supplied name resolves to multiple declarations without an exact disambiguating owner
- **THEN** explanation fails closed with bounded candidate diagnostics instead of selecting the first SQLite row

### Requirement: Lexical type-text discovery has an honest versioned interface
The current SQL substring shortlist SHALL be exposed through a command and result schema named for type text or signature evidence, and the unqualified `search type` interface SHALL NOT continue to imply Lean type matching.

#### Scenario: Caller uses the replacement command
- **WHEN** a caller searches a rendered or lexical signature substring
- **THEN** the result labels every row as lexical type-text evidence, reports the matched field and contribution, and states that Lean applicability was not established

#### Scenario: Caller uses the retired command
- **WHEN** a caller invokes the old unqualified `proof-search search type` command
- **THEN** Ladon exits with a stable invocation diagnostic naming the replacement rather than silently preserving the old semantics

### Requirement: Every accepted search scope constrains the population
The type-text request validator SHALL accept a scope only when its required roots and repository graph data are available, and the resulting SQL candidate population SHALL implement that scope before ranking or limiting.

#### Scenario: Module and closure scopes differ
- **WHEN** the same pattern is searched under repository, module, and import-closure scopes over a fixture with declarations inside and outside those populations
- **THEN** each result contains exactly the declarations permitted by its requested scope and records attributable omissions

#### Scenario: Required scope root is absent
- **WHEN** a caller requests module, file, namespace, imports, closure, or neighborhood scope without its required root
- **THEN** request validation rejects the operation before opening or querying the database

#### Scenario: External scope is requested
- **WHEN** the local index cannot establish a complete external type-text population for the requested pattern
- **THEN** Ladon rejects the unsupported scope or returns an explicitly unavailable population and never reuses repository results under an external label

### Requirement: Freshness requests are enforced rather than echoed
`freshness=verify` SHALL verify the current source, configuration, schema, helper, and generation identity through the shared index-freshness owner before returning candidates; `freshness=stored` SHALL remain explicitly stored metadata.

#### Scenario: Verified fresh generation
- **WHEN** current tracked inputs match the indexed generation and the caller requests verified freshness
- **THEN** the result reports fresh status plus the stored and recomputed generation identities

#### Scenario: Verification detects drift
- **WHEN** a tracked source or configuration input changes after publication
- **THEN** the result reports or rejects stale evidence according to the versioned command contract and does not label the rows verified-fresh

### Requirement: Reproduced discovery defects are installed regressions
Repository-owned tests SHALL reproduce the name/type, scope, and freshness failures against the pre-change installed distribution and SHALL exercise the repaired ordinary CLI from outside the checkout.

#### Scenario: Installed adversarial suite runs
- **WHEN** an isolated wheel is installed and the adversarial discovery fixtures invoke its console command
- **THEN** the exact candidate-type comparison, distinct scoped populations, verified generation identity, unavailable cases, migration diagnostic, exits, and nonclaims all match the new contracts
