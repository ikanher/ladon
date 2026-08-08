## ADDED Requirements

### Requirement: Exact theorem selectors produce a complete evidence dossier
The system SHALL return a versioned theorem dossier that keeps Lean declaration identity, ProofIR attachments, surfaces, claims, replay evidence, obligation context, lineage, diagnostics, coverage, and nonclaims in separate sections.

#### Scenario: Exact attached theorem
- **WHEN** a theorem has one uniquely selected declaration attachment, related claims, exact replay provenance, and DAG context
- **THEN** one query returns every section with explicit relation methods, source anchors, generations, freshness, status, and authority

#### Scenario: Explicit unattached surface
- **WHEN** a surface explicitly names the theorem but has no selected declaration attachment
- **THEN** it appears as unattached quoted evidence and is not merged into attached theorem evidence

### Requirement: Dossier identity joins are conservative
The system SHALL admit theorem evidence only through exact declaration identity, selected attachment rows, or explicit surface declaration names and SHALL reject filename, description, guarantee-text, basename, and proximity inference.

#### Scenario: Nearby CDC artifacts
- **WHEN** CDC artifacts and DAG context are present near `nonempty_indexedCycleDoubleCover` but no surface explicitly identifies it
- **THEN** the dossier reports context-only evidence and no theorem attachment

#### Scenario: Duplicate declaration names
- **WHEN** several declarations share a short name and source evidence does not uniquely select one
- **THEN** the dossier reports ambiguity and selects none

### Requirement: Evidence sections preserve authority boundaries
The system SHALL quote source statuses and authorities without promoting replay success, checker reports, ProofIR claims, or attachment confidence into Lean theorem truth.

#### Scenario: Successful replay of conditional claim
- **WHEN** replay returns zero for an artifact containing a conditional claim
- **THEN** replay is successful while the claim remains conditional

### Requirement: Dossier queries are bounded and deterministic
The system SHALL use parameterized indexed SQL, deterministic ordering, per-section caps, output-byte limits, and explicit truncation metadata.

#### Scenario: High-cardinality theorem evidence
- **WHEN** a theorem relates to more rows than one section permits
- **THEN** the result is stable across repeated queries and names the controlling cap and omitted count
