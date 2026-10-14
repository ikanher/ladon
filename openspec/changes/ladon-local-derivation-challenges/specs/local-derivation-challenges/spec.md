# Spec Delta

## Purpose

Turn disputed local mathematical derivations into explicit, challengeable obligations and check concrete rational counterexamples without overstating their authority.

## ADDED Requirements

### Requirement: Preserve version-one consumers
Version-two derivation review SHALL be explicit opt-in. Version-one plans and existing finalization behavior SHALL remain supported without modifying historical records.

#### Scenario: Existing audit is inspected
- **WHEN** a version-one plan is supplied
- **THEN** its validation and scheduling remain compatible with the previous controller

### Requirement: Prioritize suspicious local obligations
For version-two plans, explicit concerns and unresolved or differing correspondence judgments SHALL require derivation review ahead of unrelated inventory. Missing contracts, missing steps, unresolved assessments and challenger disagreements SHALL remain actionable.

#### Scenario: A discrepancy is buried behind captures
- **WHEN** a reviewed discrepancy and hundreds of unexamined captures coexist
- **THEN** the next batch starts with the discrepancy's missing concrete work

### Requirement: Bind steps and independent challenge context
Each derivation step SHALL bind an exact source subspan, local contract, rule, substitution and valid earlier-step dependencies. Challenges SHALL identify a different reviewer and bind the current complete local context. Exported challenge inputs SHALL omit earlier assessment outcomes and proposed repairs.

#### Scenario: An earlier premise changes after review
- **WHEN** an existing challenge digest no longer matches its claim or predecessor context
- **THEN** the controller rejects the stale challenge rather than accepting its conclusion

#### Scenario: A reviewer gives only an unresolved challenge
- **WHEN** the challenge is absent, unresolved or disagrees with the author
- **THEN** the corresponding step remains queued and does not become completed through endpoint success

### Requirement: Check exact rational witnesses
The witness operation SHALL evaluate a bounded authored rational implication at an explicit assignment. It SHALL report a counterexample only when every premise holds and the conclusion fails. It SHALL expose exact evaluated values and distinguish failed assumptions from a non-refuting sample.

#### Scenario: A plausible witness violates a premise
- **WHEN** the conclusion is false but a premise also fails
- **THEN** the result is outside-assumptions rather than a counterexample

#### Scenario: A faithful control survives a sample
- **WHEN** premises and conclusion all hold
- **THEN** the result is not-counterexample and makes no universal-validity claim

### Requirement: Reject malformed or excessive arithmetic
Witness inputs SHALL reject unknown variables/operators, ambiguous fields, booleans/floats as rationals, zero denominators, excessive depth/count/size, and undefined arithmetic. Commands SHALL perform no arbitrary code execution or automatic tool/model invocation.

#### Scenario: Unsupported expression hides behind a false premise
- **WHEN** any expression is malformed even though another premise is false
- **THEN** validation rejects the entire input

### Requirement: Preserve authority and evaluation provenance
Step assessments, reviewer identity and prose-to-arithmetic interpretation SHALL remain explicitly attributed. Exact arithmetic SHALL not certify the original exposition. The consuming exercise SHALL preserve fresh first responses, controls, unsuccessful attempts and independently replayed evidence without changing past research-paper reports.

#### Scenario: An arithmetic witness is accepted
- **WHEN** a supplied assignment refutes the stored scalar implication
- **THEN** the report scopes the result to that interpretation and preserves its original source context
