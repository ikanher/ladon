# Proposal

Review feedback repeatedly called out near-duplicate proof skeletons, especially
families such as first-lag finite-sum lower bounds. Ladon currently reports
individual declaration fan-in/fan-out, but not families of similarly named
declarations.

Add a small declaration-name family heuristic based on theorem-name suffixes.

# Scope

- Group declarations by basename suffix after the first underscore.
- Emit groups with at least two declarations.
- Render a compact `Declaration Name Families` section.
- Promote large groups to findings.

# Non-Goals

- No proof-term comparison.
- No semantic theorem similarity.
- No domain-specific BIFR token rules.
