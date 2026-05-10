# Proposal

Unresolved reference classification now separates raw parser candidates from
actionable unresolved candidates, but text reports only show the top raw rows.
When no actionable rows remain, reviewers should be able to see why.

Add per-class unresolved reference counts to the JSON summary and text report.

# Scope

- Count unresolved references by classification.
- Render an `Unresolved Reference Classes` section.
- Keep raw rows and actionable rows unchanged.
