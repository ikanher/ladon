## ADDED Requirements

### Requirement: Atlas Export Packet Sequence

Ladon SHALL keep atlas work tied to explicit child packets with validation
gates.

#### Scenario: first atlas child exports reports

- GIVEN the atlas export suite is applied
- WHEN child `ladon-report-atlas-export` is complete
- THEN Ladon SHALL provide a deterministic report-atlas JSON and Markdown
  exporter.
