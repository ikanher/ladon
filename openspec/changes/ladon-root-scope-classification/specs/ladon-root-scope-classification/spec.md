## ADDED Requirements

### Requirement: Root-Scope Finding Classification

Ladon SHALL classify root-scope pressure findings by likely review context.

#### Scenario: public root is intentionally narrow

- GIVEN a one-segment root with a broad repository inventory and high
  unreachable count
- WHEN root-scope pressure is emitted
- THEN the finding SHALL include `public_root_narrow_inventory`.

#### Scenario: theorem owner imports broad stack

- GIVEN a deep owner root with a broad direct import closure
- WHEN root-scope pressure is emitted
- THEN the finding SHALL include `narrow_owner_broad_import`.

#### Scenario: component signals preserved

- GIVEN root-scope classification is attached
- WHEN the finding is emitted
- THEN existing component signals SHALL still be present.
