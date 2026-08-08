## ADDED Requirements

### Requirement: Surface attachments use compatible source identity
The system SHALL generate declaration attachment candidates from compatible
source evidence and SHALL select an attachment only when the strongest
admissible match resolves to exactly one current declaration ID.

#### Scenario: Exact file hash path and declaration
- **WHEN** a surface declaration name, repository-relative path, and file hash match one indexed declaration's owning module source
- **THEN** the surface receives one high-confidence selected attachment to that declaration ID

#### Scenario: Exact compatible source range
- **WHEN** file hash is unavailable but declaration name, path, and compatible source range uniquely match
- **THEN** the surface receives a lower-confidence selected attachment with the exact match method recorded

#### Scenario: Hash subjects differ
- **WHEN** a surface provides a whole-file hash and a declaration provides only a block hash
- **THEN** the hashes are not compared as equal and cannot independently establish a high-confidence attachment

### Requirement: Ambiguous and weak matches are never selected arbitrarily
The system SHALL retain candidate evidence and diagnostics for ambiguous,
name-only, module-only, and context-only matches but SHALL NOT select the first
matching declaration row.

#### Scenario: Duplicate fully qualified candidate
- **WHEN** several declaration rows share the same fully qualified candidate name and no source evidence disambiguates them
- **THEN** the result is ambiguous with all bounded candidates listed and no selected attachment

#### Scenario: Basename-only match
- **WHEN** only a declaration basename matches a surface
- **THEN** the candidate is warning/context-only and cannot attach theorem evidence

#### Scenario: Unique strongest match among weak candidates
- **WHEN** several name candidates exist but exactly one also matches path and file hash
- **THEN** that strongest candidate is selected and the rejected candidates remain explainable

### Requirement: Source staleness is explicit
The system SHALL compare current source fingerprints with artifact source
evidence and SHALL prevent stale exact evidence from being reported as a fresh
attachment.

#### Scenario: Source file changed
- **WHEN** a surface's recorded file hash differs from the current indexed module hash
- **THEN** the surface and candidates remain queryable with a stale diagnostic but no fresh high-confidence attachment is claimed

#### Scenario: Source generation rebuilt
- **WHEN** declaration IDs change after a base-index rebuild but source evidence is unchanged
- **THEN** attachments are recomputed against the new generation rather than copied by obsolete declaration ID

### Requirement: Lineage overlays preserve separate authority
The system SHALL overlay selected declaration attachments on compatible active
theorem-lineage nodes without inserting ProofIR graph rows into the lineage
graph or presenting attachment as a proof dependency.

#### Scenario: Attached declaration is in active lineage
- **WHEN** a selected surface declaration occurs in a fresh active closure
- **THEN** theorem evidence output links the surface and lineage node while retaining separate ProofIR and Lean authority sections

#### Scenario: Lineage unavailable
- **WHEN** an exact declaration attachment exists but no compatible active lineage closure is stored
- **THEN** the attachment is returned and lineage is explicitly unavailable rather than inferred

#### Scenario: Stale lineage generation
- **WHEN** the artifact/declaration generation is current but the lineage closure is stale
- **THEN** the overlay is withheld or labeled stale according to policy without degrading the declaration attachment itself

### Requirement: Context never becomes theorem attachment by inference
The system SHALL require an explicit source-backed theorem identity for theorem
attachment and SHALL treat module, description, guarantee, result text, and
nearby artifact relationships as context only.

#### Scenario: CDC theorem negative oracle
- **WHEN** querying `Quux.Problems.CDCGeneralTheorem.DirectedMultigraph.Bridgeless.nonempty_indexedCycleDoubleCover` against current CDC artifacts that do not explicitly name it
- **THEN** no ProofIR theorem attachment is returned, while relevant module-level witnesses and conditional DAGs may be listed as unattached context with reasons

#### Scenario: Prose mentions theorem result
- **WHEN** an artifact description or guarantee resembles a theorem conclusion but has no explicit source anchor
- **THEN** no declaration or lineage attachment is synthesized

### Requirement: Attachment queries are indexed and bidirectional
The system SHALL support bounded theorem-to-evidence, declaration-to-evidence,
surface-to-declaration, and artifact-to-attachment queries with named indexes
and deterministic results.

#### Scenario: Theorem-first query
- **WHEN** a caller queries a fully qualified theorem with exact attached surfaces
- **THEN** all in-bound evidence is returned with source links, artifact identity, match method, authority, freshness, and coverage

#### Scenario: Query-plan validation
- **WHEN** declaration-name/path candidate selection and selected-attachment-to-lineage joins are explained
- **THEN** SQLite uses the prescribed attachment and declaration indexes rather than full scans
