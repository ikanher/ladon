## ADDED Requirements

### Requirement: Capability readiness uses a closed monotone ladder
Every advertised capability SHALL be classified as exactly `experimental`, `contract-supported`, `externally-evaluated`, or `release-qualified`, and promotion SHALL require all evidence of lower levels.

#### Scenario: Help-only optional command
- **WHEN** a capability has only parser/help coverage
- **THEN** it remains experimental and is not described as contract-supported

#### Scenario: Contract gates pass without external outcomes
- **WHEN** installed, adversarial, resource, and result-schema gates pass but no held-out evaluation exists
- **THEN** the capability may be contract-supported but not externally-evaluated

### Requirement: Readiness evidence is machine-readable and executable
The generated readiness matrix SHALL name exact tests, candidate commands, environments, resource gates, external studies, known limitations, and timestamps or revisions for every promotion claim.

#### Scenario: Referenced gate is stale or missing
- **WHEN** matrix generation cannot collect a named test or reproduce its owning candidate command
- **THEN** generation fails or demotes the capability instead of retaining the unsupported level

### Requirement: Proof-discovery evaluation uses a preregistered held-out corpus
Evaluation SHALL freeze goals, local contexts, repository revisions, toolchains, candidate-scope policy, labels, exclusions, and resource bounds before measuring Ladon.

#### Scenario: Development fixture enters the held-out set
- **WHEN** a goal used to tune ranking or implementation is proposed as held-out evidence
- **THEN** it is labeled development data and excluded from external-evaluation promotion metrics

#### Scenario: External repository is unavailable
- **WHEN** an optional held-out repository cannot be accessed in required CI
- **THEN** required portable gates remain independently decidable and external evaluation is reported unavailable rather than fabricated

### Requirement: Baselines use comparable subjects and evidence
Ladon SHALL be compared with `exact?`, `apply?`, editor search where automatable, `#check`, and `rg` on the same preregistered goals and environments, with method-specific nonclaims and comparable time/resource accounting.

#### Scenario: Baseline cannot express local context
- **WHEN** one baseline cannot consume the same subject or return the same outcome class
- **THEN** the comparison records the mismatch and does not turn missing data into a win for either system

### Requirement: Outcome metrics remain separate
Evaluation SHALL report verified candidate recall, incorrect-suggestion rate, time to first accepted candidate, scratch replay success, resource use, architecture-finding precision, and maintainer actionability separately and SHALL NOT collapse them into one quality score.

#### Scenario: Recall improves while incorrect suggestions increase
- **WHEN** a ranking change finds more accepted candidates but produces more invalid suggestions
- **THEN** both effects remain visible and readiness policy applies its preregistered thresholds independently

### Requirement: Product profiles follow measured readiness
Documentation SHALL present verified discovery as primary, architecture review as secondary, evidence/lineage as audit substrate, and optional layers as extras only to the degree supported by readiness evidence.

#### Scenario: Verified discovery has not passed external evaluation
- **WHEN** the vertical slice is contract-supported but lacks held-out outcome evidence
- **THEN** documentation identifies the intended primary direction while retaining its current readiness level and limitations
