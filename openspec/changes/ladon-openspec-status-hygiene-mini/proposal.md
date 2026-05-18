# Proposal

Add a deterministic OpenSpec status-hygiene analyzer and use it to remove the
known completed-vs-active metadata drift.

# Why

Ladon is starting to analyze its own process artifacts. If completed packet
tasks coexist with `status: active`, operators and future Ladon self-analysis
receive contradictory signals.

# Scope

- Scan `openspec/changes/*/.openspec.yaml` and sibling `tasks.md`.
- Infer whether task checklists are complete.
- Flag active metadata for completed task lists.
- Provide a small script for JSON reports, check mode, and safe status fixing.
- Normalize current completed-active packet metadata where appropriate.

# Non-Goals

- No general YAML parser dependency.
- No archive/delete workflow.
- No OpenSpec CLI replacement.
- No claim that a completed checklist proves semantic acceptance.
