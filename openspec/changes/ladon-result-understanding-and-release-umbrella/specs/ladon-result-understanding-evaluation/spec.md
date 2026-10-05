## ADDED Requirements

### Requirement: Qualitative usage feedback precedes comparative metrics
Motivated by [Responsible Release of AI-Generated Mathematics](https://agmai.org/general-sep29/) (2026-09-29), §1 and §2.B Step II, the system SHALL support reproducible LLM usage reports for claim comprehension and lemma reuse. Per user direction on 2026-10-02, comparative metrics, held-out corpora, and human-cohort evaluation SHALL remain deferred and SHALL NOT block implementation. Interpretation remains traceable through `../../sources.md`.

#### Scenario: An LLM reports confusing output
- **WHEN** an agent encounters ambiguous or missing information during a development task
- **THEN** the report retains the task, exact command and relevant output, friction, workaround, suggested change, and reproduction status

### Requirement: Feedback does not promote authority or measured benefit
Reports SHALL distinguish usability observations from suspected correctness problems. Correctness findings SHALL be checked against source or explicit Lean observations before being treated as confirmed. Model self-report SHALL NOT establish human understanding, external-benefit improvement, independent review, or release qualification.

#### Scenario: An agent says a checked theorem proves a stronger informal claim
- **WHEN** that conclusion appears in a usage report
- **THEN** it remains a suspected interpretation issue until the exact statement, assumptions, and evidence are inspected, without inheriting checker authority

### Requirement: Development scenarios preserve difficult and failed cases
The development scenario inventory SHALL cover exact links, additional assumptions, incomplete mappings, stale reviews, unresolved evidence, and reusable lemmas as those features become available. Reports SHALL retain failed attempts and unavailable operations. Attribution and incomplete attempt-population scenarios SHALL join the full feedback pass.

#### Scenario: A needed operation is not implemented
- **WHEN** an agent cannot resolve canonical evidence through the offline validator
- **THEN** feedback records the limitation and does not substitute schema validation for theorem checking

#### Scenario: A guide references assessments in the reader fixture
- **WHEN** the reader is told that component assessments are supplied
- **THEN** the fixture includes the explicitly permitted revision-bound companion or the explanation discloses its absence
- **AND** prior bundles and measurements remain unchanged historical evidence

#### Scenario: Real records have no review population
- **WHEN** the real exposition has zero guide or correspondence reviews
- **THEN** stale-review behavior uses a separately labeled synthetic variant and does not fabricate actual review of the exposition

### Requirement: Reader tasks end in explicit new-goal application
The first qualitative alpha SHALL retain an ordinary read/find/check attempt
using a precise new goal and ordered local context, including a valid proposed
application and a nearby missing-prerequisite case. Readers SHALL receive ordinary
materials without the evaluator answer key or a preselected lemma name. Exact
commands, outputs, failures, interventions and candidate/environment/resource
observations SHALL be retained. Missing prerequisites SHALL remain obligations or
rejected applications rather than verdicts that a goal is false.

#### Scenario: A supporting lemma requires a boundary-sign premise
- **WHEN** a reader proposes that application without supplying its required boundary-sign premise
- **THEN** an explicit Lean operation records the unresolved or rejected application separately from the stored theorem's checking evidence
- **AND** a successful attempt in the complete context is bound to its own goal and environment

### Requirement: Same-guide comparison isolates the tool contribution qualitatively
A fresh plain-tooling reader context SHALL receive the same exposition, Lean
sources, authored guide, claim map and supplied evidence as the Ladon reader.
Original attempts SHALL precede repairs and remain immutable. A bounded
repair-and-retest cycle SHALL report concrete decisions, navigation assistance or
error avoidance rather than infer benefit from curation or favorable self-report.
Quantitative metrics and human cohorts SHALL remain deferred.

#### Scenario: Standard tooling achieves the same useful result
- **WHEN** the same-guide comparison shows no concrete contribution from Ladon while adding latency or metadata work
- **THEN** the feedback recommends stopping result-layer expansion and redirecting attention to core search/check rather than claiming general improvement

#### Scenario: The end-to-end task fails at environment or discovery
- **WHEN** setup, discovery or explicit candidate checking blocks completion
- **THEN** the recorded next work prioritizes that dependency over additional release features and preserves the failed attempt

### Requirement: Installed correctness remains required
Core alpha acceptance SHALL exercise the ordinary installed CLI outside the source checkout with offline inspection and separately attributable pinned real-Lean evidence where semantic operations are claimed. Artifact-only validation SHALL NOT require Lean. Mocks SHALL NOT establish semantic acceptance.

#### Scenario: An offline schema test passes
- **WHEN** the manifest validator accepts declared identities and references without loading Lean evidence
- **THEN** only the offline milestone can pass and canonical targets remain unresolved

### Requirement: Focused application and exposition tasks are separate
The next development evaluation SHALL run a short application task and a short
exposition task separately before combining them. Application evidence SHALL
include preserved source goal/context, discovery without a preselected name,
contextual residuals and requested final replay. Exposition evidence SHALL include
a correct passage and an evaluator-labelled synthetic alteration with an omitted
assumption or broadened conclusion, including false-alarm outcomes. Reader-visible
identifiers SHALL be neutral and SHALL NOT reveal which cases were altered.

#### Scenario: The application task reaches a missing prerequisite
- **WHEN** the nearby application remains incomplete
- **THEN** the report retains its exact residual and context separately from the completed case's compiler replay

#### Scenario: A correct passage is supplied as a control
- **WHEN** the exposition reader evaluates the control and altered passage
- **THEN** the report records unsupported alarms on the control and evidence for each proposed correction
- **AND** failure to verify an alteration alone does not establish that it is false

### Requirement: Recording is external to ordinary reader work
Evaluation recording SHALL capture operations automatically outside the reader's
normal task responsibilities. Reader configuration and competent baseline Lean
operation SHALL be preflighted and frozen before comparison, with identical
guide/evidence inputs. Missing or unobserved activity SHALL remain disclosed and
SHALL NOT become a complete population or a model-configuration diagnosis.

#### Scenario: A reader performs an operation outside the capture boundary
- **WHEN** activity cannot be accounted for by the external recorder
- **THEN** the report discloses that gap without relying on the reader's self-count to assert complete command coverage

#### Scenario: A reader omits requested replay
- **WHEN** the task remains incomplete despite a successful intermediate check
- **THEN** the omission remains an outcome of that configuration and task, without concluding that its reasoning level caused the failure

### Requirement: Expansion follows a concrete mathematical contribution
Continuation SHALL identify concrete preserved premises, avoided wrong
applications, reduced goal reconstruction or supported paragraph corrections.
Same-guide ordinary-tool outcomes SHALL remain visible. A structurally different
small project SHALL follow development-fixture success before generality claims;
release features and larger benchmarks SHALL NOT be prerequisites.

#### Scenario: Application contributes no useful distinction from native tools
- **WHEN** the same-guide baseline achieves the useful outcome without additional error prevention from Ladon
- **THEN** the decision considers narrowing standalone search/check and prioritizing correspondence/exposition without claiming superiority

#### Scenario: Exposition only repeats the authored guide
- **WHEN** no correction or useful review distinction is established
- **THEN** the layer remains optional rather than expanding merely to complete the roadmap

### Requirement: Integration gates remain independent of feedback
Canonical evidence integration and full exits SHALL require the authority-safe and verified-discovery receipts recorded in `../../children/dependency-ledger.json`. Independent artifact-only validation SHALL be allowed experimentally without becoming an upstream gate dependency. Qualitative feedback SHALL replace the current core/full comparative evaluation milestones without satisfying external-benefit readiness requirements.

#### Scenario: Prerequisite receipts are missing
- **WHEN** the offline validator is usable but full prerequisite receipts are absent
- **THEN** offline development and feedback can proceed while canonical integration and the full claim-correspondence exit remain gated

### Requirement: Frozen development baselines retain their original outcomes
Completed qualitative baselines SHALL retain input inventories, model/manual work boundaries, candidate identities, commands, outputs and limitations. Later improvements SHALL be compared without rewriting the original baseline or treating it as held-out evaluation data.

#### Scenario: A later candidate is compared with the fixed-epoch baseline
- **WHEN** the frozen exposition baseline is replayed against another installed candidate
- **THEN** input identities and original expected outcomes remain unchanged and behavior changes are recorded as explicit comparison results
- **AND** successful capture of an unavailable operation does not count as implementation of that operation or completion of the core alpha exit

#### Scenario: A boxed-statement inventory is complete
- **WHEN** an inventory includes every labelled theorem-like environment while excluding unboxed assertions and proof steps
- **THEN** its completeness is limited to that declared scope and component counts do not become a proof-coverage score

### Requirement: Future metrics require a separate frozen protocol
If comparative evaluation resumes, it SHALL define pinned cases, independent labels, valid alternatives, comparable baselines, budgets, missing-data rules, and promotion criteria before held-out execution. Qualitative usage scenarios SHALL be treated as development data rather than uncontaminated held-out evidence.

#### Scenario: A development feedback case becomes a benchmark
- **WHEN** the same case was used to tune the implementation
- **THEN** it cannot support an unqualified held-out benefit claim

### Requirement: Diagnosis tasks exclude evaluator answers
Unreviewed-paragraph tasks SHALL use a neutral derivative fixture without
prewritten case verdicts, proposed repairs or answer-revealing case-specific
receipt citations. Both arms SHALL receive the same legitimate guide and
mathematical evidence. Original authored engineering controls SHALL remain
separate and SHALL NOT establish independent detection or repair.

#### Scenario: A passage is broadened beyond supplied formal coverage
- **WHEN** the reader evaluates a neutral unreviewed paragraph
- **THEN** its actual diagnosis and minimally revised paragraph are retained without supplying the evaluator's correction
- **AND** conventional conclusions can remain while their formalization status is corrected

#### Scenario: A correction adds a hypothesis
- **WHEN** the revised paragraph or formal statement adds a missing premise
- **THEN** the record identifies the narrowing and preserves the original stronger statement separately
- **AND** checking the new statement does not complete the old goal

### Requirement: Both arms have competent ordinary Lean exploration
The next comparison SHALL offer ordinary goal, source, search and Lean checking
tools in both arms, adding Ladon only in the augmented arm. The declared search
population and setup costs SHALL be retained; answer-specific owner selection
SHALL NOT be called unassisted discovery. Reader/tool configuration and working
baseline SHALL be preflighted and frozen before the sessions.

#### Scenario: An operator prepared a one-owner index
- **WHEN** that owner was selected using prior knowledge of the expected lemma
- **THEN** it remains an intervention rather than evidence of ordinary discovery

#### Scenario: The nearby incomplete case has a different proof
- **WHEN** a reader checks an alternative proof of the unchanged original goal under the declared trust policy
- **THEN** it can succeed rather than being forced to reproduce the evaluator's expected residual

### Requirement: First attempts and intervention boundaries remain visible
The next benefit test SHALL retain its first attempts and separately identify
assisted continuations or targeted repair/retests. Actual proof or precise
residual, original/revised paragraph, matched ordinary-tool work and complete
failure/intervention records SHALL determine the next review. Repeated changes
to prompts or model configurations SHALL NOT select a favorable outcome while
discarding earlier failures.

#### Scenario: A tool defect blocks the first attempt
- **WHEN** a bounded targeted repair enables a later retest
- **THEN** the original failure and changed candidate/configuration remain separately identified

### Requirement: Known correspondence tasks preserve the original mathematical target
A bounded known-gap task SHALL freeze its intended formal rendering and budget
before attempts. Both configurations SHALL retain competent ordinary Lean and
the same mathematical curation; Ladon SHALL remain optional. Checked calibration
identity and horizon/constant translation SHALL be explicit. Conditional or
narrowed results SHALL remain separate from original-target completion, and an
offset bridge SHALL NOT promote sibling leading-order coverage. Mathematical
success SHALL remain distinct from command-surface or artifact-maintenance value.

#### Scenario: Fixed-epoch offset bridge succeeds with ordinary tools
- **WHEN** the intended offset specialization is checked but existing Ladon adds no concrete handoff contribution
- **THEN** the offset proof and attributed exposition update remain mathematical results
- **AND** the decision consolidates standalone interfaces rather than launching another uptake challenge

#### Scenario: Calibration identity is supplied as a new hypothesis
- **WHEN** an attempted bridge requires an extra calibration-equivalence premise
- **THEN** its conditional result cannot complete the preserved original statement or promote its coverage
