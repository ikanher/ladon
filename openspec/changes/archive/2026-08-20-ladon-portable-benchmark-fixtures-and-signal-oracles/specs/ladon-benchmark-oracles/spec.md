## ADDED Requirements

### Requirement: Portable benchmark fixtures cover promoted signals

The benchmark corpus SHALL include portable source fixtures for promoted Ladon
signals, including module import pressure, root-scope classification,
declaration reference resolution, unresolved-reference classification,
proof-family similarity, and packet-evidence profiles.

#### Scenario: CI runs without sibling repositories

- **WHEN** the maintained test suite runs in a clean Ladon checkout without
  Quux, matrix-factorization, or mathlib
- **THEN** benchmark fixture tests can run or skip Lean-only cases without
  requiring sibling repositories

### Requirement: Signal oracles check focused outcomes

The oracle evaluator SHALL check focused expected outcomes instead of comparing
entire report JSON payloads.

#### Scenario: Oracle checks a declaration signal

- **WHEN** an oracle expects a candidate to be classified as parser noise,
  local or field noise, known inventory, external, or actionable unknown
- **THEN** the evaluator reports pass or fail with the fixture name, signal
  name, expected value, and observed value

### Requirement: Negative cases are first-class

The benchmark corpus SHALL include adversarial negative examples for ambiguous
basenames, intentional root narrowness, local binder noise, field-like
references, and evidence packets that are partial by design.

#### Scenario: Negative case prevents overpromotion

- **WHEN** a fixture contains an ambiguous basename reference
- **THEN** the oracle expects no high-confidence resolved declaration edge

### Requirement: New promoted findings require oracle coverage

Any future packet that adds a promoted finding kind SHALL add a benchmark oracle
or explicitly document why the finding remains experimental and unpromoted.

#### Scenario: New finding is proposed

- **WHEN** a change adds a new finding kind to `summarize_findings`
- **THEN** the change includes oracle coverage for at least one positive and
  one negative case, or marks the finding as experimental in the proposal
