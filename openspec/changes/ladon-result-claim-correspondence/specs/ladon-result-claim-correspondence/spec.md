## ADDED Requirements

### Requirement: Dated source traceability
The capability SHALL cite [Responsible Release of AI-Generated Mathematics](https://agmai.org/general-sep29/) (2026-09-29), §2.B Step I.4, as motivation for informal/formal correlation. It SHALL retain the distinction between source recommendations and Ladon's engineering requirements documented in `../../../ladon-result-understanding-and-release-umbrella/sources.md`; artifact presence SHALL NOT imply source-document compliance.

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


#### Scenario: Resolving an explicitly qualified stored target
- **WHEN** the user supplies valid local canonical envelopes, an exact declaration subject reference, matching rendered/structural type identity, canonical environment and an exact source-map association
- **THEN** `ladon result resolve` reports the stored association as resolved, while checker acceptance and current working-tree freshness remain not-assessed and project revision remains producer-declared

#### Scenario: Source association is ambiguous or inconsistent
- **WHEN** multiple anchors bind the selected artifact-qualified subject, or an anchor contradicts its name or identity
- **THEN** the target remains ambiguous or unresolved without selecting another declaration by name

#### Scenario: Compact selection cannot hide invalid evidence
- **WHEN** a target filter or output cap omits some rows and another supplied envelope is invalid
- **THEN** complete-population validation fails before any success output; valid populations retain exact status totals, omission counts and an exact target-ID drill-down
