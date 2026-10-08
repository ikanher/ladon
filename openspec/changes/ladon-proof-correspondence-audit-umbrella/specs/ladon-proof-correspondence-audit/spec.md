# Spec Delta

## Purpose

Help authors and readers examine whether a particular proof passage is supported by its proposed formal counterpart, preserving exact subjects, local obligations, attributed interpretations and correction scope.

## ADDED Requirements

### Requirement: Audits preserve the original question and source versions
An audit SHALL identify the selected passage, proposed formal counterpart and disputed statement, definition or inference. It SHALL retain source versions, locators, available content identities and relevant mathematical context. Original material SHALL remain distinct from reconstructions, repaired variants and proposed replacements.

#### Scenario: A published example is reconstructed locally
- **WHEN** executable code is recreated from a paper or screenshot
- **THEN** the audit identifies that code as a reconstruction, retains the published source and records any changes needed for the selected environment
- **AND** a successful reconstruction is not reported as replay of the original model session

### Requirement: Findings expose their basis and limits
Each finding SHALL give reachable source references, the disputed proposition or presupposition, relevant assumptions and quantifiers, evidence obtained, the consequence for the prose and remaining uncertainty. Source interpretation and proof-method correspondence SHALL remain attributed judgments distinct from formal checking results.

#### Scenario: An auditor formalizes a sentence
- **WHEN** a local obligation checks in Lean
- **THEN** the report states the exact proposition and context checked and attributes the interpretation connecting them to the sentence
- **AND** Lean acceptance does not certify that interpretation

### Requirement: Final theorem acceptance cannot close a disputed intermediate step
A successful proof of the final theorem SHALL NOT close an audit of an unsupported intermediate step. A repair or alternative derivation SHALL be identified separately from support for the original argument.

#### Scenario: Incorrect factorization is silently repaired
- **WHEN** the final polynomial inequality checks using a corrected factorization
- **THEN** the original asserted factorization remains a separate audit obligation and a demonstrated failure is reported with its own evidence
- **AND** the report distinguishes the true conclusion from the invalid supplied argument

### Requirement: Definition presuppositions remain explicit obligations
An audit SHALL distinguish a formal definition's total behavior from the existence, uniqueness or domain conditions presupposed by the prose. Default values SHALL NOT discharge those conditions. An unresolved condition SHALL remain explicit rather than being silently added as a premise or treated as false.

#### Scenario: Least-element construction uses an empty-set default
- **WHEN** the prose presupposes a least natural number but the formal construction supplies a value for an empty set
- **THEN** the audit separately examines nonemptiness and reports the definition's behavior
- **AND** an algebraic identity using that value does not establish the presupposed existence

#### Scenario: Existence is explicitly assumed in a repaired statement
- **WHEN** a proposed repair adds a nonemptiness hypothesis
- **THEN** its checked conditional result is labelled as such and does not establish the original unconditional existence assertion

### Requirement: Statement differences preserve mathematical direction
Audits SHALL identify material differences in assumptions, domain, quantifiers, conclusions, constant dependence and defined objects. Syntactic differences SHALL NOT establish semantic inequivalence. Stronger hypotheses, weaker conclusions and incomparable statements SHALL be distinguished only to the extent justified by the retained evidence.

#### Scenario: A published estimate and a formal estimate use different derivative orders
- **WHEN** selected source versions appear to require m+4 and m+5 input derivatives respectively
- **THEN** the audit compares the norms, derivative variables, assumptions and constant dependence before stating the relation
- **AND** the report does not infer that the paper's stronger estimate or final theorem is false merely because the selected formal estimate does not establish it

### Requirement: Alternative valid arguments are not false-proof findings
An audit SHALL distinguish validity of the supplied argument, validity of an alternative formal derivation and fidelity between their methods. Method differences SHALL NOT alone imply that either proof is incorrect. Dependency names or an automatically generated back-translation SHALL NOT alone establish method fidelity.

#### Scenario: Diagonalization is replaced by a direct sum of squares
- **WHEN** the written matrix proof and formal proof establish the same statement by those different routes
- **THEN** the report preserves their separate validity evidence and describes the method difference without calling the written proof false

#### Scenario: A correctly repaired passage is supplied
- **WHEN** the passage faithfully states the supported local argument and its conditions
- **THEN** the audit retains it without inventing an omitted premise or treating conventional exposition as a defect solely because it lacks a formal binding

### Requirement: Failed checks retain the scope of their failure
Reports SHALL distinguish an unsuccessful application, an unresolved obligation, a demonstrated counterexample and unavailable execution. Failure to establish an implication SHALL NOT be reported as proof of its negation. Resource or environment failures SHALL retain their operational status.

#### Scenario: An attempted bridge leaves a residual
- **WHEN** checking a proposed local implication leaves a premise unresolved
- **THEN** the report gives the residual in its actual context and does not declare the original claim impossible

### Requirement: Checking evidence is reproducible and source scoped
Fresh checking claims SHALL retain exact checked source, selected goal/context where applicable, environment identity, commands, outputs, dependency-policy results and available timing/resource observations. Stored receipts SHALL remain historical. Ordinary compiler exit status alone SHALL NOT establish placeholder-free proof acceptance under a declared trust policy.

#### Scenario: A historical receipt is supplied without its runnable imports
- **WHEN** an auditor can inspect the receipt but cannot reproduce the environment
- **THEN** the report identifies historical support and the missing replay prerequisites without claiming a fresh check

### Requirement: Corrections and reviews retain separate revisions
The audit SHALL preserve original and proposed passages, describe substantive changes and distinguish proposed, adopted and unresolved outcomes. Adding a hypothesis SHALL be identified as narrowing the statement. Prior assessments SHALL retain their original revision bindings; new hashes alone SHALL NOT renew their judgments.

#### Scenario: A paragraph changes after review
- **WHEN** a correction is proposed or adopted
- **THEN** the original review remains bound to its original passage and any new correspondence judgment names the revised subject and its evidence

### Requirement: Audit consumption supports ordinary accessible tools
Essential explanations, findings and supporting source references SHALL be readable through ordinary files without access to the generating model. The documented checking route SHALL state its real environment prerequisites. Use of a Ladon command SHALL NOT be required to count a mathematical audit outcome as useful.

#### Scenario: An auditor uses files and ordinary Lean only
- **WHEN** that route substantiates a discrepancy and correction
- **THEN** the result is retained as mathematical progress without being promoted into evidence of Ladon interface superiority

### Requirement: Development cases and bounded outcomes are honestly characterized
The workflow SHALL label published examples and authored controls as development material, retain failed attempts and interventions, and separate mathematical findings from software contribution. A bounded unresolved outcome SHALL identify the exact open obligation or missing evidence; it SHALL NOT be described as completed mathematical verification.

#### Scenario: The published-passage audit reaches its declared budget
- **WHEN** an implication remains unresolved at the stopping point
- **THEN** the handoff records the attempted relation, retained evidence and unresolved scope rather than extending the task into a full-paper verification campaign

#### Scenario: Existing tools suffice throughout the selected audits
- **WHEN** no concrete missing software operation is observed
- **THEN** the workflow closes with its findings and ordinary-tool recipe and does not infer a need for interface expansion or claim measured general reader benefit
