## ADDED Requirements

### Requirement: Common-Layer and Facade Quality

Ladon SHALL report common-layer candidates and facade subtype quality using
generic graph and source-shape evidence.

#### Scenario: common dependency is ranked

- **WHEN** modules from multiple selected groups import one target
- **THEN** Ladon SHALL report source groups, importer count, samples,
  dependency scope, confidence, and confidence reason.

#### Scenario: facade subtype is classified

- **WHEN** a module is a pure barrel, generated aggregation, public root facade,
  or mixed barrel/theorem module
- **THEN** Ladon SHALL expose the subtype in module metadata and summaries.

#### Scenario: implementation fan-out excludes facades

- **WHEN** implementation fan-out tables are computed
- **THEN** facade-like modules SHALL be separated from implementation rows.
