## ADDED Requirements

### Requirement: Dated source traceability
The capability SHALL cite [Responsible Release of AI-Generated Mathematics](https://agmai.org/general-sep29/) (2026-09-29), §2.B Step I.4, as motivation for informal/formal correlation. It SHALL retain the distinction between source recommendations and Ladon's engineering requirements documented in `../../sources.md`; artifact presence SHALL NOT imply source-document compliance.

#### Scenario: Inspecting the proposal's source basis
- **WHEN** a reviewer follows the capability's source reference
- **THEN** the dated URL, relevant section, Ladon interpretation, and limits of that interpretation are available without running a network-dependent test

### Requirement: Versioned claims and exact formal targets
The system SHALL validate versioned manifests with stable result IDs, content revisions, declared claim-inventory scope/coverage, claim IDs, exact supplied statements, and document locators/digests. Formal links SHALL bind exact claim revisions to qualified declarations, source/environment identities, and available artifact-qualified canonical subjects. One-to-many and many-to-one links SHALL be supported without inferring complete composite-claim coverage.

#### Scenario: Two declarations implement parts of one claim
- **WHEN** one claim maps to two declarations but its existence component has no mapping
- **THEN** both links and the unmapped component are retained and the claim is not reported as fully covered

#### Scenario: Matching names occur in different environments
- **WHEN** two declarations have the same name but incompatible source or environment identities
- **THEN** they remain distinct targets and neither receives the other's checking or review evidence

#### Scenario: Article and pinned formal archive have different coverage
- **WHEN** a current article refers to a pinned archive and the selected working-tree declaration has matching source bytes
- **THEN** article, archive and working-tree identities remain separately recorded and the source match does not inherit a fresh check or full article correspondence

#### Scenario: Offline validation receives a nonexistent declaration
- **WHEN** a well-formed manifest supplies a declaration name for which no canonical subject has been resolved
- **THEN** successful metadata validation retains not-assessed or unresolved canonical resolution and cannot assert declaration existence or acceptance

### Requirement: Link resolution is separate from correspondence review
The system SHALL distinguish resolved, ambiguous, unresolved, and stale links from not-reviewed, reviewed-aligned, reviewed-with-differences, and disputed correspondence. Fuzzy search SHALL produce only candidate links. Reviews SHALL name exact subject revisions, attributed reviewer identity and kind, method, timestamp, rationale, and comparison evidence if any. Self-reported identity SHALL NOT be presented as authenticated identity.

#### Scenario: A model proposes a plausible theorem link
- **WHEN** a model proposes a similarly named theorem and reports that it matches the claim
- **THEN** the proposal and model review remain attributable assertions and do not become exact resolution or human correspondence approval

#### Scenario: Conflicting reviews of an extra assumption
- **WHEN** reviewers disagree about whether a finiteness hypothesis preserves the informal claim
- **THEN** both reviews and the hypothesis difference remain inspectable with disputed correspondence status

### Requirement: Differences and revisions retain their evidence scope
The system SHALL attach assumption, domain, quantifier, conclusion, or scope differences to exact text/source anchors and a stated evidence basis. Syntactic comparison SHALL NOT establish semantic equivalence or inequivalence. A claim or formal-target revision change SHALL invalidate applicability of prior correspondence reviews while preserving them historically; no implicit re-approval is permitted.

#### Scenario: A checked theorem acquires a stronger hypothesis
- **WHEN** a declaration is revised to require a stronger hypothesis while an older correspondence review remains stored
- **THEN** the new revision shows an unreviewed or stale relationship and the prior review remains bound to the older statement

### Requirement: Manifests reuse canonical evidence and reject invalid identity
The manifest SHALL reference existing ProofIR and theorem evidence without inventing a new checker authority or ProofIR family. Validation SHALL reject duplicate IDs, contradictory revision bindings, unsupported versions, and dangling required internal references before index publication. Missing optional external evidence SHALL remain explicitly unresolved.

#### Scenario: Evidence is unavailable locally
- **WHEN** a valid claim references an external canonical artifact that is not present
- **THEN** inspection reports unresolved evidence and does not fetch the URL, select a similar artifact, or report checker acceptance

### Requirement: Explicit source capture observes whole-module coherence
An explicit source-capture operation SHALL publish a source map only after a
pinned, bounded compilation of frozen owner bytes reproduces the selected
canonical module and emits compatible declaration locations. It SHALL preserve
separate checking and correspondence dimensions, reject unsupported compilation
profiles and changed inputs, and keep offline resolution free of execution.

#### Scenario: A sibling declaration changes without rebuilding the owner
- **WHEN** the target name and type remain unchanged but the source module no longer reproduces the recorded compiled bytes
- **THEN** source capture emits no source map and reports a mismatch without changing the stored candidate-check result

#### Scenario: The exact source reproduces the selected stored module
- **WHEN** the supported compilation profile produces identical module bytes and a valid fresh location for the exact target
- **THEN** the emitted anchor binds the frozen source digest and location to the selected artifact-qualified declaration and environment
- **AND** compilation and temporary outputs remain under explicit resource limits outside the target build tree

#### Scenario: An imported range survives an edit
- **WHEN** an old compiled module still supplies a declaration range for changed source bytes
- **THEN** the range alone is insufficient to publish a source association
