# Design

The classifier stays string-based and conservative:

- single-character uppercase identifiers are likely local variables in theorem
  statements, not missing theorem owners;
- dotted roots such as `ENNReal` and `ProbabilityTheory` are external mathlib
  namespaces;
- multi-character uppercase/camel theorem-like names remain actionable unless
  already known through inventory or external roots.
