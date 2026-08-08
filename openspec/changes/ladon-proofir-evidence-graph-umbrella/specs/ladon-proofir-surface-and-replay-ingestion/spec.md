## ADDED Requirements

### Requirement: Admitted surface inputs are normalized transactionally
The system SHALL normalize only versioned `proofir_bridge_index` and
`proof_ir_lean_surface_bundle` inputs into artifact-owned surface, claim, and
surface-claim rows and SHALL preserve their quoted source, authority, trust,
replay-boundary, and nonclaim metadata.

#### Scenario: Lean surface bundle
- **WHEN** a supported bundle contains a valid source-anchored theorem surface
- **THEN** one artifact-owned surface and its quoted claim are stored with the exact surface ID, claim ID, declaration name, source path/range/hash, authority, proof trust, and replay boundary

#### Scenario: Compact claim without surface
- **WHEN** a compact bridge index contains a valid claim not referenced by a surface
- **THEN** the claim remains stored under its artifact and is not silently dropped or attached to a declaration

#### Scenario: Unsupported lookalike
- **WHEN** an artifact has surface-like fields but an unsupported artifact kind
- **THEN** it remains catalog-only and structural similarity does not activate the surface adapter

### Requirement: Replay provenance remains a separate evidence fact
The system SHALL normalize supported `proof_ir_lean_replay_provenance` artifacts
as quoted replay runs without replacing or upgrading a surface's extractor
replay boundary, claim status, or authority.

#### Scenario: Successful repository-local build
- **WHEN** a surface says `not_replayed_by_extractor` and a related provenance artifact records `lake build` return code zero
- **THEN** a query returns both facts separately with repository scope, dirty state, command, toolchain versions, guarantee, authority interpretation, and nonclaims

#### Scenario: Failed repository-local build
- **WHEN** a provenance artifact records a nonzero return code
- **THEN** the replay run is reported as failed evidence without marking the surface or theorem false

### Requirement: Replay relationships require exact artifact evidence
The system SHALL relate replay provenance to a bundle only when the referenced
repository-relative path and full bundle content hash match a cataloged bundle,
and SHALL relate only surface IDs owned by that exact bundle.

#### Scenario: Exact bundle and surface coverage
- **WHEN** provenance names a matching bundle hash and 18 surface IDs owned by that bundle
- **THEN** one exact artifact relationship and 18 replay-surface relationships are stored

#### Scenario: Stale bundle hash
- **WHEN** the referenced bundle path exists but its current hash differs from the provenance hash
- **THEN** the provenance artifact is retained, the relation is diagnosed stale, and no active replay-surface coverage is claimed

#### Scenario: Foreign surface ID
- **WHEN** provenance lists a surface ID not owned by its exact referenced bundle
- **THEN** that surface relationship is rejected and reported without attaching it to a same-named surface in another artifact

### Requirement: Missing provenance is not failed provenance
The system SHALL distinguish absent replay provenance, stale provenance,
successful replay, failed replay, and unsupported replay evidence in coverage
and query results.

#### Scenario: Surface without provenance
- **WHEN** a normalized surface has no matching replay artifact
- **THEN** its replay coverage is `not_observed` and not `failed`

#### Scenario: Quux coverage oracle
- **WHEN** frozen fixtures model 63 surfaces with exact provenance for 52
- **THEN** coverage reports 52 related and 11 not observed without status promotion

### Requirement: Derived aggregates do not duplicate source surfaces
The system SHALL treat downstream bridge snapshots and architecture indexes as
derived/catalog evidence unless a dedicated adapter explicitly owns their
semantics.

#### Scenario: Aggregate and source bundle both configured
- **WHEN** a downstream aggregate copies a surface already owned by a configured source bundle
- **THEN** the source surface is counted once and the aggregate creates no second primary surface row

### Requirement: Surface and replay storage is constrained and indexed
The system SHALL enforce artifact ownership, unique surface/claim identities,
valid relationship endpoints, bounded quoted fields, and named indexes for
surface ID, claim ID, declaration name, source path/hash, replay bundle, and
replay surface lookups.

#### Scenario: Conflicting duplicate surface
- **WHEN** one artifact repeats a surface ID with different normalized content
- **THEN** transactional ingestion rejects the artifact and preserves the prior active generation

#### Scenario: Indexed theorem surface lookup
- **WHEN** a stored query filters by declaration name and source path
- **THEN** its query plan uses the required surface lookup index
