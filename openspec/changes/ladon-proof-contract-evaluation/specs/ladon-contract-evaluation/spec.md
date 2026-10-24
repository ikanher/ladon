## Purpose

Reproducible evaluation of contract analysis, source fidelity and independent discovery. This capability supports bounded prose–formal auditing with explicit evidence and limitations.

## ADDED Requirements

### Requirement: Separate capability tracks
Evaluation SHALL score supplied-contract analysis, source production and unfamiliar-source discovery separately, with fixed denominators, actual formal counterparts and explicit unsupported cases. Known-answer cases SHALL remain in a development partition.

#### Scenario: Curated cases all pass
- **WHEN** the analyzer classifies supplied contracts correctly but source-production cases fail
- **THEN** the report credits analysis correctness and does not claim end-to-end discovery success

### Requirement: Frozen baseline and runtime
Comparisons SHALL freeze exact local-checkout runtime bytes, dependencies, toolchains, corpus, model configuration, order and budgets for each arm. A commit ID alone SHALL NOT represent a dirty working tree.

#### Scenario: Baseline includes local edits
- **WHEN** the current checkout contains uncommitted runtime changes before implementation
- **THEN** the baseline manifest and launcher preserve those exact bytes rather than substituting the last commit or pip package

### Requirement: Independent answer custody
Held-out discovery inputs SHALL exclude answer labels, contract annotations, selected fault locations and answer-derived mappings. First outputs SHALL be frozen before independent adjudication; exposure SHALL invalidate a blind claim.

#### Scenario: Auditor reads the key
- **WHEN** an access incident exposes a reference answer before the first report is frozen
- **THEN** the run is marked contaminated and cannot satisfy the blind-discovery gate

### Requirement: Complete measurement
Reports SHALL retain case-level detections, false accusations, missed faults, justified controls, abstentions, extraction failures, checker attempts, time and memory for both arms. Timeouts and unsupported cases SHALL remain in the denominator.

#### Scenario: A hard case exhausts memory
- **WHEN** a case stops at its configured RSS limit
- **THEN** the report retains the case and resource failure instead of replacing it with an easier case

### Requirement: Predeclared promotion rule
A broader paper trial SHALL require passing the 24-case analysis and 12-case production gates and an independent 12-case discovery arm with at least four of six confirmed faults, five of six justified controls, zero false accusations, and one more confirmed fault than baseline within equal budgets.

#### Scenario: No incremental detection
- **WHEN** the enhanced arm meets its absolute counts but finds no additional confirmed fault over baseline
- **THEN** the report does not recommend a broader trial on an improvement claim

### Requirement: Negative result and preservation
Evaluation SHALL preserve original reports and previous experiment directories and publish failed, blocked or inconclusive gate outcomes. Infrastructure completion SHALL remain distinct from detection benefit.

#### Scenario: Independent custody unavailable
- **WHEN** a held-out answer set cannot be kept independent of auditors
- **THEN** the track is blocked or explicitly nonblind and detection benefit remains unestablished
