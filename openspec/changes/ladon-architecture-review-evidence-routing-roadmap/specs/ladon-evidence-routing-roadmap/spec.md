## ADDED Requirements

### Requirement: Roadmap states Ladon's review-routing posture

The roadmap SHALL state that Ladon is a host-side Lean architecture review and
evidence-routing assistant, and SHALL state that Ladon does not validate theorem
truth, witness adequacy, or proof correctness.

#### Scenario: Reviewer reads roadmap posture

- **WHEN** a maintainer opens the roadmap proposal or design
- **THEN** the maintainer can identify Ladon's intended product posture and
  non-claims without reading implementation code

### Requirement: Roadmap orders child packets by evidence leverage

The roadmap SHALL list child packets in an explicit order that prioritizes
portable benchmark oracles, then declaration source evidence, then atlas review
workflow.

#### Scenario: Apply order is needed

- **WHEN** a maintainer asks which future-direction packet to apply first
- **THEN** the roadmap identifies `ladon-portable-benchmark-fixtures-and-signal-oracles`
  as the first child and explains why it gates later findings

### Requirement: Roadmap records deferred directions

The roadmap SHALL identify deferred or avoided directions, including full
proof-correctness gates inside Ladon, Rust rewrites without workload evidence,
and UI or graph-database work before report contracts stabilize.

#### Scenario: New broad feature is proposed

- **WHEN** a future proposal suggests proof correctness, Rust, UI, graph
  clustering, or LLM explanation work
- **THEN** the roadmap gives maintainers a documented gate for whether that work
  is premature
