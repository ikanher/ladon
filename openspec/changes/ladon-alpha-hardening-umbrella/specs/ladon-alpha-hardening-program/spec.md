## ADDED Requirements

### Requirement: One product interface
The alpha-hardening program SHALL preserve one shared public CLI contract whose
commands, defaults, analysis, and report payloads do not vary by caller type.

#### Scenario: Equivalent callers
- **WHEN** two callers invoke `ladon` with identical arguments and repository state
- **THEN** both invocations produce the same normalized analysis result regardless of whether a caller is a person, script, CI job, or model

#### Scenario: No role-specific surface
- **WHEN** installed public CLI help and configuration are inspected
- **THEN** they contain no model-only, agent-only, prompt-only, or hidden alternate-analysis command

### Requirement: Single rendering source
Text and JSON output MUST be derived from one validated report model and MUST
not select different findings or thresholds.

#### Scenario: Text and JSON parity
- **WHEN** text and JSON are rendered for the same completed run
- **THEN** total selected counts and phase states agree, every text-rendered row preserves its JSON identifier/severity/authority, and compact text names how many detailed rows it omits

### Requirement: Bounded child ownership
Every in-scope alpha technical-risk requirement SHALL have one authoritative
child packet, and the umbrella SHALL record dependencies without duplicating
implementation tasks.

#### Scenario: Requirement ownership audit
- **WHEN** the umbrella and child briefs are inspected
- **THEN** each in-scope technical risk maps to exactly one child owner and any reused historical packet is named as evidence or a superseded source

### Requirement: Dependency-aware implementation
The program MUST establish report and runtime foundations before promoting
elaborated declaration surfaces, and MUST benchmark stabilized behavior before
declaring the milestone ready.

#### Scenario: Declaration packet readiness
- **WHEN** elaborated declaration work is selected for implementation
- **THEN** report-contract-v2 and Lean-extraction-runtime prerequisites are complete or explicitly tracked as blockers

#### Scenario: Benchmark promotion
- **WHEN** a repaired or enriched signal is proposed for the default report
- **THEN** portable positive, negative, and boundary evidence exists in the benchmark child

### Requirement: Heuristic expansion freeze
The alpha-hardening milestone MUST NOT add a new default heuristic family
without a separate approved change and benchmark evidence.

#### Scenario: Unplanned heuristic proposal
- **WHEN** implementation discovers a possible new heuristic unrelated to a verified audit defect
- **THEN** the idea is deferred to a separate change instead of being added to an alpha-hardening child

### Requirement: Evidence authority preservation
All children SHALL keep text observations, parser candidates, Lean-elaborated
facts, and quoted external evidence distinguishable.

#### Scenario: Mixed evidence report
- **WHEN** one report contains evidence from more than one authority class
- **THEN** each row retains its backend, provenance, and authority and no ranking or renderer promotes a weaker class into a stronger one

### Requirement: Alpha readiness gate
The umbrella SHALL be complete only after every child is complete, strictly
valid, and passes its declared clean-source gates.

#### Scenario: Incomplete child
- **WHEN** any child has unchecked implementation tasks, strict validation failure, or a failing required gate
- **THEN** the umbrella remains incomplete and names that child as a blocker

#### Scenario: Machine-checked readiness
- **WHEN** the umbrella readiness command runs for an explicit tracked candidate
- **THEN** it resolves every child from either one active path or one uniquely named dated archive, validates archived artifacts in an isolated change root, checks canonical postconditions, expands milestone-qualified edges at their declared pre-close or post-archive phase, rejects invalid phase ordering, unresolvable cycles, or unattained predicates, and executes every preserved required child gate in dependency order

#### Scenario: Post-archive canonical milestone
- **WHEN** a milestone is declared `post-archive`
- **THEN** readiness cannot attain it until the owning child has closed, has one resolved archive, and its declared canonical gates pass

#### Scenario: Ambiguous or missing child history
- **WHEN** a child ID is absent from both active and archive state or resolves to multiple unexplained archives
- **THEN** readiness fails with the child ID and candidate paths instead of silently treating it as complete

#### Scenario: Archived active-ID validation command
- **WHEN** archived automation contains `openspec validate <child-id>` that only resolves active changes
- **THEN** readiness substitutes isolated validation of the archived artifacts and runs the registry's remaining commands without issuing the stale active lookup

#### Scenario: Absent publication license
- **WHEN** all technical gates pass but the project owner has not granted a distribution license
- **THEN** alpha technical readiness may complete while publication remains explicitly blocked
