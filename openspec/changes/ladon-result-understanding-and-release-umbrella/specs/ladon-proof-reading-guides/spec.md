## ADDED Requirements

### Requirement: Reading guides link exposition to exact subjects
Following [Responsible Release of AI-Generated Mathematics](https://agmai.org/general-sep29/) (2026-09-29), §2.B Step I.1(a–b) and Step II, the system SHALL expose ordered reading steps linking a claim to definitions, supporting lemmas, source locations, and supplied explanations. Every annotation SHALL identify its author kind, exact subject revisions, purpose, and separate review records. Interpretation and limits SHALL be traceable through `../../sources.md`.

#### Scenario: An LLM explanation has not received human review
- **WHEN** a model-generated explanation is attached to a checked declaration
- **THEN** the guide displays the explanation's model authorship and absent human review independently of the declaration's checker evidence

### Requirement: Structural navigation is not an explanatory proof
Reading paths SHALL reuse existing lineage and derivation queries with their coverage, edge kinds, limits, and authority. Authored reading order and claims that a lemma explains a proof step SHALL remain separate annotations. The system SHALL NOT turn lexical references or dependency paths into a mathematical argument.

#### Scenario: Only declaration dependencies are available
- **WHEN** lineage identifies dependencies but no elaborated proof-step structure or reviewed explanation exists
- **THEN** the guide offers structural navigation and reports the missing explanatory evidence rather than generating an authoritative proof narrative

#### Scenario: A conditional theorem coexists with a counterexample and different release scopes
- **WHEN** an authored guide explains the fixed-epoch baseline or an analogous result
- **THEN** its reading steps identify the sufficient condition, the counterexample's role, and differences such as transcript versus average-only release before presenting supporting dependency navigation
- **AND** those explanation choices retain author/review attribution rather than becoming checker findings

### Requirement: Citation relationships remain attributable assertions
Citation records SHALL retain bibliographic identity, URL or persistent identifier where supplied, passage/result locator, relationship kind, submitter, and review status. Supported relationships SHALL include background, uses-result, related-method, and attribution-claim. Suggested citations SHALL remain unreviewed until an explicit review is recorded; priority, novelty, and attribution correctness SHALL NOT be inferred from citation presence or retrieval similarity.

#### Scenario: Two sources are proposed as the origin of an idea
- **WHEN** incompatible attribution claims are attached to a proof explanation
- **THEN** both assertions and their supporting locators remain visible as disputed or unreviewed and no earliest-origin verdict is manufactured

### Requirement: Review scope and revision changes remain visible
Reviews SHALL distinguish mathematical explanation, correspondence, and attribution scope, retain reviewer identity/kind and rationale, and bind the exact explanation and target revisions. Editing an explanation, cited passage, or target SHALL NOT carry forward an approval silently. A human review SHALL be an attributed attestation, not a machine guarantee of understanding.

#### Scenario: Exposition is edited after review
- **WHEN** the explanation changes while the formal theorem remains identical
- **THEN** the old exposition review remains historical and the edited explanation appears unreviewed without altering theorem checker evidence

### Requirement: Guides support bounded reuse-oriented inspection
`ladon result guide` SHALL support exact claim and declaration selection, bounded reading steps, and references for further inspection under the dossier limits. It SHALL expose available lemma statements and hypotheses with source links, while applicability to a new goal SHALL require the existing explicit Lean-check workflow. No model call or citation download SHALL occur implicitly.

#### Scenario: A reader selects a supporting lemma for another proof
- **WHEN** a guide surfaces a lemma and its explanation as a reuse candidate
- **THEN** its statement, assumptions, and exact identity are available and the guide does not claim it applies to the reader's new goal without a separate check

### Requirement: Focused exposition review preserves application boundaries
Paragraph review SHALL identify its exact prose revision, selected component,
formal statements, relevant premises and checking references. Explicit proof-step
checks SHALL retain their formal goal/context and result. A checked translation
or alternative derivation SHALL NOT establish prose fidelity or the supplied
proof's strategy; those judgments SHALL remain attributed and separately scoped.

#### Scenario: A paragraph omits an application prerequisite
- **WHEN** a cited lemma's explicit application leaves that prerequisite unresolved
- **THEN** the review identifies the unsupported application and proposes a revision preserving the premise
- **AND** it does not declare the prose conclusion false solely because that application is incomplete

#### Scenario: An alternative formal derivation succeeds
- **WHEN** the claimed inference is established by a derivation different from the supplied proof
- **THEN** its formal checking result remains separate from a judgment about whether the exposition describes the supplied proof's method

### Requirement: Exposition change notices request scoped reassessment
Changes to paragraph, statement or application bindings SHALL identify the
affected explanation and historical review scope through existing revision
mechanisms. They SHALL request reassessment without automatically asserting
mathematical falsehood. Conventional argument, unchecked translation, unresolved
correspondence and demonstrated mismatch SHALL remain distinct.

#### Scenario: A bound theorem changes its assumptions
- **WHEN** an explanation relies on the preceding statement revision
- **THEN** the view identifies that paragraph as needing recheck and preserves the historical judgment
- **AND** changed content identity alone does not become a mismatch or falsehood verdict
