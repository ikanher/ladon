## ADDED Requirements

### Requirement: Portable overclaim fixtures
The system SHALL include portable fixtures for the reviewed overclaim classes
without depending on private sibling repositories.

#### Scenario: Closed claim with imported finite-window evidence fixture
- **WHEN** the route-audit fixture advertises a Lean-closed claim whose finite-window premise has imported interval-certified authority
- **THEN** the expected diagnostics include `ladon.claim.closed_with_imported_evidence`

#### Scenario: Arbitrary-neighbor overclaim fixture
- **WHEN** the route-audit fixture advertises arbitrary-neighbor event DP while the primary theorem surface records sampled-null event DP
- **THEN** the expected diagnostics include `ladon.claim.endpoint_scope_overclaim`

#### Scenario: All-Lean scalar replay overclaim fixture
- **WHEN** the route-audit fixture advertises all-Lean scalar replay while a scalar row has imported, interval-certified, diagnostic, smoke, or unchecked authority
- **THEN** the expected diagnostics include `ladon.evidence.authority_mismatch`

### Requirement: Portable positive fixtures
The system SHALL include portable fixtures for scoped and honestly conditional
routes so the audit does not learn only negative examples.

#### Scenario: Scoped sampled-null route is honest
- **WHEN** a fixture claim advertises sampled-null event DP and the primary theorem surface also records sampled-null event DP
- **THEN** the expected diagnostics do not include `ladon.claim.endpoint_scope_overclaim`

#### Scenario: Imported seam is honestly labeled
- **WHEN** a fixture claim advertises conditional external evidence and lists the imported premise in `allowedExternalEvidence`
- **THEN** the expected diagnostics do not include `ladon.claim.closed_with_imported_evidence`

### Requirement: Fixture source evidence
Route-audit fixtures SHALL include enough source evidence to test primary theorem
attachment confidence and weak-attachment warnings.

#### Scenario: Primary theorem has source hash
- **WHEN** a fixture primary theorem surface includes declaration name, source path, source range, and content hash
- **THEN** the route-audit test can assert source attachment confidence separately from authority status

#### Scenario: Primary theorem only has a basename
- **WHEN** a fixture primary theorem surface only joins by basename
- **THEN** the route-audit test expects a weak attachment warning and does not treat the surface as strong evidence

### Requirement: Packet validation clarity
Future review-packet validation summaries SHALL distinguish skipped source
repository paths from forbidden archive entries.

#### Scenario: Source scan skips cache paths
- **WHEN** packet generation skips `__pycache__`, `.pytest_cache`, or other cache paths from the source repository
- **THEN** validation summary records them under skipped source paths rather than forbidden archive entries

#### Scenario: Archive contains forbidden path
- **WHEN** a generated archive actually contains a forbidden cache or build path
- **THEN** validation summary records it under forbidden archive entries and the packet validation fails
