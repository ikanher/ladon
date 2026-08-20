## ADDED Requirements

### Requirement: Literature-Grounded Quality Signal Roadmap

Ladon SHALL track its next quality-signal work as a literature-grounded
umbrella roadmap.

#### Scenario: each quality signal has a literature basis

- GIVEN a new quality signal is proposed under this umbrella
- WHEN its child packet is opened
- THEN it SHALL cite at least one entry from `paper/ladon-code-quality/manifest.json`.

#### Scenario: findings distinguish signal from defect

- GIVEN a child packet emits new findings
- WHEN the text report renders them
- THEN the finding wording SHALL describe review triage or evidence pressure,
  not claim a defect by itself.

#### Scenario: calibration precedes stronger smell claims

- GIVEN a child packet introduces thresholded quality findings
- WHEN the packet is implemented
- THEN it SHALL either use an empirical baseline or explicitly document why a
  fixed threshold is provisional.

#### Scenario: proof-code similarity remains deterministic first

- GIVEN repeated proof-shape analysis is extended
- WHEN implementation begins
- THEN the first version SHALL use deterministic features before any LLM-assisted
  explanation.
