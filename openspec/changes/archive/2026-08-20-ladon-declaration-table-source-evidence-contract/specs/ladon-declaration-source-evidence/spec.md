## ADDED Requirements

### Requirement: Reports include declaration source evidence rows

When declaration IR is available, Ladon reports SHALL include a
`declaration_graph.declarations` list with rows containing declaration, module,
kind, source path, source range, selection range, content hash, extraction
backend, extractor version, name-resolution method, and confidence where those
fields are known.

#### Scenario: Lean backend emits declaration rows

- **WHEN** Ladon runs with the Lean extraction backend and declaration commands
  are extracted
- **THEN** the JSON report includes declaration rows with declaration identity,
  module, backend, method, confidence, and available source evidence

### Requirement: Missing source evidence is explicit

Ladon SHALL omit unknown optional source fields or mark the confidence/method so
that consumers can distinguish source-backed rows from derived rows.

#### Scenario: Bridge falls back to derived declaration rows

- **WHEN** a Ladon report lacks explicit declaration source evidence rows
- **THEN** the ProofIR bridge uses derived rows only for medium or low
  confidence joins and does not invent source ranges or hashes

### Requirement: ProofIR joins prefer stronger source evidence

The ProofIR bridge SHALL prefer exact source hash declaration joins, then exact
source range declaration joins, then exact module/declaration joins, then
basename-only joins, and SHALL mark basename-only joins as warning-only.

#### Scenario: Surface hash matches declaration hash

- **WHEN** a ProofIR surface and Ladon declaration row have matching declaration
  name, source path, and content hash
- **THEN** the bridge emits an `exact_source_hash_decl` join with high
  attachment confidence

### Requirement: Source attachment confidence is not proof truth

Reports and bridge diagnostics SHALL state that source-range or source-hash
joins establish attachment confidence only, not theorem truth, witness
adequacy, or proof correctness.

#### Scenario: Reviewer reads bridge report

- **WHEN** a bridge report contains high-confidence source attachment joins
- **THEN** the report also includes trust rules stating that Ladon does not
  validate mathematical truth or promote ProofIR statuses
