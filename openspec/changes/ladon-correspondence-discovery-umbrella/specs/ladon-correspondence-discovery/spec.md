# Spec Delta

## Purpose

Help auditors discover and substantiate discrepancies between mathematical exposition and existing formal proofs, while exposing source coverage, interpretation uncertainty and the exact scope of checking.

## ADDED Requirements

### Requirement: Preserve the original audit question

Each audit SHALL bind the selected exposition, proposed formal source and original local assertions to identifiable revisions. Interpretations, reconstructions, proposed repairs and post-reveal judgments SHALL remain distinct from those sources and from earlier audit results.

#### Scenario: Answer revealed after a blind attempt
- **WHEN** a user supplies a critique after an audit missed a discrepancy
- **THEN** the original findings and source identities remain available unchanged, and subsequent detections are labeled as informed by the reveal

### Requirement: Source coverage precedes mapping coverage

An audit SHALL report its selected source range, inventory method and attribution, discovered claims and reasoning steps, exclusions, unexamined passages and unresolved extraction. Mapping coverage SHALL use only its named population and SHALL NOT imply complete source coverage.

#### Scenario: All selected endpoints are mapped
- **WHEN** two endpoints are mapped but intermediate estimates in the selected passage were not inventoried
- **THEN** the audit exposes that coverage gap even if every declared component is mapped and every endpoint checks

#### Scenario: Mathematical notation is ambiguous after extraction
- **WHEN** text extraction loses a distinction between two operators
- **THEN** the audit retains the ambiguity and checks the source rendering before attributing a mismatch to the mathematics

### Requirement: Compare local mathematical contracts

Each reviewed correspondence SHALL identify the prose assertion and formal statement, variable correspondence, hypotheses, domains, quantifier order, conclusion and applicable quantitative dependencies. Unresolved interpretations SHALL remain explicit. Syntactic differences alone SHALL NOT establish semantic mismatch or equivalence.

#### Scenario: An inverse estimate loses an additional derivative
- **WHEN** the prose requests an order-m output bound from order-(m+4) input norms and the cited formal estimate requires order-(m+5) input norms
- **THEN** the audit reports the changed quantitative guarantee, checks derivative variables and uniform constant dependence, and leaves a strengthening bridge unresolved unless independently supplied

#### Scenario: Equivalent notation changes
- **WHEN** renamed bound variables or a justified normalization change leave the mathematical contract equivalent
- **THEN** the audit records the correspondence justification without reporting an error merely from the textual difference

### Requirement: Require the implication needed by the consumer

For a proposed formal substitute, the audit SHALL examine whether the prose context supplies its premises and whether its conclusion establishes the needed local claim. Added premises, weaker guarantees and missing implication steps SHALL be reported separately from formal checking and from falsity.

#### Scenario: A pressure bound introduces a gradient norm
- **WHEN** the prose bound uses B alone, its formal substitute also uses A, and the available comparison bounds B above by a function of A
- **THEN** the audit does not use that comparison backwards to eliminate A; it records the exact missing implication or an independently justified replacement argument

#### Scenario: The goal was repaired during checking
- **WHEN** a candidate checks only after adding a premise or weakening the original goal
- **THEN** checking applies to the revised proposition, while the original local correspondence stays unresolved or receives a separate supported finding

### Requirement: Distinguish statement support from method support

Audit findings SHALL separately assess the local statement and the argument claimed in the exposition. Proof-method findings SHALL cite actual proof steps and relevant premise producers or consumers. A final theorem, an axiom inventory or a lexical dependency edge SHALL NOT establish that a stated intermediate argument was followed.

#### Scenario: Two valid proofs have different methods
- **WHEN** a direct calculation and a spectral argument establish the same conclusion
- **THEN** the audit can report statement agreement and method difference without labeling either proof false

### Requirement: Evidence-directed triage retains omissions

The workflow SHALL prioritize concrete unresolved obligations and load-bearing uses, retain bounded candidate searches and the reasons for follow-up, and record resource-limited or unsupported work as unexamined or unresolved. Completed checks SHALL NOT discharge unrelated obligations.

#### Scenario: The work budget ends after a narrow proof slice
- **WHEN** the auditor exhausts its declared budget while other selected passages remain unexamined
- **THEN** the report names those passages and the next mathematical questions without announcing a clean bill of health for the selected document

### Requirement: Keep mechanical and attributed judgments distinct

Coverage checks, source associations, Lean checks and attributed correspondence reviews SHALL remain independently reported. A workflow completion check SHALL establish only its declared bookkeeping predicates; disputed or incomplete mathematical judgments SHALL NOT become aligned through artifact validation or review currency.

#### Scenario: A fully bound review is mistaken
- **WHEN** an attributed aligned review has valid revision bindings but a later audit identifies a changed hypothesis
- **THEN** the original review remains historical evidence, the new finding is separately attributed, and no integrity result is presented as having certified the original judgment

### Requirement: Evaluate discovery without revealing the answer

Detection evaluation SHALL freeze inputs, access boundaries, rubric, budgets and case labels before scored runs. It SHALL separate disclosed development cases from withheld cases, retain failures and interventions, and score localization, classification, omissions, false alarms and cost. Uncertain reference judgments SHALL remain unscored or separately adjudicated.

#### Scenario: A published diagnosis is already known
- **WHEN** the evaluator has been given the Navier–Stokes derivative or pressure diagnosis
- **THEN** reproduction of that diagnosis counts as a development result and not as withheld detection success

#### Scenario: Answer files remain accessible
- **WHEN** a purported withheld run can read the reference diagnosis or prior solution artifacts
- **THEN** the run is labeled contaminated and excluded from claims of withheld detection

### Requirement: Attribute Ladon benefit through a fair comparison

A comparative benefit claim SHALL use equivalent source access, model configuration, task framing and budgets for competent ordinary tooling and Ladon-assisted runs. The report SHALL distinguish workflow improvements from software contributions and preserve negative results, abstentions and sample limitations.

#### Scenario: Both workflows find the same discrepancy
- **WHEN** ordinary Lean tools and Ladon-assisted auditing both identify the same local mismatch
- **THEN** the result does not credit discovery uniquely to Ladon and compares only observed differences in evidence quality, omissions and cost

### Requirement: Keep development fixtures portable

Ladon's production behavior and portable tests SHALL operate without Quux or a large external research checkout. External mathematical sources SHALL retain provenance and preparation instructions; live formal checks SHALL identify their actual environment and scope.

#### Scenario: The research checkout is unavailable
- **WHEN** portable regressions run without the Navier–Stokes repository
- **THEN** small attributed fixtures exercise the workflow boundaries, while unavailable research replays remain explicitly separate
