## ADDED Requirements

### Requirement: Witness Packet Evidence Summary

Ladon SHALL summarize generic evidence completeness for packet directories.

#### Scenario: complete packet evidence

- GIVEN a packet directory with metadata, witness JSON, checker scripts, tests,
  verification commands, and owner references
- WHEN packet evidence is summarized
- THEN Ladon SHALL report passed checks and a complete status.

#### Scenario: partial packet evidence

- GIVEN a packet directory missing one or more evidence classes
- WHEN packet evidence is summarized
- THEN Ladon SHALL report failed checks without claiming witness correctness.

#### Scenario: CLI packet-dir integration

- GIVEN `--packet-dir` is provided
- WHEN the CLI writes a report
- THEN the JSON and text report SHALL include packet evidence.
