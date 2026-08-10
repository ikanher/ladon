## ADDED Requirements

### Requirement: Incremental projection resolves the database union incoming batch
Projection SHALL validate every reference against the union of previously validated persisted artifacts and the complete incoming atomic batch.

#### Scenario: Check run is projected first
- **WHEN** a check-run artifact is committed and a derivation that references it is projected later
- **THEN** the derivation is accepted exactly when the persisted content ID and target kind satisfy the typed reference

### Requirement: Failed incoming batches are atomic
No artifact, subject, child, omission, or observation row from an incoming batch SHALL remain when reference validation or projection fails.

#### Scenario: One external reference dangles
- **WHEN** one artifact in a multi-artifact batch names a missing external content artifact
- **THEN** the transaction emits the frozen diagnostic and retains none of the batch rows

### Requirement: Evidence references are not derivation topology
Graph validation and queries SHALL distinguish premise/conclusion topology from external checker, support, and attachment evidence references.

#### Scenario: Derivation step names an external check run
- **WHEN** local premise and conclusion references close and `checkRunRef` resolves externally
- **THEN** navigation and proof-slice queries accept the derivation without rendering the check run as a proof premise

### Requirement: Query bounds and accounting are truthful
Every public query limit SHALL be a positive bounded integer and every result SHALL distinguish exact matched counts from bounded lower bounds.

#### Scenario: Negative limit
- **WHEN** a caller supplies `limit=-1`
- **THEN** the query fails with a stable invalid-limit diagnostic before SQL and never returns negative accounting fields

### Requirement: Dossiers use complete set-oriented derivation rows
The theorem dossier SHALL retrieve subjects and derivation relationships with bounded set-oriented queries and SHALL render each returned step's ordered premises, conclusion, rule, context, and checker relationship.

#### Scenario: Several subjects share derivations
- **WHEN** a dossier matches several subjects and steps
- **THEN** query count remains bounded independently of matched subject count and no returned step is represented by an ID/status stub alone

### Requirement: Artifact input references are closed
Bare or typed artifact inputs SHALL use one normalized reference family and SHALL resolve against persisted plus incoming content artifacts unless an explicit typed unresolved state is permitted.

#### Scenario: Check run names a missing environment artifact
- **WHEN** a check-run input contains a syntactically valid but absent artifact content ID
- **THEN** validation rejects it before any row is committed

### Requirement: Fingerprint schemes use one registry
The Lean worker, artifact builder, SQLite projection, semantic-candidate query, and conformance corpus SHALL use one versioned fingerprint-scheme registry.

#### Scenario: Worker statement is queried
- **WHEN** two worker artifacts contain the same supported structural statement fingerprint
- **THEN** the semantic-candidate query returns the matching candidate under that registered scheme

### Requirement: Dependent query completeness is inherited honestly
A dependent dossier section SHALL query the complete selector population or SHALL expose the parent cap as a truncation cause and decline to claim an exact total.

#### Scenario: Parent subject set is truncated
- **WHEN** unexamined subject owners may contain matching claims
- **THEN** the claims section reports `matchedExact=false`, a bounded lower count, and `truncationCause=parent-subject-cap`

### Requirement: Large set joins and ordered aggregates are portable
Bounded multi-subject queries SHALL avoid platform parameter-limit overflow and SHALL derive ordered JSON arrays from explicitly ordered relational inputs.

#### Scenario: Query reaches the public subject cap
- **WHEN** a query contains enough subjects to exceed a supported SQLite variable limit under an OR expansion
- **THEN** Ladon uses a bounded set relation and returns stable ordered premises and substitutions without exceeding the platform limit
