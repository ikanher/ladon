## ADDED Requirements

### Requirement: Semantic extraction is versioned and framed
The Lean helper SHALL implement `ladon-lean-semantic-v1` framed NDJSON with protocol, operation, request, and module identities and ordered start, row, end, and summary frames.

#### Scenario: Complete stream is received
- **WHEN** a helper extracts a requested module successfully
- **THEN** the collector validates frame order and terminal counts before accepting the artifact as complete

### Requirement: Extraction preserves module ownership and completeness
The helper MUST emit declarations owned by the requested module plus explicit external symbol references and MUST NOT repeat the entire imported environment for each module.

#### Scenario: Imported declaration is referenced
- **WHEN** an owned declaration depends on a declaration from an import
- **THEN** the stream contains the owned declaration and an external symbol reference without claiming ownership of the import

### Requirement: Expression keys remain non-authoritative
The helper SHALL emit versioned exact structural fingerprints and coarse search-shape keys and every consumer MUST treat them as candidate evidence rather than definitional equality.

#### Scenario: Fingerprints coincide
- **WHEN** two stored rows share a search-shape key
- **THEN** the system still requires Lean verification before reporting semantic applicability

### Requirement: Failures are supervised and honest
Timeout, cancellation, malformed frames, duplicates, missing summaries, and process failure SHALL terminate the process group and produce bounded partial/unavailable evidence.

#### Scenario: Stream ends before summary
- **WHEN** validated row prefixes arrive but no terminal summary is received
- **THEN** the artifact is partial and cannot populate a complete semantic generation
