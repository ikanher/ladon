# Spec Delta

## Purpose

Source-bound coordination and reporting of semantic-pitfall evidence. This capability retains exact evidence scope and explicit unresolved outcomes.

## ADDED Requirements

### Requirement: Explicit premise accounting for selected-theorem support

The bounded premise-accounting workflow SHALL retain the original source claim and exact selected formal judgment with its dependency-preserving context. Each formal premise, including relevant implicit and instance premises, SHALL have an identified source attribution, a checked derivation under the original assumptions, or an explicit unresolved status. Source mappings SHALL remain attributed interpretations rather than kernel-certified translations. Unavailable context coverage SHALL remain unresolved. Complete premise accounting SHALL NOT alone certify conclusion correspondence or whole-source fidelity.

#### Scenario: Formal premise is absent from the prose

- **WHEN** a selected theorem requires a premise that has neither a sufficient source attribution nor a checked derivation
- **THEN** that theorem is not sufficient recorded support for the unchanged passage, and the missing premise is reported without silently adding it or automatically declaring the passage false

#### Scenario: Premise follows from the original assumptions

- **WHEN** a premise is not stated verbatim but follows by an independently replayed derivation from the original assumptions
- **THEN** its ledger row records the exact closed obligation and evidence without treating the wording difference as a discrepancy or assuming the missing premise in its own derivation

#### Scenario: Stronger theorem premise is unnecessary

- **WHEN** the selected theorem has an unmatched premise but a separate checked proof establishes the source claim under its original assumptions
- **THEN** the report preserves the gap in the first route and the support supplied by the alternative route without inferring premise necessity or source falsity

#### Scenario: Control deliberately states a conditional assumption

- **WHEN** faithful or explicitly repaired prose includes the selected theorem's premises
- **THEN** the workflow records support under those premises with distinct source identities for repairs, without calling a legitimate conditional theorem a pitfall

### Requirement: Checked source-context route

For new source readings, the N.3 recipe SHALL freeze a source-only interpretation before candidate-theorem exposure and record later revisions. Reused exposed cases SHALL disclose prior theorem/answer knowledge and SHALL NOT count as qualification of source-only interpretation behavior. Completed support for a selected route SHALL require a consistently instantiated application and checked conclusion transfer bound to the original interpreted context and goal. Separate premise proofs or filled ledger rows SHALL NOT substitute for completion evidence. Unresolved obligations SHALL block completed support for that route while permitting a separately completed alternative route.

#### Scenario: Premise rows use incompatible assignments

- **WHEN** individually valid premise proofs use different assignments to a shared parameter
- **THEN** the workflow requires a single consistent application and cannot report completed support from the separate rows

#### Scenario: The conclusion changes its quantifier order

- **WHEN** the theorem establishes a sample-dependent almost-sure limit but the source asks for one common deterministic limit
- **THEN** the conclusion transfer remains unresolved or is separately refuted even if every theorem premise is supplied

#### Scenario: Ordinary proof succeeds but native completion rejects it

- **WHEN** a whole proof under the original source context compiles with permitted axioms but the native completion route rejects closure or replay
- **THEN** the report may record the separate ordinary Lean support while retaining the native failure; neither an empty residual list nor ordinary success supplies native completion authority

#### Scenario: Source context is explicitly hypothetical

- **WHEN** the source itself states conditional assumptions, possibly contradictory ones
- **THEN** valid conditional support does not require an added feasibility certificate, and the workflow distinguishes that support from any independent feasibility claim

### Requirement: Delivered checking path qualification

N.3 SHALL qualify one reproducible substantive query in the actual delivered environment using existing checks, with completed and unresolved outcomes. Pristine capsule inputs SHALL remain distinct from mutable working projects when replay is used. Reporting SHALL include invocation failures and time to substantive evidence, with unavailable costs explicit.

#### Scenario: Replay is pointed at an expanded project

- **WHEN** dependency or build files make a working project differ from the capsule inventory
- **THEN** the recipe uses the pristine capsule input for replay and retains inventory validation rather than accepting extra entries

#### Scenario: Safe-looking abstention hides a failed workflow

- **WHEN** omission cases remain unresolved but all faithful and derived-premise controls also receive abstention
- **THEN** qualification remains incomplete because justified positive support is required alongside avoidance of false reassurance and false accusations

### Requirement: Correction and development evidence boundaries

A scoring correction SHALL preserve the original registration, first reports, reviews, results and receipts and identify superseded aggregate interpretations in a separately versioned record. It SHALL apply the frozen categories and conditional-reading policy. Known evaluation failures reused for qualification SHALL be labeled exposed development; passing them SHALL NOT establish fresh discovery or incremental detection benefit. New comparisons SHALL require separate registration and fresh inputs after workflow qualification.

#### Scenario: Faulty passage is incorrectly called supported

- **WHEN** a report misses a fault and reassures the reader that the passage is supported
- **THEN** the correction records a missed fault/false reassurance rather than counting that act as a false accusation against supported mathematics, and recomputes the gate under the unchanged registration

#### Scenario: Reviewer metadata reveals treatment

- **WHEN** reviewer inputs reveal which arm used Ladon
- **THEN** the report discloses the limitation on treatment blinding while keeping independence, mathematical adjudication and anonymity claims distinct

### Requirement: Synthetic challenge authority

A synthetic evaluation SHALL identify its constructed provenance, independently validate fault/control/ambiguity judgments, and preserve the original formal development. Development examples SHALL remain separate from evaluation mutations. Synthetic outcomes SHALL NOT be reported as natural-error discovery or satisfy historical improvement gates retroactively.

#### Scenario: Proposed mutation is merely stronger

- **WHEN** a prose mutation asserts a stronger conclusion and its proof search fails
- **THEN** it remains unvalidated until independent mathematical evidence establishes the claimed fault or source-justification gap

#### Scenario: Related variants reveal the edit

- **WHEN** faithful and mutated passages originate from the same source
- **THEN** each scored variant is delivered in a separate fresh unit context without sibling variants, mutation diffs or correctness labels, and reporting retains their common source cluster

### Requirement: Locally reproducible challenge inputs

The challenge SHALL retain source-bound capsules and required compiled evidence under Ladon, with finite resource bounds and pinned dependencies. The donor repository SHALL remain read-only. Fresh replay and arm execution SHALL NOT depend on the live donor checkout. Materialization, replay, compiled lineage and scoped proof-use observation SHALL retain distinct evidence authority and unresolved frontiers.

#### Scenario: Capsule still imports the donor

- **WHEN** a replay requires an absolute path, symlink or environment entry into the donor checkout
- **THEN** local portability remains unqualified and the challenge cannot be registered as reproducible from its retained local inputs

#### Scenario: Only lexical dependencies are available

- **WHEN** a local capsule has lexical import or name-dependency records but no required native semantic evidence
- **THEN** the report preserves that limitation and does not label those records compiled proof lineage or actual scoped premise use

### Requirement: Independent evidence dimensions

An opt-in audit SHALL report assumption feasibility, premise origin, operation obligations, formal support, interpretation fidelity, method correspondence and coverage independently. Unrun checks SHALL remain not-run, and historical evidence SHALL NOT acquire fresh checking authority.

#### Scenario: Vacuous implication

- **WHEN** a correspondence implication is checked under an inconsistent context
- **THEN** the report preserves conditional support and separately reports the checked inconsistency without asserting that the conditional theorem is false

### Requirement: Immutable source expectations

Each diagnostic SHALL bind the original source span and attributed interpretation, exact selected formal subject, environment, checker identity and bounds. A repair or alternate reading SHALL be a distinct subject.

#### Scenario: Repair adds an assumption

- **WHEN** an agent adds a nonemptiness hypothesis after the original existence check fails
- **THEN** the new result is a proposed revision and cannot close the original obligation

#### Scenario: Initial interpretation is wrong

- **WHEN** a frozen interpretation silently narrows the original prose
- **THEN** successful checks leave source fidelity attributed or reviewed separately rather than certifying the translation

### Requirement: Existing consumer integration

Audits SHALL expose the child diagnostics through the existing opt-in investigation workflow, readable reports and stored inspection, retaining unknown providers and unexamined source spans. Ordinary theorem checking SHALL NOT require pitfall auditing.

#### Scenario: Old receipt inspected

- **WHEN** a pre-extension receipt lacks feasibility observations
- **THEN** inspection remains compatible and shows feasibility not-run rather than inferring that its premises are feasible

### Requirement: Bounded execution and replay

All audit stages SHALL share an absolute deadline and enforce process-tree memory, output and traversal limits. The default memory cap SHALL remain 12 GiB. Exhaustion SHALL preserve partial results and the existing stop-and-report instruction without automatic escalation.

#### Scenario: Provider expansion exhausts its budget

- **WHEN** a selected provider exceeds traversal or memory bounds
- **THEN** the report retains its unexpanded frontier, resource stop and unresolved judgment instead of declaring no hidden premise

### Requirement: Measured qualification

The umbrella SHALL require the baseline child’s accepted family baseline before each corresponding child’s semantic runtime edits, and SHALL retain the same preserved pre-change runtime and frozen common policy for every baseline batch. It SHALL require the full 24-case baseline, validated scorer, child acceptance evidence, independent integrated review and matched per-family metrics before final acceptance. Implementation completion SHALL remain separate from detection improvement and unfamiliar-paper discovery.

#### Scenario: One child is ready before the rest

- **WHEN** the feasibility family baseline and shared evidence contract are accepted while other families remain unmeasured
- **THEN** feasibility implementation may proceed, other child unlocks remain pending, and the umbrella cannot claim full baseline or final acceptance

#### Scenario: New checks do not improve detection

- **WHEN** all engineering gates pass but the matched development gate fails
- **THEN** the umbrella records implementation completion and unestablished improvement without scheduling a broader paper trial

