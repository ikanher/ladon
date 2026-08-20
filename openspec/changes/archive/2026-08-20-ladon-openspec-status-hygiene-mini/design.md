# Design Notes

## Inference Rule

A change is inferred complete only when it has at least one checklist item in
`tasks.md` and every item is checked with `- [x]` or `- [X]`.

Unchecked or mixed checklists are inferred active. Missing task files are
reported as `unknown`, not drift.

## Drift Rule

The first drift class is intentionally narrow:

```text
metadata status active + inferred complete checklist
```

This avoids rewriting packets that are still underway and avoids treating
missing task files as complete.

## Fix Policy

The fixer only changes the exact `status:` line in `.openspec.yaml`, preserving
all other metadata text. It is deliberately limited to completed-active drift.
