## ADDED Requirements

### Requirement: Clean-core report bridge adaptation
The ProofIR bridge SHALL consume the current clean-core declaration graph when
an explicit declaration table is absent without inventing unavailable source
hashes or ranges.

#### Scenario: Explicit declaration table is present
- **WHEN** a Ladon report includes explicit declaration rows
- **THEN** the bridge prefers those rows over derived clean-core inventory

#### Scenario: Clean-core declaration table is absent
- **WHEN** a Ladon report exposes declarations only through graph edges, chosen roots, and fan rows
- **THEN** the bridge derives bounded declaration/module rows and permits medium-confidence exact module/declaration joins

#### Scenario: Derived row lacks source evidence
- **WHEN** clean-core fields do not supply source ranges or hashes
- **THEN** the bridge does not invent them or claim a high-confidence source-hash join

### Requirement: Real-report CLI smoke
The installed bridge CLI SHALL accept a clean-core-shaped Ladon report and a
compact ProofIR bridge index and SHALL emit a structured bridge report.

#### Scenario: Quux-shaped clean-core fixture
- **WHEN** the CLI receives the tracked Quux-shaped clean-core report and compact bridge index fixtures
- **THEN** it exits successfully and emits the expected derived declaration and joined-surface counts
