## Purpose
Help callers judge whether indexed declarations cover the current working tree and distinguish exact matches from lexical suggestions during active editing.

## ADDED Requirements

### Requirement: Source changes are inspectable
Verified status and name search SHALL report added, changed and removed supported source counts relative to the queried generation, with deterministic bounded path samples, explicit truncation and an opt-in detailed listing. Supported untracked Lean files SHALL participate in the same source-discovery rules as full builds.

#### Scenario: Untracked module appears after publication
- **WHEN** a supported untracked module is added after an index build
- **THEN** verified status reports it as added and name search reports that the generation omits current sources

#### Scenario: Changed and removed files
- **WHEN** one indexed file changes and another is deleted
- **THEN** both categories are counted independently and a bounded listing cannot imply that its samples are exhaustive

### Requirement: Query staleness impact is conservative
Query diagnostics SHALL distinguish a changed selected population, a proven unchanged selected population and unknown relevance. Namespace/path hints SHALL be labelled lexical hints and SHALL NOT certify the absence of relevant declarations in changed files.

#### Scenario: Unqualified identifier has no exact match
- **WHEN** an unqualified query misses an exact name and current sources differ
- **THEN** the result reports the exact miss and source changes without claiming an unrelated path sample proves the query unaffected

### Requirement: Exact misses and fallback suggestions are distinct
Identifier-shaped queries SHALL report exact-match availability in the requested scope separately from returned lexical suggestions. Text SHALL place stale or unchecked limitations before suggestions; JSON SHALL preserve existing result collections and add explicit match classification and exact-count scope.

#### Scenario: Stale generation returns four similar names
- **WHEN** an identifier has no exact match in a stale generation but four lexical suggestions exist
- **THEN** text states zero exact matches before separately labelled suggestions and JSON identifies their fallback basis

#### Scenario: Stored-only search
- **WHEN** a caller chooses stored freshness
- **THEN** the result prominently says current sources were not checked, emits no invented live delta and performs no implicit source verification or rebuild

### Requirement: Generation identity meanings are explicit
The stored generation identity SHALL identify the rows being read; the current generation identity SHALL identify freshly observed supported inputs, not another database publication. Unchanged supported inputs SHALL produce equal identities immediately after publication. Differences SHALL have a supported-input reason or an explicit unknown/integrity diagnostic.

#### Scenario: Build then status without edits
- **WHEN** a build succeeds and supported inputs remain unchanged
- **THEN** immediate status and verified name search are fresh with matching stored and current generation identities

#### Scenario: Repository changes during observation
- **WHEN** a source inventory changes during build or freshness verification
- **THEN** the operation rejects the unstable observation or reports its instability and cannot certify a mixed inventory as fresh

### Requirement: Routine status is concise
Default text status SHALL foreground freshness, generation identity meanings, size and applicable budgets, declaration/module counts, source changes and publisher state. Detailed per-object storage and schema inventories SHALL remain explicitly accessible; existing JSON fields SHALL remain compatible.

#### Scenario: Large schema inventory
- **WHEN** status inspects a large index
- **THEN** routine text does not expand every schema/storage object and the output explains how to request the detailed inventory
