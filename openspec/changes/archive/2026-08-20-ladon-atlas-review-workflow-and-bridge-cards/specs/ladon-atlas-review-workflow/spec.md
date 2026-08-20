## ADDED Requirements

### Requirement: Atlas workflow answers reviewer routing questions

The atlas workflow SHALL provide outputs that answer what changed since the last
run, which subjects recur across reports, which roots need review first, which
joins are low-confidence, and which packet or bridge evidence is incomplete or
stale.

#### Scenario: Reviewer opens workflow output

- **WHEN** a reviewer opens the atlas workflow Markdown or card output
- **THEN** the reviewer can identify the top review routes without opening raw
  per-root JSON first

### Requirement: Reviewer cards include evidence and non-claims

Reviewer cards SHALL include root identity, extraction backend, source report
links, top findings, review regions, strongest evidence, known non-claims, and
optional ProofIR diagnostics when supplied.

#### Scenario: Bridge diagnostics are present

- **WHEN** a report set is accompanied by ProofIR bridge diagnostics
- **THEN** reviewer cards include bridge diagnostic summaries and trust notes
  without treating ProofIR statuses as Ladon-validated truth

### Requirement: Machine-readable atlas remains canonical

The workflow SHALL keep atlas JSON as the canonical interchange output, with
Markdown, SQLite, diff, and cards derived from it or from explicitly supplied
bridge reports.

#### Scenario: Derived artifact is regenerated

- **WHEN** a reviewer regenerates SQLite or Markdown cards from the same atlas
  JSON and bridge inputs
- **THEN** the derived artifacts preserve the same report identities, findings,
  review regions, and diagnostic counts

### Requirement: ProofIR diagnostics remain optional and namespaced

ProofIR bridge diagnostics SHALL remain optional, SHALL be namespaced as
`proofir.*`, and SHALL not be required for normal atlas generation.

#### Scenario: No bridge report is supplied

- **WHEN** the atlas workflow runs on Ladon reports without ProofIR bridge data
- **THEN** the atlas workflow still produces reviewer cards and does not emit
  missing-bridge failures
