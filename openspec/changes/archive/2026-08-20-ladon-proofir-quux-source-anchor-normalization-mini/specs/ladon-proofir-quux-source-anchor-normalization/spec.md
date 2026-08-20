## ADDED Requirements

### Requirement: Source hash alias supports hash joins

The ProofIR bridge SHALL treat `sourceHash` as an alias for `contentHash` during
source-hash attachment joins.

#### Scenario: Alias hash matches declaration content hash

- **WHEN** a bridge surface has `sourceHash` and the matching Ladon declaration
  row has the same content hash
- **THEN** the bridge emits `exact_source_hash_decl`

### Requirement: Nested source anchors are preserved conservatively

The bridge SHALL normalize nested `sourceAnchor` rows into attachment metadata
without promoting them to content-hash joins unless compatible content-hash
evidence exists.

#### Scenario: Line anchor joins without content hash

- **WHEN** a surface has a nested source anchor with declaration name, repository
  path, and start line, and the Ladon declaration row has the same declaration,
  source path, and starting line but no matching content hash
- **THEN** the bridge emits a low-confidence source-line anchor join instead of
  `exact_source_hash_decl`

### Requirement: Source-anchor joins remain warning routes

Source-line anchor joins SHALL be marked warning-only and SHALL be summarized in
low-confidence atlas workflow rows.

#### Scenario: Workflow receives source-line anchor join

- **WHEN** a bridge report contains a `source_line_anchor_decl` join
- **THEN** reviewer workflow treats it as low-confidence review context
