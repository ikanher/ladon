# Design Notes

## Finding Classes

- `openspec_status_drift`
- `missing_automation`
- `missing_validation_command`
- `stale_child_reference`

## Child Reference Rule

Files under `children/*.md` are treated as references to change IDs by stem.
If `openspec/changes/<stem>` is absent, the reference is stale.

## Validation Rule

Automation evidence is intentionally simple: a packet should include at least
one command containing `openspec validate`. This is enough to prevent silent
non-validation without requiring a full command runner.
