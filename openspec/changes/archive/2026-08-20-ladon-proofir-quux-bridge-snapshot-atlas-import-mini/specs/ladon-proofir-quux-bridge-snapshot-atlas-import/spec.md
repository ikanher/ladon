## ADDED Requirements

### Requirement: Atlas workflow accepts bridge snapshots as optional summaries

Atlas workflow SHALL normalize `ladon_proofir_bridge_snapshot` inputs into the
existing optional bridge-report summary shape before scoring or rendering.

#### Scenario: Snapshot contributes bridge pressure

- **WHEN** a snapshot contains bridge diagnostics and source Ladon report root
  identity
- **THEN** atlas workflow includes those diagnostics in bridge pressure for that
  root

### Requirement: Snapshot diagnostics keep ProofIR namespace

Snapshot diagnostics SHALL be mapped to workflow diagnostics without stripping
their `proofir.*` or bridge trust-boundary identity.

#### Scenario: Snapshot diagnostic is rendered

- **WHEN** a snapshot diagnostic has `diagnosticId` and `severity`
- **THEN** workflow rows expose equivalent `ruleId` and `level` fields

### Requirement: Snapshot statuses are quoted only

Atlas workflow SHALL NOT treat statuses inside a bridge snapshot as
Ladon-validated theorem truth.

#### Scenario: Snapshot has established external Lean status

- **WHEN** a snapshot surface has an external status
- **THEN** workflow output may summarize the join but does not emit any
  Ladon-established proof status
